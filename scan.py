import asyncio
from bleak import BleakScanner

async def test_scan():
    print("Scanning for BLE devices... (5 seconds)")
    devices = await BleakScanner.discover()
    
    if not devices:
        print("No BLE devices found. Ensure Bluetooth is enabled and devices are advertising.")
        return
        
    for device in devices:
        print(f"Device: {device.name} | Address/UUID: {device.address}")

asyncio.run(test_scan())
