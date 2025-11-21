from svg_to_xy import *
from xy_to_angles_inverse_kinamatics import *
from command_generator import *
from xydrawing_tester import *
from pathlib import Path
import serial
import time
import shutil


# --- Configuration ---
BASE_DIR = Path(__file__).parent.parent
# Make sure this path points correctly to your commands.txt file
COMMAND_FILE_DIR = BASE_DIR / "data" / "command_files" 
SERIAL_PORT = 'COM3'  # <-- CHANGE THIS to your Arduino's serial port
BAUDRATE = 9600

# --- Constants ---
# These should match the constants in your Arduino sketch
ARDUINO_BUFFER_SIZE = 10
ARDUINO_LOW_THRESHOLD = 3
# Calculate batch size to send to avoid overflowing the Arduino buffer
COMMAND_BATCH_SIZE = ARDUINO_BUFFER_SIZE - ARDUINO_LOW_THRESHOLD


def main():
    """
    Connects to the Arduino and sends commands in batches upon request.
    """
    COMMAND_FILE = next(COMMAND_FILE_DIR.glob('*'))
    if not COMMAND_FILE.exists():
        print(f"❌ Error: Command file not found at {COMMAND_FILE}")
        return

    # Read all commands from the file, filtering out empty lines
    with open(COMMAND_FILE, 'r') as f:
        # Also filter out any lines with '(None, None)'
        commands = [
            line.strip() for line in f 
            if line.strip() and '(None, None)' not in line
        ]

    if not commands:
        print("❌ Error: Command file is empty or contains no valid commands.")
        return

    print("Attempting to connect to Arduino...")
    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as ser:
            print(f"✅ Connected to {SERIAL_PORT} at {BAUDRATE} baud.")
            print("Waiting for Arduino to initialize...")
            time.sleep(2)  # Wait for Arduino to reset

            # --- Synchronization: Wait for the first REQUEST ---
            print("Waiting for the first 'REQUEST' from Arduino to start...")
            initial_request_received = False
            while not initial_request_received:
                if ser.in_waiting > 0:
                    response = ser.readline().decode().strip()
                    if response:
                        print(f"Arduino: {response}")
                    if "REQUEST" in response:
                        initial_request_received = True
                        print("🚀 Arduino is ready! Starting command stream.")
            
            # --- Main Sending Loop ---
            command_index = 0
            while command_index < len(commands):
                if ser.in_waiting > 0:
                    response = ser.readline().decode().strip()
                    if response:
                        print(f"Arduino: {response}")

                    # If Arduino requests more, send the next batch
                    if "REQUEST" in response:
                        print(f"--> Received REQUEST. Sending batch of up to {COMMAND_BATCH_SIZE} commands.")
                        
                        for _ in range(COMMAND_BATCH_SIZE):
                            if command_index < len(commands):
                                cmd = commands[command_index]
                                ser.write((cmd + '\n').encode())
                                print(f"    Sent [{command_index + 1}/{len(commands)}]: {cmd}")
                                command_index += 1
                                time.sleep(0.5) # Small delay between sends
                            else:
                                break # No more commands left
            
            print("\n🎉 All commands sent. Waiting for Arduino to finish...")
            
            # --- FIX: Wait for the buffer to empty ---
            # Keep the serial port open and listen for the final
            # "REQUEST" signals, which indicate the buffer is empty.
            final_request_count = 0
            while final_request_count < 2: # Wait for 2 more requests
                if ser.in_waiting > 0:
                    response = ser.readline().decode().strip()
                    if response:
                        print(f"Arduino (finishing): {response}")
                        if "REQUEST" in response:
                            final_request_count += 1
                else:
                    # If no response, assume Arduino is done
                    time.sleep(0.5)
                    if not ser.in_waiting > 0:
                         break # Break if no activity

            print("✅ Robot should be finished. Closing port.")


    except serial.SerialException as e:
        print(f"\n❌ SERIAL ERROR: {e}")
        print("Please check the following:")
        print(f"  1. Is the Arduino plugged in?")
        print(f"  2. Is '{SERIAL_PORT}' the correct port? Check the Arduino IDE.")
        print(f"  3. Is another program (like the Arduino Serial Monitor) using the port?")
    except KeyboardInterrupt:
        print("\n🛑 Program stopped by user.")

'''take an svg file at /data/svg_files/svg_filename and generate a command file at /data/command_files/commands.txt'''
def generate_robot_command_from_svg(svg_filename, l1, l2, samples_per_segment=20):
    print(calculate_standardized_metrics(svg_filename))
    points = svg_to_simplified_points_list(svg_filename, samples_per_segment=samples_per_segment, arm_L1=l1, arm_L2=l2, margin=2)
    print(f"Generated {len(points)} points from SVG '{svg_filename}'.")
    name = f"output_{svg_filename}.txt"
    with open(BASE_DIR / "data" / "xy_file_storage" / name, 'w') as f:
        for point in points:
            f.write(f"{point}\n")
    
    
    command_list = generate_commands(points, l1, l2)
    generate_commands_file(command_list, svg_filename)

def generate_robot_command_from_xy(xy_filename, l1, l2):
    xy_file_path = BASE_DIR / "data" / "xy_files" / xy_filename
    points = []
    with open(xy_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line == "(None, None)":
                points.append((None, None))
            else:
                point = eval(line)
                points.append(point)
    print(f"Loaded {len(points)} points from XY file '{xy_filename}'. into command list.")
    command_list = generate_commands(points, l1, l2)
    generate_commands_file(command_list, xy_filename)

def move_file_into_cmd_files(src_path):
    shutil.move(src_path, BASE_DIR / "data" / "command_files" / src_path.name)

def visualize_xy_file():
    # 2. Read the points from the file
    points = read_points_file()
    # 3. Plot the data
    plot_xy_points(points, title=f"Visualization of XY Points from {next(XY_FILE_DIR.glob('*')).name}")


'''USER FUNCTIONS TO CALL
    visualize_xy_file()
    - reads the first xy file in /data/xy_files/ and visualizes it

    move_file_into_cmd_files(src_path)
    - moves a file at src_path into the /data/command_files/ directory
    
    generate_robot_command_from_xy(xy_filename, l1, l2)
    - expects an xy file in /data/xy_files/xy_filename
    - l1 and l2 are the lengths of the two arm segments
    - generates a command file at /data/command_file_storage/commands_xy_filename.txt
    
    generate_robot_command_from_svg(svg_filename, l1, l2)
    - expects an svg file in /data/svg_files/svg_filename
    - l1 and l2 are the lengths of the two arm segments
    - generates a command file at /data/command_file_storage/commands_svg_filename.txt
    - might error if the svg has points out of reach of the arm
    
    main()
    - connects to the Arduino and sends commands from the command file in /data/command_files/
    - WILL DO THE FIRST FILE IT FINDS IN THAT DIRECTORY
    - must be connected to arduino with matching serial settings
    - sends commands in batches upon request from the Arduino
'''
if __name__ == '__main__':
      SVG_FILES_DIR = BASE_DIR / "data" / "svg_files"
      for file in SVG_FILES_DIR.iterdir():
         print(f"Using command file: {file.name}")
         generate_robot_command_from_svg(file.name, l1=13, l2=12.5, samples_per_segment=5)
    
    # generate_robot_command_from_xy("2_dots_lmao.txt", l1=13, l2=12.5)
    # move_file_into_cmd_files(BASE_DIR / "data" / "command_file_storage" / "2_dots_lmao.txt.txt")
    #main()
    # visualize_xy_file()