DefineConstant[
jets_toggle = {1, Name "Toggle Jets --> 0 : No jets, 1: Yes jets"}
height_cylinder = {1, Name "Cylinder Height (ND)"}
ar = {1.0, Name "Cylinder Aspect Ratio"}
cylinder_y_shift = {0.0, Name "Cylinder Center Shift from Centerline, Positive UP (ND)"}
x_upstream = {10, Name "Domain Upstream Length (from left-most rect point) (ND)"}
x_downstream = {26, Name "Domain Downstream Length (from right-most rect point) (ND)"}
height_domain = {20, Name "Domain Height (ND)"}
coarse_y_distance_top_bot = {4, Name "y-distance from center where mesh coarsening starts"}
coarse_x_distance_left_from_LE = {2, Name "x-distance from upstream face where mesh coarsening starts"}
mesh_size_cylinder = {0.05, Name "Mesh Size on Cylinder Walls"}
mesh_size_jets = {0.01, Name "Mesh Size on jet suirfaces"}
mesh_size_medium = {0.2, Name "Medium mesh size (at boundary where coarsening starts"}
mesh_size_coarse = {1, Name "Coarse mesh Size Close to Domain boundaries outside wake"}
jet_width = {0.1, Name "Jet Width (ND)"}
];

// Seed the cylinder's center's identifier and create the center point
center = newp;
Point(center) = {0, 0, 0, mesh_size_cylinder};

// V-shape dimensions
r_height = height_cylinder; // V-shape characteristic height
r_length = ar*height_cylinder; // V-shape length (from tip to rear)
arm_thickness = 0.15; // Thickness of each V arm

// V-shape geometry: 60 degree opening angle, tip pointing upstream
v_angle = 30 * Pi / 180; // Half angle in radians (30 degrees, total 60 degrees)

// Define key x coordinates
x_tip = -r_length/2;  // Front tip (most upstream point)
x_rear = r_length/2;  // Rear edge (most downstream point)

// V-shape with thickness: each arm is a rectangular bar
// Top arm - outer edge points
y_rear_top_outer = (x_rear - x_tip) * Tan(v_angle);  // Top arm outer edge at rear
y_tip_top_outer = 0 + arm_thickness/(2*Cos(v_angle)); // Top arm outer edge at tip

// Top arm - inner edge points (offset by arm_thickness perpendicular to arm)
thickness_offset_y = arm_thickness * Cos(v_angle); // Vertical component of thickness
thickness_offset_x = arm_thickness * Sin(v_angle); // Horizontal component of thickness
y_rear_top_inner = y_rear_top_outer - thickness_offset_y;
y_tip_top_inner = -arm_thickness/(2*Cos(v_angle));
x_tip_top_inner = x_tip + thickness_offset_x;

// Bottom arm - outer edge points (mirror of top)
y_rear_bot_outer = -y_rear_top_outer;
y_tip_bot_outer = -y_tip_top_outer;

// Bottom arm - inner edge points
y_rear_bot_inner = -y_rear_top_inner;
y_tip_bot_inner = -y_tip_top_inner;
x_tip_bot_inner = x_tip + thickness_offset_x;

// Jet positioning on outer edges near rear
x_jet_start = x_rear - jet_width * Cos(v_angle);
y_jet_top_start_outer = y_rear_top_outer - jet_width * Sin(v_angle);
y_jet_bot_start_outer = y_rear_bot_outer + jet_width * Sin(v_angle);

// Jet center points
x_jet_centre = (x_jet_start + x_rear) / 2;
y_jet_top_centre = (y_jet_top_start_outer + y_rear_top_outer) / 2;
y_jet_bot_centre = (y_jet_bot_start_outer + y_rear_bot_outer) / 2;

// Define all points for V-shape with thickness
p = newp;
// Top arm outer edge
Point(p) = {x_tip, y_tip_top_outer, 0, mesh_size_cylinder};  // Front tip outer top (p)
Point(p+1) = {x_jet_start, y_jet_top_start_outer, 0, mesh_size_jets};  // Top jet start outer (p+1)
Point(p+2) = {x_jet_centre, y_jet_top_centre, 0, mesh_size_jets};  // Top jet centre outer (p+2)
Point(p+3) = {x_rear, y_rear_top_outer, 0, mesh_size_jets};  // Top rear outer (p+3)

// Top arm inner edge
Point(p+4) = {x_rear, y_rear_top_inner, 0, mesh_size_jets};  // Top rear inner (p+4)
Point(p+5) = {x_tip_top_inner, y_tip_top_inner, 0, mesh_size_cylinder};  // Front tip inner top (p+5)

// Bottom arm inner edge
Point(p+6) = {x_tip_bot_inner, y_tip_bot_inner, 0, mesh_size_cylinder};  // Front tip inner bottom (p+6)
Point(p+7) = {x_rear, y_rear_bot_inner, 0, mesh_size_jets};  // Bottom rear inner (p+7)

// Bottom arm outer edge
Point(p+8) = {x_rear, y_rear_bot_outer, 0, mesh_size_jets};  // Bottom rear outer (p+8)
Point(p+9) = {x_jet_centre, y_jet_bot_centre, 0, mesh_size_jets};  // Bottom jet centre outer (p+9)
Point(p+10) = {x_jet_start, y_jet_bot_start_outer, 0, mesh_size_jets};  // Bottom jet start outer (p+10)
Point(p+11) = {x_tip, y_tip_bot_outer, 0, mesh_size_cylinder};  // Front tip outer bottom (p+11)

