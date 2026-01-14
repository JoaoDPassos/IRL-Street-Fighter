import serial
import serial.tools.list_ports
import pyautogui
import time

# Automatically find Arduino port
def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Found port: {port.device} - {port.description}")
        if 'usbmodem' in port.device or 'USB' in port.description:
            return port.device
    return None

ARDUINO_PORT = find_arduino_port()
BAUD_RATE = 9600

if ARDUINO_PORT is None:
    print("No Arduino found. Available ports:")
    for port in serial.tools.list_ports.comports():
        print(f"  {port.device}")
    exit()

print(f"Connecting to Arduino on {ARDUINO_PORT}...")

try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    print('Connected to Arduino')
    time.sleep(2)  # Wait for connection to stabilize
    
    # Clear any initial data
    arduino.reset_input_buffer()
    
except Exception as e:
    print(f'Failed to connect to Arduino: {e}')
    exit()

print('Ready to receive keypresses...')

while True:
    try:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            print(f"Received: {line}")
            
            if 'Movement detected' in line:
                print('Sending key: a')
                pyautogui.press('a')
        
        time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nClosing connection...")
        arduino.close()
        break
