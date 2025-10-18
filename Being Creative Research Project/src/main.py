from svg_to_xy import *
from xy_to_angles_inverse_kinamatics import *
from command_generator import *
from pathlib import Path
import serial
import time

# --- Configuration ---
BASE_DIR = Path(__file__).parent.parent
# Make sure this path points correctly to your commands.txt file
COMMAND_FILE = BASE_DIR / "data" / "command_files" / "commands.txt" 
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
                                time.sleep(0.05) # Small delay between sends
                            else:
                                break # No more commands left
            
            print("\n🎉 All commands sent. The robot will now complete its final moves.")

    except serial.SerialException as e:
        print(f"\n❌ SERIAL ERROR: {e}")
        print("Please check the following:")
        print(f"  1. Is the Arduino plugged in?")
        print(f"  2. Is '{SERIAL_PORT}' the correct port? Check the Arduino IDE.")
        print(f"  3. Is another program (like the Arduino Serial Monitor) using the port?")
    except KeyboardInterrupt:
        print("\n🛑 Program stopped by user.")


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