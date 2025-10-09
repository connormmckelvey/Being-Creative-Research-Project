from svgpathtools import svg2paths
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
svg_file_path = BASE_DIR / "data" / "svg_files" / "cloud-arrow-down.svg"


def svg_to_points_list(svg_file_path, samples_per_segment=20):
    paths, attributes = svg2paths(svg_file_path)
    all_points = []

    for path in paths:
        for segment in path:
            for t in [i / samples_per_segment for i in range(samples_per_segment + 1)]:
                point = segment.point(t)
                all_points.append((point.real, point.imag))

    return all_points


points = svg_to_points_list(svg_file_path)
print(points[:10])  # first few (x, y) coordinates
