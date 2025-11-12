import numpy as np
from rdp import rdp
from svgpathtools import svg2paths2, Path as svgPath
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
RDP_TOLERANCE = 5.0 
SAMPLES_PER_SEGMENT = 20

# NOTE: Assuming BASE_DIR is set up in your main environment to point to the root
BASE_DIR = Path(__file__).parent.parent

# --- RDP SIMPLIFICATION HELPER (RETAINED) ---

def simplify_polyline_rdp(points, tolerance):
    """
    Applies the Ramer-Douglas-Peucker (RDP) algorithm to a polyline.
    """
    if not points:
        return []
        
    points_array = np.array(points)
    simplified_array = rdp(points_array, epsilon=tolerance)
    
    # Convert back to a list of standard Python floats
    return [(float(p[0]), float(p[1])) for p in simplified_array]


# --- POINT SAMPLING HELPER (RETAINED) ---

def _sample_raw_points_for_path(path_list, samples_per_segment):
    """
    Samples raw (x, y) points from a list of svgPath objects (a single stroke).
    """
    raw_stroke_points = []
    
    for segment in path_list:
        num_samples = samples_per_segment 
        for i in range(num_samples):
            t = i / samples_per_segment
            point = segment.point(t)
            raw_stroke_points.append((float(point.real), float(point.imag)))
            
    if path_list:
        last_segment = path_list[-1]
        point = last_segment.point(1.0)
        raw_stroke_points.append((float(point.real), float(point.imag)))
        
    return raw_stroke_points


# --- MAIN METRICS FUNCTION (RETAINED) ---

def calculate_standardized_metrics(svg_path_name):
    """
    Calculates key complexity metrics, including a standardized node count 
    obtained via RDP simplification. (No coordinate flip needed here.)
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

    split_paths = split_svg_paths(paths) 
    
    total_length = 0.0
    standardized_node_count = 0
    stroke_count = len(split_paths)

    for path in split_paths:
        total_length += path.length()
        raw_stroke_points = _sample_raw_points_for_path(path, SAMPLES_PER_SEGMENT)
        simplified_points = simplify_polyline_rdp(raw_stroke_points, RDP_TOLERANCE)
        standardized_node_count += len(simplified_points)

    return {
        "total_path_length": total_length,
        "stroke_count": stroke_count,
        "standardized_node_count": standardized_node_count
    }


# --- MAIN POINT GENERATION FUNCTION (UPDATED) ---

def svg_to_simplified_points_list(svg_path, samples_per_segment, arm_L1, arm_L2, margin):
    '''
    Convert an SVG file to a list of (x, y) coordinates. Paths are simplified 
    using RDP to standardize complexity before scaling/translation.
    
    The Y-axis is automatically inverted if the filename contains '_AI'.
    '''
    svg_file_path = BASE_DIR / "data" / "svg_files" / svg_path
    
    # --- AUTOMATIC INVERSION LOGIC ---
    # Check if the file is AI-generated and needs Y-axis inversion
    invert_y = "_AI" in svg_path
    # -----------------------------------
    
    paths, attributes, svg_attributes = svg2paths2(svg_file_path)
    split_paths = split_svg_paths(paths)

    # --- Collect simplified points ---
    simplified_points = []
    
    for path in split_paths:
        raw_stroke_points = _sample_raw_points_for_path(path, samples_per_segment)
        simplified_stroke_points = simplify_polyline_rdp(raw_stroke_points, RDP_TOLERANCE)
        
        simplified_points.extend(simplified_stroke_points)
        simplified_points.append((None, None))  # Separator between paths

    # --- Scale and move to fit on paper ---
    scaled_points = normalize_and_scale_points(simplified_points, arm_L1 * 0.9, arm_L2 * 0.9, margin, invert_y)

    # Add pen down/up instructions for robot
    scaled_points = add_pen_down_none_tuples(scaled_points)
    scaled_points.append((None, None))
    return scaled_points


# --- DEPENDENT HELPER FUNCTIONS (UPDATED) ---

def get_point_lists_from_svgs(svg_file_paths, samples_per_segment=SAMPLES_PER_SEGMENT, arm_L1=12.5, arm_L2=12.5, margin=1.0):
    """
    Processes a list of SVG files, automatically applying coordinate inversion
    based on the '_AI' naming convention.
    """
    point_lists = []
    for svg_file_path in svg_file_paths:
        # Call the single-file function, which now handles inversion automatically
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


def normalize_and_scale_points(points, l1, l2, margin, invert_y):
    """
    Normalize and scale SVG points. Conditionally inverts Y-axis based on the 
    'invert_y' flag passed from the caller (which checks the filename).
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

    max_reach = l1 + l2 - margin
    diagonal = (width**2 + height**2)**0.5
    scale = max_reach / diagonal if diagonal != 0 else 1

    scaled_points = []
    for (x, y) in points:
        if x is None or y is None:
            scaled_points.append((None, None))
        else:
            # X Translation and Scaling
            new_x = (x - min_x) * scale + margin
            
            if invert_y:
                # Flips the Y-axis (for AI-generated Cartesian/Y-up sources)
                # It maps the original max_y to the scaled min, and min_y to scaled max.
                new_y = (max_y - y) * scale + margin
            else:
                # Standard Y-axis (for human/SVG Y-down sources)
                new_y = (y - min_y) * scale + margin
            
            scaled_points.append((float(new_x), float(new_y)))

    return scaled_points