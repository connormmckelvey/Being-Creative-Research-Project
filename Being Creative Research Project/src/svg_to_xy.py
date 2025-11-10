import numpy as np
from rdp import rdp
from svgpathtools import svg2paths2, Path as svgPath
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
# IMPORTANT: This tolerance value controls the level of simplification applied 
# to all paths. It must be consistent for human and AI drawings to ensure 
# the 'standardized_node_count' is a fair comparison metric.
RDP_TOLERANCE = 1.0 
SAMPLES_PER_SEGMENT = 20 # Used for sampling the curve into a polyline before RDP

# NOTE: Assuming BASE_DIR is set up in your main environment to point to the root
# of your project where 'data/svg_files' resides.
BASE_DIR = Path(__file__).parent.parent

# --- RDP SIMPLIFICATION HELPER (FIXED) ---

def simplify_polyline_rdp(points, tolerance):
    """
    Applies the Ramer-Douglas-Peucker (RDP) algorithm to a polyline.
    
    FIX: Explicitly casts NumPy floats back to standard Python floats.
    """
    if not points:
        return []
        
    # RDP library requires a NumPy array
    points_array = np.array(points)
    
    # Apply RDP simplification
    simplified_array = rdp(points_array, epsilon=tolerance)
    
    # Convert back to a list of tuples, explicitly converting NumPy types to standard Python floats.
    # This prevents the unwanted 'np.float64(...)' type string when writing to files.
    return [(float(p[0]), float(p[1])) for p in simplified_array]


# --- POINT SAMPLING HELPER (RETAINED) ---

def _sample_raw_points_for_path(path_list, samples_per_segment):
    """
    Samples raw (x, y) points from a list of svgPath objects (a single stroke).
    """
    raw_stroke_points = []
    
    for segment in path_list:
        # Sample points along the segment (excluding the final endpoint to prevent double counting between segments)
        num_samples = samples_per_segment 
        for i in range(num_samples):
            t = i / samples_per_segment
            point = segment.point(t)
            # svgpathtools returns complex numbers; extract real/imag as standard floats
            raw_stroke_points.append((float(point.real), float(point.imag)))
            
    # Add the final point of the last segment to close the stroke
    if path_list:
        last_segment = path_list[-1]
        point = last_segment.point(1.0)
        raw_stroke_points.append((float(point.real), float(point.imag)))
        
    return raw_stroke_points


# --- MAIN METRICS FUNCTION (RETAINED) ---

def calculate_standardized_metrics(svg_path_name):
    """
    Calculates key complexity metrics, including a standardized node count 
    obtained via RDP simplification.
    """
    svg_file_path = BASE_DIR / "data" / "svg_files" / svg_path_name
    
    try:
        paths, attributes, svg_attributes = svg2paths2(svg_file_path)
    except Exception as e:
        print(f"Error reading SVG file {svg_path_name}: {e}")
        return {
            "total_path_length": 0.0,
            "stroke_count": 0,
            "standardized_node_count": 0
        }

    # Split into distinct strokes
    split_paths = split_svg_paths(paths) 
    
    total_length = 0.0
    standardized_node_count = 0
    stroke_count = len(split_paths)

    # 1. Iterate through all distinct strokes/paths
    for path in split_paths:
        # A. Calculate total geometric path length
        total_length += path.length()
        
        # B. Sample, Simplify, and Count Standardized Nodes
        raw_stroke_points = _sample_raw_points_for_path(path, SAMPLES_PER_SEGMENT)
        simplified_points = simplify_polyline_rdp(raw_stroke_points, RDP_TOLERANCE)
        
        # The standardized node count is the number of points in the simplified polyline
        standardized_node_count += len(simplified_points)

    return {
        "total_path_length": total_length,
        "stroke_count": stroke_count,
        "standardized_node_count": standardized_node_count
    }


# --- MAIN POINT GENERATION FUNCTION (RETAINED) ---

