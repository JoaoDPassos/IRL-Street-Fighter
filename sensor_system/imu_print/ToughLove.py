import asyncio
from bleak import BleakScanner, BleakClient
import pyautogui

# Nordic UART Service UUIDs
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

TARGET_DEVICES = ["Left Hand", "Right Hand", "Leg"]  # Add your device names

def create_notification_handler(device_name):
    "Create a notification handler for each device"
    def notification_handler(sender, data):
        message = data.decode('utf-8').strip()
        # print(f"[{device_name}] Received: {message}")
        
        if 'Movement:PunchL' in message:
            # print(f'[{device_name}] Sending key: a')
            # print('Sending key: a')
            pyautogui.press('j')
        elif 'Movement:Left_Down' in message:
            print(f'[{device_name}] Action: Holding')
            pyautogui.keyDown('A')
        elif 'Movement:Left_Up' in message:
            print(f'[{device_name}] Action: Releasing Left Arrow')
            pyautogui.keyUp('A')
        elif 'Movement:PunchR' in message:
            print(f'[{device_name}] Sending key: s')
            pyautogui.press('k')
        elif 'Movement:Right_Down' in message:
            print(f'[{device_name}] Action: Holding Right Arrow')
            pyautogui.keyDown('D')
        elif 'Movement:Right_Up' in message:
            print(f'[{device_name}] Action: Releasing Right Arrow')
            pyautogui.keyUp('D')
        elif 'Movement:StompR' in message:
            print(f'[{device_name}] Action: Stomp')
            pyautogui.press('L')
        elif 'Movement:KickR' in message:
            print(f'[{device_name}] ActionlLLLLLLL;LLLLL Kick')
            pyautogui.press(';')
    return notification_handler
async def connect_to_device(device_address, device_name):
    """Connect to a single device and listen for notifications"""
    try:
        print(f"Connecting to {device_name} at {device_address}...")
        
        async with BleakClient(device_address) as client:
            print(f"[{device_name}] Connected!")
            
            # Subscribe to notifications
            await client.start_notify(UART_TX_CHAR_UUID, create_notification_handler(device_name))
            
            print(f"[{device_name}] Listening for movement data...")
            
            # Keep connection alive
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print(f"\n[{device_name}] Disconnecting...")
                await client.stop_notify(UART_TX_CHAR_UUID)
    
    except Exception as e:
        print(f"[{device_name}] Error: {e}")


async def main():
    print("Scanning for Device...")
    
    # Scan for  devices
    devices = await BleakScanner.discover()
    found_devices = {}
    
    for device in devices:
        if device.name:
            print(f"Found: {device.name} - {device.address}")

        if device.name in TARGET_DEVICES:
            found_devices[device.name] = device.address
    
    if not found_devices:
        print("No target devices found!")
        return
    
    print(f"Found {len(found_devices)} target device(s)")
    
    # Create connection tasks for all devices
    tasks = []
    for device_name, device_address in found_devices.items():
        task = connect_to_device(device_address, device_name)
        tasks.append(task)

    # Run all connections concurrently
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nShutting down all connections...")

# Run the async main function
asyncio.run(main())
