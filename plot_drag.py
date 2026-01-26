'''
Plot Drag vs Step from test_strategy.csv
'''

import pandas as pd
import matplotlib.pyplot as plt
import os

# 读取CSV文件（使用分号作为分隔符）
csv_path = "saved_models/test_strategy.csv"
df = pd.read_csv(csv_path, sep=';')

# ========== 参数设置 ==========
skip_steps = 0  # 跳过前面的步数（初始瞬态阶段），设为0则显示全部
# ==============================

# 流体参数（用于计算Cd）
rho = 1.0       # 密度
U_inf = 1.0     # 来流速度
D = 1.0         # 特征长度（y方向总长度）

# 跳过初始步骤
if skip_steps > 0 and skip_steps < len(df):
    df_plot = df.iloc[skip_steps:].copy()
    print(f"跳过前 {skip_steps} 步，从第 {skip_steps} 步开始绘图")
else:
    df_plot = df.copy()
    print("显示全部数据")

# 计算阻力系数 Cd = 2*F_D / (rho * U_inf^2 * D)
df_plot['Cd'] = 2 * df_plot['Drag'] / (rho * U_inf**2 * D)

# 创建两个子图
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# 第一个子图：Drag vs Step
ax1 = axes[0]
ax1.plot(df_plot['Step'], df_plot['Drag'], linewidth=0.5, color='blue')
ax1.set_xlabel('Step', fontsize=12)
ax1.set_ylabel('Drag', fontsize=12)
ax1.set_title(f'Drag vs Step (skip first {skip_steps} steps)', fontsize=14)
ax1.grid(True, alpha=0.3)

mean_drag = df_plot['Drag'].mean()
ax1.axhline(y=mean_drag, color='r', linestyle='--', label=f'Mean: {mean_drag:.4f}')
ax1.legend()

# 第二个子图：Cd vs Step
ax2 = axes[1]
ax2.plot(df_plot['Step'], df_plot['Cd'], linewidth=0.5, color='green')
ax2.set_xlabel('Step', fontsize=12)
ax2.set_ylabel(r'$C_D$', fontsize=12)
ax2.set_title(r'Drag Coefficient $C_D$ vs Step (skip first ' + str(skip_steps) + ' steps)', fontsize=14)
ax2.grid(True, alpha=0.3)

mean_cd = df_plot['Cd'].mean()
ax2.axhline(y=mean_cd, color='r', linestyle='--', label=f'Mean: {mean_cd:.4f}')
ax2.legend()

plt.tight_layout()

# 保存图像
output_path = "saved_models/drag_and_cd_vs_step.png"
plt.savefig(output_path, dpi=150)
print(f"图像已保存到: {output_path}")

# 显示图像
plt.show()

# 打印统计信息
min_drag = df_plot['Drag'].min()
max_drag = df_plot['Drag'].max()
min_cd = df_plot['Cd'].min()
max_cd = df_plot['Cd'].max()

print(f"\n统计信息 (跳过前 {skip_steps} 步后):")
print(f"  显示步数: {len(df_plot)}")
print(f"  Drag统计:")
print(f"    平均Drag: {mean_drag:.6f}")
print(f"    最小Drag: {min_drag:.6f}")
print(f"    最大Drag: {max_drag:.6f}")
print(f"  Cd统计 (Cd = 2*Drag / (rho*U^2*D)):")
print(f"    平均Cd: {mean_cd:.6f}")
print(f"    最小Cd: {min_cd:.6f}")
print(f"    最大Cd: {max_cd:.6f}")
