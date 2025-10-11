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


def draw_points(points):
    plt.ion()
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.set_xlim(-200, 200)
    ax.set_ylim(-200, 200)
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
            # move pen without drawing
            pen_x.append(None)
            pen_y.append(None)
            pen_down = True  # lower pen after moving

        plt.draw()
        plt.pause(0.02)

    plt.ioff()
    plt.show()

# --- Main ---
if __name__ == "__main__":
    points = load_points(filename=BASE_DIR / "data" / "output.txt")
    draw_points(points)
