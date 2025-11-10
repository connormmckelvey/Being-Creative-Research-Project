from pathlib import Path
from xy_to_angles_inverse_kinamatics import compute_joint_angles

BASE_DIR = Path(__file__).parent.parent

def generate_commands(xypoints, l1, l2):
    ''' Generate a list of commands from a list of (x, y) coordinates.
        Commands are tuples of (theta1, theta2) for the two joints, or strings "PEN UP", "PEN DOWN", "START", "END".
        l1 and l2 are the lengths of the two arm segments.
        xypoints is a list of (x, y) tuples, where (None, None) indicates pen up movement. in the form returned by svg_to_points_list
    '''
    command_list = xypoints.copy()

    is_down = True
    for i in range(len(xypoints)):
        if xypoints[i] == (None, None):
            if is_down:
                command_list[i] = "PEN UP"
                is_down = False
            else:
                command_list[i] = "PEN DOWN"
                is_down = True
        else:
            try:
              command_list[i] = compute_joint_angles(xypoints[i][0], xypoints[i][1], l1, l2)
            except ValueError as e:
                print(f"Warning: {e}. print {xypoints[i]} skipped.")

    command_list.insert(0, "START")
    command_list.insert(2, "PEN DOWN")  # Start with pen up

    command_list.append("PEN UP")  # End with pen up
    command_list.append("END")
    return command_list

def generate_commands_file(command_list, name):
    ''' Generate a command file from a list of commands given in the format returned by generate_commands '''
    name = f"commands_{name}.txt"
    with open(BASE_DIR / "data" / "command_file_storage" / name, "w") as f:
        for command in command_list:
            f.write(f"{command}\n")