If(jets_toggle)

  cylinder[] = {}; // Create empty list of curves of the V-shape body
  no_slip_cyl[] = {};  // No-slip V-shape physical surfaces list

  // Top arm outer edge (from tip to rear)
  l = newl;
  Line(l) = {p, p+1};  // Tip to jet start
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Top jet surface
  l = newl;
  Line(l) = {p+1, p+2};
  Line(l+1) = {p+2, p+3};
  Physical Line(5) = {l, l+1};  // Top jet physical surface
  cylinder[] += {l, l+1};

  // Top arm rear end (outer to inner)
  l = newl;
  Line(l) = {p+3, p+4};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Top arm inner edge (rear to tip)
  l = newl;
  Line(l) = {p+4, p+5};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Front connection (top inner to bottom inner)
  l = newl;
  Line(l) = {p+5, p+6};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Bottom arm inner edge (tip to rear)
  l = newl;
  Line(l) = {p+6, p+7};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Bottom arm rear end (inner to outer)
  l = newl;
  Line(l) = {p+7, p+8};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Bottom jet surface
  l = newl;
  Line(l) = {p+8, p+9};
  Line(l+1) = {p+9, p+10};
  Physical Line(6) = {l, l+1};  // Bottom jet physical surface
  cylinder[] += {l, l+1};

  // Bottom arm outer edge (rear to tip)
  l = newl;
  Line(l) = {p+10, p+11};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Front connection (bottom outer to top outer)
  l = newl;
  Line(l) = {p+11, p};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  Physical Line(4) = {no_slip_cyl[]};  // Define no-slip V-shape physical surfaces

// Just the V-shape without jets
Else

   l = newl;
   // Top arm outer edge
   Line(l) = {p, p+3};
   // Top arm rear end
   Line(l+1) = {p+3, p+4};
   // Top arm inner edge
   Line(l+2) = {p+4, p+5};
   // Front connection top
   Line(l+3) = {p+5, p+6};
   // Bottom arm inner edge
   Line(l+4) = {p+6, p+7};
   // Bottom arm rear end
   Line(l+5) = {p+7, p+8};
   // Bottom arm outer edge
   Line(l+6) = {p+8, p+11};
   // Front connection bottom
   Line(l+7) = {p+11, p};

   cylinder[] = {l, l+1, l+2, l+3, l+4, l+5, l+6, l+7};	// All edges of thick V-shape
   Physical Line(4) = {cylinder[]}; // Define no-slip V-shape physical surfaces
EndIf

// Create the channel (Domain exterior boundary)
// Define useful quantities
y_top_dom = height_domain/2-cylinder_y_shift;  // Smaller than half the height if positive shift
y_bot_dom = -height_domain/2-cylinder_y_shift; // Larger in mag than half the height if positive shift
x_left_dom = -r_length/2-x_upstream;
x_right_dom = r_length/2+x_downstream;

y_coarse_top = coarse_y_distance_top_bot;
y_coarse_bot = - coarse_y_distance_top_bot;
x_coarse_left = - r_length/2 - coarse_x_distance_left_from_LE;

// Define points
p = newp;
Point(p) = {x_left_dom, y_bot_dom, 0, mesh_size_coarse}; // domain bottom-left corner
Point(p+1) = {x_right_dom, y_bot_dom, 0, mesh_size_coarse}; // domain bottom-right corner
Point(p+2) = {x_right_dom, y_top_dom, 0, mesh_size_coarse}; // domain top-right corner
Point(p+3) = {x_left_dom, y_top_dom, 0, mesh_size_coarse}; // domain top-left corner

Point(p+4) = {x_coarse_left, y_coarse_bot, 0, mesh_size_medium}; // coarsening bottom-left corner
Point(p+5) = {x_right_dom, y_coarse_bot, 0, mesh_size_medium}; // coarsening bottom-right corner
Point(p+6) = {x_right_dom, y_coarse_top, 0, mesh_size_medium}; // coarsening top-right corner
Point(p+7) = {x_coarse_left, y_coarse_top, 0, mesh_size_medium}; // coarsening top-left corner


l = newl;
// Bottom wall (slip-free)
Line(l) = {p, p+1};
Physical Line(1) = {l};

// Right wall (outflow)
Line(l+1) = {p+1, p+5};  // Bottom-right side
Line(l+2) = {p+5, p+6};  // Middle-right side (coarsening bound right)
Line(l+3) = {p+6, p+2};  // Top-right side
Physical Line(2) = {l+1, l+2, l+3};

// Top wall (slip free)
Line(l+4) = {p+2, p+3};
Physical Line(1) += {l+4};

// Inlet
Line(l+5) = {p+3, p};
Physical Line(3) = {l+5};

// Coarsening bound bottom
Line(l+6) = {p+4, p+5};

// Coarsening bound top
Line(l+7) = {p+6, p+7};

// Coarsening bound left
Line(l+8) = {p+7, p+4};

// Define coarse mesh portion of domain
// Create line loop for coarse area
coarse = newll;
Line Loop(coarse) = {(l), (l+1), -(l+6), -(l+8), -(l+7), (l+3), (l+4), (l+5)};
// Create surface and physical surface for coarse area
s = news;
Plane Surface(s) = {coarse};
Physical Surface(1) = {s};  // Physical surface to be mesh (then we'll add fine portion)

// Create line loop for fine area (containing the cylinder)
fine_outer = newll;
Line Loop(fine_outer) = {(l+6), (l+2), (l+7), (l+8)};  // Outer line loop of fine zone
fine_inner = newll;
Line Loop(fine_inner) = {cylinder[]}; // Inner line loop (cylinder)

// Define final physical surface
s = news;
Plane Surface(s) = {fine_outer, fine_inner}; // Should be outer, inner, no??
Physical Surface(1) += {s}; // // Add to surface to be mesh


// First the jet and no slip surfaces of the cylinder are defined. Each jet surface is a physical line and all the no slip
// cylinder surfaces are another. Then the domain is created.