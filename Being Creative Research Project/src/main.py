from svg_to_xy import *
from xy_to_angles_inverse_kinamatics import *
from command_generator import *
from pathlib import Path
import serial
import time

BASE_DIR = Path(__file__).parent.parent
COMMAND_FILE = BASE_DIR / "data" / "command_files" / "commands.txt"

def main(port='COM3', baudrate=9600, timeout=1, delay=0.05):
    """
    Sends commands from a text file to the Arduino via serial line-by-line.
    Each line is sent only after the Arduino responds with 'OK' or similar.
    """
    if not COMMAND_FILE.exists():
        print(f"Error: command file not found at {COMMAND_FILE}")
        return

    # Read all commands from file
    with open(COMMAND_FILE, 'r') as f:
        commands = [line.strip() for line in f if line.strip()]

    if not commands:
        print("Error: command file is empty.")
        return

    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Connected to {port} at {baudrate} baud.")
            time.sleep(2)  # Wait for Arduino to reset

            for i, cmd in enumerate(commands):
                ser.write((cmd + '\n').encode())
                print(f"[{i+1}/{len(commands)}] Sent: {cmd}")

                #Optional: wait for Arduino acknowledgment
                while True:
                    response = ser.readline().decode().strip()
                    if response:
                        print(f"Arduino: {response}")
                        if response.lower() in ["ok", "done", "next"]:
                            break
                        elif "error" in response.lower():
                            print("Arduino reported an error. Stopping.")
                            return
                    time.sleep(delay)

            print("✅ All commands sent successfully.")

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == '__main__':
    main()
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
    #print((svg_to_points_list("cloud-arrow-down.svg"))[:50])
    #generate_commands_file(generate_commands(svg_to_points_list("cloud-arrow-down.svg"), 20, 20))