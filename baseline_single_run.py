'''
Perform a single run of the flow without control
'''

import os
import socket
import numpy as np
import csv
import sys
import math
import argparse
import json

from dolfin import Expression
from gym.wrappers.time_limit import TimeLimit

from Env2DCylinderModified import Env2DCylinderModified
from probe_positions import probe_positions
from simulation_base.env import resume_env, nb_actuations

from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize, VecFrameStack
from stable_baselines3.common.monitor import Monitor
from sb3_contrib import TQC
from stable_baselines3 import SAC
from stable_baselines3.common.evaluation import evaluate_policy

# If previous evaluation results exist, delete them
if(os.path.exists("saved_models/test_strategy.csv")):
    os.remove("saved_models/test_strategy.csv")

if(os.path.exists("saved_models/test_strategy_avg.csv")):
    os.remove("saved_models/test_strategy_avg.csv")


if __name__ == '__main__':

    simulation_duration = 200  # Non-dimensional time unit (defined in env.py)
    action_step_size = simulation_duration / nb_actuations  # Get action step size from the environment, not used
    horizon = 400 # Number of actions for single run. Non-dimensional time is horizon*action_step_size (by default action_step_size=0.5)
    action_steps = int(horizon)
    
    # 使用 DummyVecEnv 以便看到详细错误信息（调试时使用）
    # 注意：修改几何后需要先用 remesh=True 重新预热，生成新的 u_init.xdmf
    #env = DummyVecEnv([resume_env(plot=300, single_run=True, horizon=horizon, n_env=99, remesh=True)])
    env = SubprocVecEnv([resume_env(plot=300, single_run=True, horizon=horizon, n_env=99, remesh=False)], start_method='spawn')

    observations = env.reset()
    
    # 获取环境数量 (这里是 1)
    num_envs = env.num_envs
    # 获取动作空间维度 (通常是 2，对应两个射流)
    action_dim = env.action_space.shape[0]
    # 创建全零动作数组 (形状为 [n_envs, action_dim])
    zero_actions = np.zeros((num_envs, action_dim))
    
    print(f"Starting baseline run with {action_steps} steps...")
    
    for k in range(action_steps):
        observations, rw, done, _ = env.step(zero_actions)
        
        if k % 10 == 0:
            print(f"Step {k}/{action_steps}")
            
            
    print("Baseline run finished.")