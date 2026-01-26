DefineConstant[
jets_toggle = {1, Name "Toggle Jets --> 0 : No jets, 1: Yes jets"}
height_cylinder = {1, Name "Cylinder Height (ND)"}
ar = {1.0, Name "Cylinder Aspect Ratio"}
cylinder_y_shift = {0.0, Name "Cylinder Center Shift from Centerline, Positive UP (ND)"}
x_upstream = {20, Name "Domain Upstream Length (from left-most rect point) (ND)"}
x_downstream = {26, Name "Domain Downstream Length (from right-most rect point) (ND)"}
height_domain = {25, Name "Domain Height (ND)"}
coarse_y_distance_top_bot = {4, Name "y-distance from center where mesh coarsening starts"}
coarse_x_distance_left_from_LE = {2.5, Name "x-distance from upstream face where mesh coarsening starts"}
mesh_size_cylinder = {0.05, Name "Mesh Size on Cylinder Walls"}
mesh_size_jets = {0.015, Name "Mesh Size on jet suirfaces"}
mesh_size_medium = {0.45, Name "Medium mesh size (at boundary where coarsening starts"}
mesh_size_coarse = {1, Name "Coarse mesh Size Close to Domain boundaries outside wake"}
jet_width = {0.1, Name "Jet Width (ND)"}
];

// Seed the cylinder's center's identifier and create the center point
center = newp;
Point(center) = {0, 0, 0, mesh_size_cylinder};

// V-shape geometry: 70 degree half-angle, tip pointing upstream
v_angle = 70 * Pi / 180; // Half angle in radians (70 degrees, total 140 degrees)

// Scaling factor: scale the geometry so that y-direction total length = 1
// Original y-direction length is 2*tan(70°)*r_length, now we want it to be 1
scale_factor = 1.0 / (2.0 * Tan(v_angle));

// V-shape dimensions (scaled)
r_height = height_cylinder; // V-shape characteristic height
r_length = ar * height_cylinder * scale_factor; // V-shape length (from tip to rear), scaled
arm_thickness = 0.064; // the thickness of each V arm, scaled
jet_interval = 0.01; // interval between jet and rear edge, scaled

// Define key x coordinates
x_tip = -r_length/2;  // Front tip (most upstream point)
x_rear = r_length/2;  // Rear edge (most downstream point)

// Define V-shape outer points based on scaled dimensions
y_rear_top_outer = (x_rear - x_tip) * Tan(v_angle);  // Top rear corner y-coordinate (= 0.5 after scaling)
y_rear_bot_outer = -(x_rear - x_tip) * Tan(v_angle); // Bottom rear corner y-coordinate (= -0.5 after scaling)

thickness_offset_x = arm_thickness * Sin(v_angle);
thickness_offset_y = arm_thickness * Cos(v_angle);
x_rear_inner = x_rear + thickness_offset_x;
x_tip_inner = x_tip +  arm_thickness / Sin(v_angle);
y_rear_top_inner = y_rear_top_outer - thickness_offset_y;
y_rear_bot_inner = y_rear_bot_outer + thickness_offset_y;

// Jet positioning on rear outer edges
// Jets are positioned on the rear slanted edges
x_jet_start = x_rear_inner - (jet_width + jet_interval) * Cos(v_angle);  // Jet upstream bound x
x_jet_end = x_rear_inner - jet_interval * Cos(v_angle);
y_jet_top_start = y_rear_top_inner - (jet_width + jet_interval) * Sin(v_angle);  // Top jet upstream y
y_jet_bot_start = y_rear_bot_inner + (jet_width + jet_interval) * Sin(v_angle);  // Bottom jet upstream y
y_jet_top_end = y_rear_top_inner - jet_interval * Sin(v_angle);
y_jet_bot_end = y_rear_bot_inner + jet_interval * Sin(v_angle);



// Calculate jet center points
x_jet_centre = (x_jet_start + x_jet_end) / 2;
y_jet_top_centre = (y_jet_top_start + y_jet_top_end) / 2;
y_jet_bot_centre = (y_jet_bot_start + y_jet_bot_end) / 2;

