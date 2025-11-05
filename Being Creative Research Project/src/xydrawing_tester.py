import ast
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def load_points(filename):
    points = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                points.append(ast.literal_eval(line))
    return points


def draw_points(points, arm_L1=12.5, arm_L2=12.5, margin=2, speed=0.001):
    """
    Visualize robot drawing path.
    Automatically scales axes to match robot reach and draws faster.
    """
    # Determine total reach in same units as your (x, y) data
    max_reach = arm_L1 + arm_L2
    limit = max_reach + margin

    plt.ion()
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_title("Robot Drawing Path")
    ax.set_xlabel("X (cm)")
    ax.set_ylabel("Y (cm)")
    line, = ax.plot([], [], 'r-', lw=2)
    pen_x, pen_y = [], []
    pen_down = True

    for (x, y) in points:
        if x is None or y is None:
            pen_down = False
            continue

        if pen_down:
            pen_x.append(x)
            pen_y.append(y)
            line.set_data(pen_x, pen_y)
        else:
            # lift pen and move without drawing
            pen_x.append(None)
            pen_y.append(None)
            pen_down = True  # lower pen after moving

        plt.pause(speed)

    plt.ioff()
    plt.show()


# --- Main ---
if __name__ == "__main__":
    xy_folder = BASE_DIR / "data" / "xy_file_storage"
    for file in xy_folder.iterdir():
        points = load_points(filename=xy_folder / file.name)
        draw_points(points, arm_L1=12.5, arm_L2=12.5, margin=2, speed=0.001)
        plt.close('all')
