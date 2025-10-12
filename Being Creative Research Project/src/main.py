from svg_to_xy import *
from xy_to_angles_inverse_kinamatics import *
from command_generator import *
#import serial 
import time
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent


def main(port = 'COM3', baudrate = 9600, timeout = 1):
    '''
    Main function to send instructions to Arduino via serial port
    '''
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f'Connected to {port} at {baudrate} baud.')
            time.sleep(2)  # Wait for Arduino to reset
            while True:
                if ser.in_waiting:
                    pass
    except serial.SerialException as e:
        print(f'Error: {e}')
    except KeyboardInterrupt:
        print('Exiting...')


if __name__ == '__main__':
    #main()
    #for file in (BASE_DIR / "data" / "svg_files").iterdir():
        # points = svg_to_points_list(file.name)
        # for point in points[:10]:
        #     print(point)  # first few (x, y) coordinates
        # print("first joint angles (degrees):")
        # #for point in points[:10]:
        # #    print(compute_joint_angles(point[0], point[1], 10, 10))
        # with open(BASE_DIR / "data" / f"output_{file.name}.txt", "w") as f:
        #     for point in points:
        #         f.write(f"{point}\n")
    print((svg_to_points_list("cloud-arrow-down.svg"))[:50])
    generate_commands_file(generate_commands(svg_to_points_list("cloud-arrow-down.svg"), 20, 20))