// Define all points of V-shape (defined in CCW sense)
p = newp;
Point(p) = {x_tip, 0, 0, mesh_size_cylinder};  // Front tip outer
Point(p+1) = {x_rear, y_rear_top_outer, 0, mesh_size_cylinder};  // Top rear corner outer
Point(p+2) = {x_rear_inner, y_rear_top_inner, 0, mesh_size_cylinder};  // Top rear corner inner
Point(p+5) = {x_jet_start, y_jet_top_start, 0, mesh_size_jets};  // Top jet upstream bound
Point(p+4) = {x_jet_centre, y_jet_top_centre, 0, mesh_size_jets};  // Top jet centre
Point(p+3) = {x_jet_end, y_jet_top_end, 0, mesh_size_jets};  // Top jet downstream bound
Point(p+6) = {x_tip_inner, 0, 0, mesh_size_cylinder};  // Front tip inner
Point(p+9) = {x_jet_end, y_jet_bot_end, 0, mesh_size_jets};  // Bottom jet downstream bound
Point(p+8) = {x_jet_centre, y_jet_bot_centre, 0, mesh_size_jets};  // Bottom jet centre
Point(p+7) = {x_jet_start, y_jet_bot_start, 0, mesh_size_jets};  // Bottom jet upstream bound
Point(p+10) = {x_rear_inner, y_rear_bot_inner, 0, mesh_size_cylinder};  // Bottom rear corner inner
Point(p+11) = {x_rear, y_rear_bot_outer, 0, mesh_size_cylinder};  // Bottom rear corner outer

If(jets_toggle)

  cylinder[] = {}; // Create empty list of curves (surfaces) of the V-shape body. Defined CCW
  no_slip_cyl[] = {};  // No-slip V-shape physical surfaces list

  // Define top outer edge (from tip to top rear outer corner)
  l = newl;
  Line(l) = {p, p+1};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Define top rear edge (from outer to inner)
  l = newl;
  Line(l) = {p+1, p+2};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Define top inner edge (from rear inner to jet start)
  l = newl;
  Line(l) = {p+2, p+3};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Define top jet surface
  l = newl;
  Line(l) = {p+3, p+4};
  Line(l+1) = {p+4, p+5};
  Physical Line(5) = {l, l+1};  // Top jet physical surface
  cylinder[] += {l, l+1}; // Add to V-shape list

  // Define inner edge (from top jet end to front tip inner)
  l = newl;
  Line(l) = {p+5, p+6};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Define inner edge (from front tip inner to bottom jet start)
  l = newl;
  Line(l) = {p+6, p+7};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Define bottom jet surface
  l = newl;
  Line(l) = {p+7, p+8};
  Line(l+1) = {p+8, p+9};
  Physical Line(6) = {l, l+1};  // Bottom jet physical surface
  cylinder[] += {l, l+1}; // Add to V-shape list

  // Define bottom inner edge (from jet end to rear inner)
  l = newl;
  Line(l) = {p+9, p+10};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Define bottom rear edge (from inner to outer)
  l = newl;
  Line(l) = {p+10, p+11};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  // Define bottom outer edge (from rear outer to tip, closing the loop)
  l = newl;
  Line(l) = {p+11, p};
  no_slip_cyl[] += {l};
  cylinder[] += {l};

  Physical Line(4) = {no_slip_cyl[]};  // Define no-slip V-shape physical surfaces

// Just the V-shape without jets
Else

   l = newl;
   Line(l) = {p, p+1};  // Top slanted edge (tip to top rear)
   Line(l+1) = {p+1, p+2};  // Rear vertical edge
   Line(l+2) = {p+2, p+6};  // Bottom slanted edge (bottom rear to tip)
   Line(l+3) = {p+6, p+10};  // Closing edge (tip to tip)
   Line(l+4) = {p+10, p+11};
   Line(l+5) = {p+11, p};  // Closing edge (tip to tip)

   cylinder[] = {l, l+1, l+2, l+3, l+4, l+5};	// List of curves (surfaces) of the V-shape. Defined CCW
   Physical Line(4) = {cylinder[]}; // Define no-slip V-shape physical surfaces (in this case all)
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