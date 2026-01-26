
from dolfin import *
import numpy as np

import math

# Solves FE problem (sets BCs,
# There are three variational problems to be defined, one for each step in the IPCS scheme


class FlowSolver(object):
    '''IPCS scheme with explicit treatment of nonlinearity.'''
    def __init__(self, flow_params, geometry_params, solver_params):
        # Using very simple IPCS solver
        mu = Constant(flow_params['mu'])              # dynamic viscosity
        rho = Constant(flow_params['rho'])            # density

        mesh_file = geometry_params['mesh']

        # Load mesh with markers
        mesh = Mesh()
        comm = mesh.mpi_comm()
        h5 = HDF5File(comm, mesh_file, 'r')
        h5.read(mesh, 'mesh', False)

        surfaces = MeshFunction('size_t', mesh, mesh.topology().dim()-1)
        h5.read(surfaces, 'facet')

        # These tags should be hardcoded by gmsh during generation
        inlet_tag = 3
        outlet_tag = 2
        wall_tag = 1
        cylinder_noslip_tag = 4
        # Tags 5 and higher are jets

        # Define function spaces
        V = VectorFunctionSpace(mesh, 'CG', 2)
        Q = FunctionSpace(mesh, 'CG', 1)
        # Here, "CG" stands for Continuous Galerkin, implying the standard Lagrange family of elements.

        # Define trial and test functions
        u, v = TrialFunction(V), TestFunction(V)
        p, q = TrialFunction(Q), TestFunction(Q)

        u_n, p_n = Function(V), Function(Q)
        # Starting from rest or are we given the initial state
        for path, func, name in zip(('u_init', 'p_init'), (u_n, p_n), ('u0', 'p0')):
            if path in flow_params:
                comm = mesh.mpi_comm()
                
                # 使用 HDF5File 代替 XDMFFile.read_checkpoint（后者有 bug）
                xdmf_path = flow_params[path]
                h5_path = xdmf_path.replace('.xdmf', '.h5')
                h5_dataset = name + '/' + name + '_0/vector'  # e.g., 'u0/u0_0/vector'
                with HDF5File(comm, h5_path, 'r') as h5:
                    h5.read(func, h5_dataset)
                # assert func.vector().norm('l2') > 0

        u_, p_ = Function(V), Function(Q)  # Solve into these

        dt = Constant(solver_params['dt'])
        # Define expressions used in variational forms
        U  = Constant(0.5)*(u_n + u)
        n  = FacetNormal(mesh)
        f  = Constant((0, 0))

        # Define strain-rate tensor
        epsilon = lambda u :sym(nabla_grad(u))

        # Define stress tensor
        sigma = lambda u, p: 2*mu*epsilon(u) - p*Identity(2)

        # Define variational problem for step 1
        F1 = (rho*dot((u - u_n) / dt, v)*dx
              + rho*dot(dot(u_n, nabla_grad(u_n)), v)*dx
              + inner(sigma(U, p_n), epsilon(v))*dx
              + dot(p_n*n, v)*ds - dot(mu*nabla_grad(U)*n, v)*ds
              - dot(f, v)*dx)

        a1, L1 = lhs(F1), rhs(F1)

        # Define variational problem for step 2
        a2 = dot(nabla_grad(p), nabla_grad(q))*dx
        L2 = dot(nabla_grad(p_n), nabla_grad(q))*dx - (1/dt)*div(u_)*q*dx

        # Define variational problem for step 3
        a3 = dot(u, v)*dx
        L3 = dot(u_, v)*dx - dt*dot(nabla_grad(p_ - p_n), v)*dx

        inflow_profile = flow_params['inflow_profile']
        # Define boundary conditions, first those that are constant in time
        bcu_inlet = DirichletBC(V, inflow_profile, surfaces, inlet_tag)  # (Function space, value, subdomain, method to identify DOFs)
        # Free stream. Note: use V.sub(0) or V.sub(1) to acces individual components
        bcu_wall = DirichletBC(V, Constant((1, 0)), surfaces, wall_tag)
        bcu_cyl_wall = DirichletBC(V, Constant((0, 0)), surfaces, cylinder_noslip_tag)
        # Fixing outflow pressure
        bcp_outflow = DirichletBC(Q, Constant(0), surfaces, outlet_tag)

        # Now the expression for the jets
        # NOTE: they start with Q=0
        width = geometry_params['jet_width']
        
        # V 形几何参数 (必须与 turek_2d.geo 中的定义完全一致!)
        v_angle = geometry_params.get('v_angle', 70 * math.pi / 180)  # 半角
        scale_factor = geometry_params.get('scale_factor', 1.0 / (2.0 * math.tan(v_angle)))
        
        # 注意：这些参数在 .geo 文件中是直接硬编码的，没有乘以 scale_factor
        # 所以这里也不应该乘以 scale_factor
        arm_thickness = 0.064  # 必须与 turek_2d.geo 中的值完全一致
        jet_interval = 0.01   # 必须与 turek_2d.geo 中的值完全一致
        jet_width = width     # jet_width 在 .geo 中也未缩放
        
        # 计算射流中心位置 (与 turek_2d.geo 完全一致)
        r_length = geometry_params['height_cylinder'] * geometry_params['ar'] * scale_factor
        x_rear = r_length / 2
        x_tip = -r_length / 2
        y_rear_top_outer = (x_rear - x_tip) * math.tan(v_angle)  # = 0.5
        
        thickness_offset_x = arm_thickness * math.sin(v_angle)
        thickness_offset_y = arm_thickness * math.cos(v_angle)
        x_rear_inner = x_rear + thickness_offset_x
        y_rear_top_inner = y_rear_top_outer - thickness_offset_y
        y_rear_bot_inner = -y_rear_top_inner
        
        x_jet_centre = x_rear_inner - (jet_width / 2 + jet_interval) * math.cos(v_angle)
        y_jet_top_centre = y_rear_top_inner - (jet_width / 2 + jet_interval) * math.sin(v_angle)
        y_jet_bot_centre = -y_jet_top_centre

        bcu_jet = []
        jet_tags = list(range(cylinder_noslip_tag + 1, cylinder_noslip_tag + 1 + 2))  # 5 and 6 for 2 jets

        theta = v_angle
        
        # 法向量分量 (指向流场内部)
        # 顶部射流法向量 (指向右下): nx = sin(theta), ny = -cos(theta)
        # 底部射流法向量 (指向右上): nx = sin(theta), ny = cos(theta)
        nx = math.sin(theta)
        ny = math.cos(theta)

        # 对于 V 形斜边上的射流，使用沿斜边的局部坐标
        # s = 沿斜边的距离 (从射流中心测量)
        # 对于顶部斜边: s = (x - x_jet_centre) * cos(theta) + (y - y_jet_centre) * sin(theta)
        # 对于底部斜边: s = (x - x_jet_centre) * cos(theta) - (y - y_jet_centre) * sin(theta)
        
        # 抛物线分布: amplitude = (3/2) * (Q/width) * (1 - (2*s/width)^2)
        # 速度方向沿法向量
        
        # 顶部射流表达式 (沿斜边的局部坐标)
        top_jet_profile = f'''(3.0/2.0) * (Q/{jet_width}) * 
            (1.0 - pow(2.0 * ({math.cos(theta)} * (x[0] - {x_jet_centre}) + {math.sin(theta)} * (x[1] - {y_jet_top_centre})) / {jet_width}, 2))'''
        
        # 底部射流表达式 (沿斜边的局部坐标)
        bot_jet_profile = f'''(3.0/2.0) * (Q/{jet_width}) * 
            (1.0 - pow(2.0 * ({math.cos(theta)} * (x[0] - {x_jet_centre}) + {-math.sin(theta)} * (x[1] - {y_jet_bot_centre})) / {jet_width}, 2))'''

        jets = [
            # Top jet (Tag 5): 方向 (nx, -ny)
            Expression((f'{nx} * {top_jet_profile}', f'{-ny} * {top_jet_profile}'),
                       Q=0, degree=2),
            
            # Bot jet (Tag 6): 方向 (nx, ny)
            Expression((f'{nx} * {bot_jet_profile}', f'{ny} * {bot_jet_profile}'),
                       Q=0, degree=2)
        ]
        
        
        for tag, jet in zip(jet_tags, jets):
            bc = DirichletBC(V, jet, surfaces, tag)
            bcu_jet.append(bc)

        # All bcs objects togets
        bcu = [bcu_inlet, bcu_wall, bcu_cyl_wall] + bcu_jet
        bcp = [bcp_outflow]

        As = [Matrix() for i in range(3)]
        bs = [Vector() for i in range(3)]

        # Assemble matrices
        assemblers = [SystemAssembler(a1, L1, bcu),
                      SystemAssembler(a2, L2, bcp),
                      SystemAssembler(a3, L3, bcu)]

        # Apply bcs to matrices (this is done once)
        for a, A in zip(assemblers, As):
            a.assemble(A)

        # Chose between direct and iterative solvers
        solver_type = solver_params.get('la_solve', 'lu')
        assert solver_type in ('lu', 'la_solve')

        if solver_type == 'lu':
            solvers = list(map(lambda x: LUSolver(), range(3)))
        else:
            solvers = [KrylovSolver('bicgstab', 'hypre_amg'),  # Very questionable preconditioner
                       KrylovSolver('cg', 'hypre_amg'),
                       KrylovSolver('cg', 'hypre_amg')]

        # Set matrices for once, likewise solver don't change in time
        for s, A in zip(solvers, As):
            s.set_operator(A)

            if not solver_type == 'lu':
                s.parameters['relative_tolerance'] = 1E-8
                s.parameters['monitor_convergence'] = True

        gtime = 0.  # External clock

        # Things to remeber for evolution
        self.jets = jets
        # Keep track of time so that we can query it outside
        self.gtime, self.dt = gtime, dt
        # Remember inflow profile function in case it is time dependent
        self.inflow_profile = inflow_profile

        self.solvers = solvers
        self.assemblers = assemblers
        self.bs = bs
        self.u_, self.u_n = u_, u_n
        self.p_, self.p_n= p_, p_n

        # Rename u_, p_ for to standard names (simplifies processing)
        u_.rename('velocity', '0')
        p_.rename('pressure', '0')

        # Also expose measure for assembly of outputs outside
        self.ext_surface_measure = Measure('ds', domain=mesh, subdomain_data=surfaces)

        # Things to remember for easier probe configuration
        self.viscosity = mu
        self.density = rho
        self.normal = n
        self.cylinder_surface_tags = [cylinder_noslip_tag] + jet_tags

    def evolve(self, jet_bc_values):
        '''Make one time step with the given values of jet boundary conditions'''
        assert len(jet_bc_values) == len(self.jets)

        # Update bc expressions
        for Q, jet in zip(jet_bc_values, self.jets): jet.Q = Q

        # Make a step
        self.gtime += self.dt(0)

        inflow = self.inflow_profile
        if hasattr(inflow, 'time'):
            inflow.time = self.gtime

        assemblers, solvers = self.assemblers, self.solvers
        bs = self.bs
        u_, p_ = self.u_, self.p_
        u_n, p_n = self.u_n, self.p_n

        for (assembler, b, solver, uh) in zip(assemblers, bs, solvers, (u_, p_, u_)):
            assembler.assemble(b)
            solver.solve(uh.vector(), b)

        u_n.assign(u_)
        p_n.assign(p_)

        # Share with the world
        return u_, p_