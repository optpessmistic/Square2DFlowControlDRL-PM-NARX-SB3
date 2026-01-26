import argparse
import os
import sys
import csv
import socket
import numpy as np
import torch
import time
from datetime import datetime, timedelta

# 强制禁用标准输出缓冲，确保在超算上实时输出
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

from simulation_base.env import resume_env, nb_actuations

from gym.wrappers.time_limit import TimeLimit

from sb3_contrib import TQC
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize, VecFrameStack
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import Logger, HumanOutputFormat, DEBUG
from stable_baselines3.sac import SAC
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, BaseCallback


class SpeedMonitorCallback(BaseCallback):
    """
    自定义回调函数，用于监控和记录训练速度
    """
    def __init__(self, check_freq=1000, log_dir='./logs/', verbose=1):
        super(SpeedMonitorCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.start_time = None
        self.last_check_time = None
        self.last_check_steps = 0
        self.episode_count = 0
        self.log_file = None
        
    def _init_callback(self) -> None:
        if self.log_dir is not None:
            os.makedirs(self.log_dir, exist_ok=True)
            log_path = os.path.join(self.log_dir, 'training_speed.csv')
            self.log_file = open(log_path, 'w', newline='')
            self.csv_writer = csv.writer(self.log_file)
            self.csv_writer.writerow(['Timestamp', 'Total_Steps', 'Episodes', 'Steps_Per_Second', 
                                      'Episodes_Per_Hour', 'Elapsed_Time_Hours', 'ETA_Hours'])
        self.start_time = time.time()
        self.last_check_time = self.start_time
        
    def _on_step(self) -> bool:
        # 持续检查episode完成情况
        if 'infos' in self.locals:
            for info in self.locals['infos']:
                if 'episode' in info:
                    self.episode_count += 1
        
        if self.n_calls % self.check_freq == 0:
            current_time = time.time()
            elapsed_total = current_time - self.start_time
            elapsed_interval = current_time - self.last_check_time
            
            # 计算速度
            steps_in_interval = self.num_timesteps - self.last_check_steps
            steps_per_second = steps_in_interval / elapsed_interval if elapsed_interval > 0 else 0
            
            # 计算每小时episodes
            episodes_per_hour = (self.episode_count / elapsed_total) * 3600 if elapsed_total > 0 else 0
            
            # 计算预计剩余时间
            total_steps = 15000000  # 从learn()函数中获取
            remaining_steps = total_steps - self.num_timesteps
            eta_seconds = remaining_steps / steps_per_second if steps_per_second > 0 else 0
            eta_hours = eta_seconds / 3600
            
            # 记录到CSV
            if self.log_file:
                self.csv_writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    self.num_timesteps,
                    self.episode_count,
                    f'{steps_per_second:.2f}',
                    f'{episodes_per_hour:.2f}',
                    f'{elapsed_total/3600:.2f}',
                    f'{eta_hours:.2f}'
                ])
                self.log_file.flush()
            
            # 打印到控制台
            if self.verbose > 0:
                print(f"\n{'='*80}", flush=True)
                print(f"训练进度监控 - Step {self.num_timesteps:,}/{total_steps:,} ({self.num_timesteps/total_steps*100:.1f}%)", flush=True)
                print(f"{'='*80}", flush=True)
                print(f"运算速度: {steps_per_second:.2f} steps/秒", flush=True)
                print(f"Episodes数: {self.episode_count}", flush=True)
                print(f"Episodes速度: {episodes_per_hour:.2f} episodes/小时", flush=True)
                print(f"已用时间: {timedelta(seconds=int(elapsed_total))}", flush=True)
                print(f"预计剩余时间: {timedelta(seconds=int(eta_seconds))}", flush=True)
                print(f"预计完成时间: {(datetime.now() + timedelta(seconds=eta_seconds)).strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
                print(f"{'='*80}\n", flush=True)
            
            # 更新检查点
            self.last_check_time = current_time
            self.last_check_steps = self.num_timesteps
            
        return True
    
    def _on_training_end(self) -> None:
        if self.log_file:
            total_time = time.time() - self.start_time
            print(f"\n训练完成！总用时: {timedelta(seconds=int(total_time))}", flush=True)
            self.log_file.close()


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--number-servers", required=True, help="number of servers to spawn", type=int)
    ap.add_argument("-s", "--savedir", required=False,
                    help="Directory into which to save the NN. Defaults to 'saver_data'.", type=str,
                    default='saver_data')

    args = vars(ap.parse_args())

    number_servers = args["number_servers"]
    savedir = args["savedir"]
    config = {}

    config["learning_rate"] = 1e-4
    config["learning_starts"] = 26000
    config["batch_size"] = 128

    config["tau"] = 5e-3
    config["gamma"] = 0.99
    config["train_freq"] = 1
    config["target_update_interval"] = 1
    config["gradient_steps"] = 48

    config["buffer_size"] = int(10e5)
    config["optimize_memory_usage"] = False

    config["ent_coef"] = "auto_0.01"
    config["target_entropy"] = "auto"
    device = "cuda" # "cpu" if run the training on cpu
    policy_kwargs = dict(net_arch=dict(pi=[256,256], qf=[256,256]))
    checkpoint_callback = CheckpointCallback(
                                            save_freq=max(200, 1),
                                            #save_env_stats=True,
                                            #save_replay_buffer=True, # This is not tested, may be useful for resume
                                            save_vecnormalize=True,
                                            save_path=savedir,
                                            name_prefix='PMTQC27FSavgPR')
    
    # 创建速度监控回调，每1000步检查一次
    speed_monitor = SpeedMonitorCallback(check_freq=1000, log_dir=os.path.join(savedir, 'logs'), verbose=1)

    # 注意：在子进程中禁用 plot 以避免 matplotlib GUI 问题
    # 禁用 random_start 以避免数值发散
    env = SubprocVecEnv([resume_env(plot=False, dump_CL=False, dump_debug=10, n_env=i, random_start=False) for i in range(number_servers)],start_method='spawn')
    
    # Deactivate this if not use history observations
    env = VecFrameStack(env, n_stack=27)
    
    env = VecNormalize(env, gamma=0.99)
    
    # 引入 VecCheckNan 并包裹环境
    # 作用：一旦环境返回 NaN 或无穷大，程序会立即报错并打印出是哪个环境、哪一步出的错
    from stable_baselines3.common.vec_env import VecCheckNan
    env = VecCheckNan(env, raise_exception=True)
    # =============== 修改结束 ===============

    # Replace 'TQC' by 'SAC' if want to use SAC
    model = SAC('MlpPolicy', env, policy_kwargs=policy_kwargs, tensorboard_log=savedir, device=device, **config)

    print(f"\n开始训练...", flush=True)
    print(f"并行环境数: {number_servers}", flush=True)
    print(f"总训练步数: 15,000,000", flush=True)
    print(f"保存目录: {savedir}", flush=True)
    print(f"设备: {device}", flush=True)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", flush=True)
    
    training_start_time = time.time()
    
    model.learn(1500000, callback=[checkpoint_callback, speed_monitor], log_interval=1)
    
    training_end_time = time.time()
    total_training_time = training_end_time - training_start_time
    
    print(f"\n{'='*80}", flush=True)
    print(f"训练完成统计", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"总训练时间: {timedelta(seconds=int(total_training_time))}", flush=True)
    print(f"平均速度: {15000000/total_training_time:.2f} steps/秒", flush=True)
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"{'='*80}\n", flush=True)


    print("Agent and Runner closed -- Learning complete -- End of script", flush=True)
    os._exit(0)

