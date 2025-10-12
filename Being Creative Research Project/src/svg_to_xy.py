from svgpathtools import svg2paths2, Path as svgPath, Line
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def svg_to_points_list(svg_path, samples_per_segment=20):
    '''
    Convert an SVG file to a list of (x, y) coordinates by sampling points along its paths, paths are seperated by cords with (None, None).
    '''
    svg_file_path = BASE_DIR / "data" / "svg_files" / svg_path
    paths, attributes, svg_attributes = svg2paths2(svg_file_path)
    paths = split_svg_paths(paths)
    all_points = []
    for path in paths:
        iter_count = 0
        for segment in path:
            for t in [i / samples_per_segment for i in range(samples_per_segment + 1)]:
                point = segment.point(t)
                all_points.append((point.real, point.imag))
        all_points.append((None, None))  # Separator between paths
    all_points = add_pen_down_none_tuples(all_points)
    all_points.append((None, None))
    return all_points

def get_point_lists_from_svgs(svg_file_paths, samples_per_segment=20):
    point_lists = []
    for svg_file_path in svg_file_paths:
        points = svg_to_points_list(svg_file_path, samples_per_segment)
        point_lists.append(points)
    return point_lists

def split_svg_paths(paths):
    split_paths = []

    for path in paths:
        current_path = svgPath()
        for segment in path:
            # A segment with a "start" that doesn't match the previous "end"
            # usually means a new subpath started (a new 'M' command).
            if len(current_path) > 0 and segment.start != current_path[-1].end:
                split_paths.append(current_path)
                current_path = svgPath()
            current_path.append(segment)
        if len(current_path) > 0:
            split_paths.append(current_path)
    return split_paths

def add_pen_down_none_tuples(points):
    # First, find all indices of (None, None)
    none_indices = []
    for i in range(len(points)):
        if points[i] == (None, None):
            none_indices.append(i)
    
    # Ignore the last one
    for idx in range(len(none_indices) - 1):
        pos = none_indices[idx]
        # Insert two positions after, accounting for previous insertions
        insert_pos = pos + 2 + idx
        points.insert(insert_pos, (None, None))
    return points
#points = svg_to_points_list(svg_file_path)
#print(points[:10])  # first few (x, y) coordinates
