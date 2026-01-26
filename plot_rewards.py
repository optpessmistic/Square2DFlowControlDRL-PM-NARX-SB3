"""
解析 rewards.csv 并区分不同进程的 reward，绘制曲线图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def parse_rewards(csv_path='saved_models/rewards.csv'):
    """
    解析 rewards.csv 文件，根据 Step 的规律区分不同的进程
    
    策略：每个进程的 Step 是独立递增的，当 Step 回退时说明是另一个进程的数据
    """
    # 读取 CSV (分号分隔)
    df = pd.read_csv(csv_path, delimiter=';')
    
    print(f"总记录数: {len(df)}")
    print(f"列名: {df.columns.tolist()}")
    print(f"\n前10行数据:")
    print(df.head(10))
    
    # 为每行分配进程 ID
    # 策略：跟踪每个进程最后看到的 Step，将新行分配给 Step 能接上的进程
    env_ids = []
    env_last_step = {}  # 记录每个环境最后的 step
    
    for idx, row in df.iterrows():
        step = row['Step']
        episode = row['Episode']
        
        # 找到能接上的环境（当前 step > 该环境的 last_step，且差值最小）
        assigned_env = None
        min_gap = float('inf')
        
        for env_id, last_step in env_last_step.items():
            if step > last_step:
                gap = step - last_step
                if gap < min_gap:
                    min_gap = gap
                    assigned_env = env_id
        
        if assigned_env is None:
            # 没有能接上的环境，创建新环境
            assigned_env = len(env_last_step)
        
        env_last_step[assigned_env] = step
        env_ids.append(assigned_env)
    
    df['EnvID'] = env_ids
    
    # 统计信息
    n_envs = df['EnvID'].nunique()
    print(f"\n检测到 {n_envs} 个进程环境")
    
    for env_id in sorted(df['EnvID'].unique()):
        env_df = df[df['EnvID'] == env_id]
        print(f"\n进程 {env_id}:")
        print(f"  记录数: {len(env_df)}")
        print(f"  Step 范围: {env_df['Step'].min()} - {env_df['Step'].max()}")
        print(f"  Reward 均值: {env_df['Reward'].mean():.6f}")
        print(f"  Reward 范围: [{env_df['Reward'].min():.6f}, {env_df['Reward'].max():.6f}]")
    
    return df


def plot_rewards_by_env(df, save_path='saved_models/rewards_by_env.png'):
    """
    绘制每个进程的 reward 曲线
    """
    n_envs = df['EnvID'].nunique()
    
    fig, axes = plt.subplots(n_envs + 1, 1, figsize=(12, 4 * (n_envs + 1)))
    
    if n_envs == 1:
        axes = [axes, None]  # 确保 axes 可迭代
    
    colors = plt.cm.tab10(np.linspace(0, 1, n_envs))
    
    # 为每个环境绘制单独的子图
    for i, env_id in enumerate(sorted(df['EnvID'].unique())):
        env_df = df[df['EnvID'] == env_id].reset_index(drop=True)
        
        ax = axes[i]
        ax.plot(env_df.index, env_df['Reward'], color=colors[i], alpha=0.7, linewidth=0.8)
        
        # 计算滑动平均
        window = min(50, len(env_df) // 5) if len(env_df) > 10 else 1
        if window > 1:
            rolling_mean = env_df['Reward'].rolling(window=window, center=True).mean()
            ax.plot(env_df.index, rolling_mean, color=colors[i], linewidth=2, 
                    label=f'Moving Avg (window={window})')
        
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        ax.set_xlabel('Action Step (within this env)')
        ax.set_ylabel('Reward')
        ax.set_title(f'Env {env_id} Rewards')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # 最后一个子图：所有环境叠加
    ax_all = axes[n_envs] if n_envs > 1 else axes[0]
    for i, env_id in enumerate(sorted(df['EnvID'].unique())):
        env_df = df[df['EnvID'] == env_id].reset_index(drop=True)
        ax_all.plot(env_df.index, env_df['Reward'], color=colors[i], alpha=0.5, 
                    linewidth=0.8, label=f'Env {env_id}')
    
    ax_all.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    ax_all.set_xlabel('Action Step')
    ax_all.set_ylabel('Reward')
    ax_all.set_title('All Environments Rewards Comparison')
    ax_all.legend()
    ax_all.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"\n图表已保存到: {save_path}")
    plt.show()


def plot_rewards_vs_step(df, save_path='saved_models/rewards_vs_step.png'):
    """
    以全局 Step 为 x 轴绘制 reward
    """
    n_envs = df['EnvID'].nunique()
    colors = plt.cm.tab10(np.linspace(0, 1, n_envs))
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    for i, env_id in enumerate(sorted(df['EnvID'].unique())):
        env_df = df[df['EnvID'] == env_id]
        ax.scatter(env_df['Step'], env_df['Reward'], color=colors[i], 
                   alpha=0.6, s=10, label=f'Env {env_id}')
    
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    ax.set_xlabel('Global Step')
    ax.set_ylabel('Reward')
    ax.set_title('Rewards vs Global Step (by Environment)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"图表已保存到: {save_path}")
    plt.show()


def print_summary_table(df):
    """
    打印汇总表格
    """
    print("\n" + "="*70)
    print("各进程 Reward 统计汇总")
    print("="*70)
    
    summary = df.groupby('EnvID').agg({
        'Reward': ['count', 'mean', 'std', 'min', 'max'],
        'Step': ['min', 'max']
    }).round(6)
    
    summary.columns = ['记录数', '均值', '标准差', '最小值', '最大值', 'Step最小', 'Step最大']
    print(summary.to_string())
    
    print("\n" + "-"*70)
    print(f"总体均值: {df['Reward'].mean():.6f}")
    print(f"总体标准差: {df['Reward'].std():.6f}")
    print("="*70)


if __name__ == '__main__':
    csv_path = 'saved_models/rewards.csv'
    
    if not os.path.exists(csv_path):
        print(f"错误: 文件 {csv_path} 不存在")
        exit(1)
    
    # 解析数据
    df = parse_rewards(csv_path)
    
    # 打印汇总表
    print_summary_table(df)
    
    # 保存带有 EnvID 的数据
    output_csv = 'saved_models/rewards_with_envid.csv'
    df.to_csv(output_csv, index=False, sep=';')
    print(f"\n带环境ID的数据已保存到: {output_csv}")
    
    # 绘图
    plot_rewards_by_env(df)
    plot_rewards_vs_step(df)
