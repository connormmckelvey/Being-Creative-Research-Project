from svgpathtools import svg2paths2, Path as svgPath
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def svg_to_points_list(svg_path, samples_per_segment, arm_L1, arm_L2, margin):
    '''
    Convert an SVG file to a list of (x, y) coordinates by sampling points along its paths,
    scaled and translated so they fit within the robot arm's reach region (L1 + L2).
    Paths are separated by (None, None).
    '''
    svg_file_path = BASE_DIR / "data" / "svg_files" / svg_path
    paths, attributes, svg_attributes = svg2paths2(svg_file_path)
    paths = split_svg_paths(paths)

    # --- Collect raw SVG points ---
    raw_points = []
    for path in paths:
        for segment in path:
            for t in [i / samples_per_segment for i in range(samples_per_segment + 1)]:
                point = segment.point(t)
                raw_points.append((point.real, point.imag))
        raw_points.append((None, None))  # Separator between paths

    # --- Scale and move to fit on paper ---
    scaled_points = normalize_and_scale_points(
        raw_points,
        arm_L1 + arm_L2,
        margin
    )

    scaled_points = add_pen_down_none_tuples(scaled_points)
    scaled_points.append((None, None))
    return scaled_points


def get_point_lists_from_svgs(svg_file_paths, samples_per_segment=20, arm_L1=12.5, arm_L2=12.5):
    point_lists = []
    for svg_file_path in svg_file_paths:
        points = svg_to_points_list(svg_file_path, samples_per_segment, arm_L1, arm_L2)
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


def normalize_and_scale_points(points, max_reach, margin):
    """
    Move and scale SVG points so they fit inside the robot’s reachable area (0,0 corner).
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

    # Max area the arm can draw in (approx. a circle radius max_reach)
    max_size = (max_reach - margin)

    # Uniform scaling to fit within reach
    scale = min(max_size / width, max_size / height)

    # Translate so (0,0) is the lower-left of the drawing area
    scaled_points = []
    for (x, y) in points:
        if x is None or y is None:
            scaled_points.append((None, None))
        else:
            new_x = (x - min_x) * scale + margin
            new_y = (y - min_y) * scale + margin
            scaled_points.append((new_x, new_y))
    return scaled_points