def svg_to_simplified_points_list(svg_path, samples_per_segment, arm_L1, arm_L2, margin):
    '''
    Convert an SVG file to a list of (x, y) coordinates. Paths are simplified 
    using RDP to standardize complexity before scaling/translation.
    '''
    svg_file_path = BASE_DIR / "data" / "svg_files" / svg_path
    paths, attributes, svg_attributes = svg2paths2(svg_file_path)
    split_paths = split_svg_paths(paths)

    # --- Collect simplified points ---
    simplified_points = []
    
    for path in split_paths:
        # 1. Sample Raw Points
        raw_stroke_points = _sample_raw_points_for_path(path, samples_per_segment)
        
        # 2. Apply RDP Simplification (Standardization)
        # The result here is guaranteed to be standard Python floats due to the fix in simplify_polyline_rdp
        simplified_stroke_points = simplify_polyline_rdp(raw_stroke_points, RDP_TOLERANCE)
        
        # 3. Append to the final list with separators
        simplified_points.extend(simplified_stroke_points)
        simplified_points.append((None, None))  # Separator between paths

    # --- Scale and move to fit on paper ---
    scaled_points = normalize_and_scale_points(simplified_points, arm_L1 * 0.9, arm_L2 * 0.9, margin)

    # Add pen down/up instructions for robot (using your existing helper)
    scaled_points = add_pen_down_none_tuples(scaled_points)
    scaled_points.append((None, None))
    return scaled_points


# --- DEPENDENT HELPER FUNCTIONS ---

def get_point_lists_from_svgs(svg_file_paths, samples_per_segment=SAMPLES_PER_SEGMENT, arm_L1=12.5, arm_L2=12.5, margin=1.0):
    point_lists = []
    for svg_file_path in svg_file_paths:
        points = svg_to_simplified_points_list(svg_file_path, samples_per_segment, arm_L1, arm_L2, margin)
        point_lists.append(points)
    return point_lists


def split_svg_paths(paths):
    split_paths = []
    for path in paths:
        current_path = svgPath()
        for segment in path:
            if len(current_path) > 0 and segment.start != current_path[-1].end:
                split_paths.append(current_path)
                current_path = svgPath()
            current_path.append(segment)
        if len(current_path) > 0:
            split_paths.append(current_path)
    return split_paths


def add_pen_down_none_tuples(points):
    none_indices = []
    for i in range(len(points)):
        if points[i] == (None, None):
            none_indices.append(i)
    for idx in range(len(none_indices) - 1):
        pos = none_indices[idx]
        insert_pos = pos + 2 + idx  
        points.insert(insert_pos, (None, None))
    return points


def normalize_and_scale_points(points, l1, l2, margin=1.0):
    """
    Normalize and scale SVG points so they fit inside the robot’s reachable area.
    
    FIX: Inverts the Y-axis to correctly translate SVG coordinates (Y increases down)
    to Cartesian coordinates (Y increases up).
    """
    valid_points = [(x, y) for (x, y) in points if x is not None and y is not None]
    if not valid_points:
        return points

    xs = [p[0] for p in valid_points]
    ys = [p[1] for p in valid_points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = max_x - min_x
    height = max_y - min_y

    # The maximum distance the arm can reach diagonally
    max_reach = l1 + l2 - margin

    # Scale uniformly so that farthest corner fits within circular reach
    diagonal = (width**2 + height**2)**0.5
    scale = max_reach / diagonal if diagonal != 0 else 1

    scaled_points = []
    for (x, y) in points:
        if x is None or y is None:
            scaled_points.append((None, None))
        else:
            # X Translation and Scaling (normal)
            new_x = (x - min_x) * scale + margin
            
            # Y Translation and Scaling (INVERTED)
            # This maps max_y (bottom of SVG) to min scaled Y, and min_y (top of SVG) 
            # to max scaled Y, effectively flipping the image right-side up.
            new_y = (max_y - y) * scale + margin 
            
            # Explicitly cast the final coordinates to standard Python floats
            scaled_points.append((float(new_x), float(new_y)))

    return scaled_points