import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import ast
import random

# --- CONFIGURATION ---
# NOTE: Adjust BASE_DIR if your main script's BASE_DIR is located differently.
BASE_DIR = Path(__file__).parent.parent 
XY_FILE_DIR = BASE_DIR / "data" / "xy_files"

def read_points_file():
    """
    Reads the list of (x, y) coordinates from a text file.
    
    IMPORTANT: This now assumes the file contains one tuple per line, 
    matching the line-by-line output format of the external script.
    """
    xy_file_path = next(XY_FILE_DIR.glob('*'))
    points_list = []
    
    try:
        with open(xy_file_path, 'r') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line:
                    # Use ast.literal_eval to safely convert the string representation of the tuple 
                    # (e.g., "(1.2, 3.4)" or "(None, None)") back into a Python tuple.
                    point = ast.literal_eval(stripped_line)
                    points_list.append(point)
            return points_list
    except FileNotFoundError:
        print(f"Error: File not found at {xy_file_path}")
        return []
    except Exception as e:
        # e.g., invalid syntax (<unknown>, line X)
        print(f"Error reading or parsing file {xy_file_path}: {e}")
        return []

def plot_xy_points(points_list, title="SVG Path Visualization"):
    """
    Plots the list of (x, y) coordinates, handling (None, None) as path breaks.
    
    Args:
        points_list (list): The list of (x, y) coordinates with (None, None) separators.
        title (str): The title for the plot.
    """
    if not points_list:
        print("No points to plot.")
        return

    plt.figure(figsize=(8, 8))
    plt.title(title)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True)
    
    # Track continuous segments
    current_stroke = []

    for point in points_list:
        # Check for (None, None) or if the element is not a tuple (safety check, should be a tuple)
        if point == (None, None) or not isinstance(point, tuple):
            # End of a stroke/segment
            if current_stroke:
                # Convert list of tuples to numpy arrays for plotting
                xs = [p[0] for p in current_stroke]
                ys = [p[1] for p in current_stroke]
                
                # Assign a random color to each stroke for easy differentiation
                color = (random.random(), random.random(), random.random())
                
                # Plot the stroke as a connected line, with a small marker for every point
                plt.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=2)
                
                # Plot the start/end points of the actual drawing path for clarity
                # Ensure the labels only appear once in the legend
                start_label = 'Start Point' if not any('Start Point' in L.get_label() for L in plt.gca().lines) else ""
                end_label = 'End Point' if not any('End Point' in L.get_label() for L in plt.gca().lines) else ""

                if len(current_stroke) > 0:
                    # Plot start and end with different markers/colors for clarity
                    plt.plot(xs[0], ys[0], 'o', color='green', markersize=5, label=start_label)
                    plt.plot(xs[-1], ys[-1], 'x', color='red', markersize=5, label=end_label)

            current_stroke = []
        else:
            # Add valid point to the current stroke
            current_stroke.append(point)
            
    # Add legend to clarify start/end points
    if any(L.get_label() for L in plt.gca().lines):
        # Filter out stroke line labels and keep only unique start/end labels
        handles, labels = plt.gca().get_legend_handles_labels()
        unique_legend = {}
        for h, l in zip(handles, labels):
            if l:
                unique_legend[l] = h
        
        legend_handles = list(unique_legend.values())
        legend_labels = list(unique_legend.keys())
        
        if legend_labels:
            plt.legend(legend_handles, legend_labels, loc='best')

    # Show the plot
    plt.show()

if __name__ == '__main__':
    # 2. Read the points from the file
    points = read_points_file()
    
    # 3. Plot the data
    plot_xy_points(points, title=f"Visualization of XY Points from {next(XY_FILE_DIR.glob('*')).name}")
    