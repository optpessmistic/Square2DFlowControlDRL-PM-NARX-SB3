from dolfin import *
import numpy as np

# 读取 u_init
mesh = Mesh()
hdf = HDF5File(mesh.mpi_comm(), "simulation_base/mesh/u_init.h5", "r")
hdf.read(mesh, "/mesh", False)
V = VectorFunctionSpace(mesh, 'CG', 2)
u = Function(V)
hdf.read(u, "/u0")
hdf.close()

# 检查数值
u_array = u.vector().get_local()
if np.isnan(u_array).any():
    print("【严重错误】u_init 中发现 NaN (非数值)！文件已损坏。")
elif np.max(np.abs(u_array)) > 100:
    print(f"【警告】u_init 中发现极大值: {np.max(np.abs(u_array))}，可能已发散。")
else:
    print("u_init 检查通过，数值正常。")