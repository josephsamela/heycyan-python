'''
HeyCyan Device BLE Constants

The HeyCyan app communicates with the Smart Glasses over Bluetooth Low Energy (BLE).
The Smart Glasses have many BLE characteristics, but only two are used by the HeyCyan app.

The DEVICE_NOTIFY_CHARACTERISTIC is a publish-subscribe type communication.
After connecting, your app must subscribe to the DEVICE_NOTIFY_CHARACTERISTIC.
All communication FROM the smart glasses are sent as notifications from this characteristic.

The DEVICE_WRITE_CHARACTERISTIC is a request-response type communication.
After you are subscribed to DEVICE_NOTIFY_CHARACTERISTIC, you can write commands to this characteristic.
Requests sent to this characteristic are received as notifications from DEVICE_NOTIFY_CHARACTERISTIC.

---------------------------

The following messages were captured using iOS PacketLogger.

HARDWARE:
    iPhone 13 Pro
    M1 MacBook Air (2020)
    Lightning to USB-C cable
    HeyCyan SmartGlasses A02E02_V3.2

SOFTWARE:
    MacOS Tahoe 26.6
    iOS 26.6
    PackeLogger 26.0.0
    HeyCyan App 1.3.1(11)
    SmartGlasses running 3.20.05_251014

'''
# BLE Device Characteristics
DEVICE_WRITE_CHARACTERISTIC  = 'de5bf72a-d711-4e47-af26-65e3012a5dc7'
DEVICE_NOTIFY_CHARACTERISTIC = 'de5bf729-d711-4e47-af26-65e3012a5dc7'

# BLE Commands
MSG_GET_POWER_INFO     = [188, 66, 1, 0, 126, 128, 1]
MSG_GET_VERSION_INFO   = [188, 67, 1, 0, 126, 128, 1]
MSG_RECORD_AUDIO_START = [188, 65, 3, 0, 208, 86 , 2, 1, 8]
MSG_RECORD_AUDIO_STOP  = [188, 65, 3, 0, 209, 149, 2, 1, 12]
MSG_RECORD_VIDEO_START = [188, 65, 3, 0, 80 , 81 , 2, 1, 2]
MSG_RECORD_VIDEO_STOP  = [188, 65, 3, 0, 145, 145, 2, 1, 3]
MSG_VOICE_MODE_STOP    = [188, 65, 4, 0, 150, 172, 2, 1, 11, 1]
MSG_TAKE_PHOTO_BLE     = [188, 65, 5, 0, 60 , 156, 2, 1, 6 , 2, 2]

# BLE Photo Transfer Commands
MSG_TRANSFER_PHOTO_BLE_PAGES = [
    [188, 253, 5, 0, 25, 192, 1, 0 , 0, 0 , 0], # PAGE 0
    [188, 253, 5, 0, 25, 172, 1, 1 , 0, 1 , 0], # PAGE 1
    [188, 253, 5, 0, 25, 24 , 1, 2 , 0, 2 , 0], # PAGE 2
    [188, 253, 5, 0, 25, 116, 1, 3 , 0, 3 , 0], # PAGE 3
    [188, 253, 5, 0, 26, 48 , 1, 4 , 0, 4 , 0], # PAGE 4
    [188, 253, 5, 0, 26, 92 , 1, 5 , 0, 5 , 0], # PAGE 5
    [188, 253, 5, 0, 26, 232, 1, 6 , 0, 6 , 0], # PAGE 6
    [188, 253, 5, 0, 26, 132, 1, 7 , 0, 7 , 0], # PAGE 7
    [188, 253, 5, 0, 28, 96 , 1, 8 , 0, 8 , 0], # PAGE 8
    [188, 253, 5, 0, 28, 12 , 1, 9 , 0, 9 , 0], # PAGE 9
    [188, 253, 5, 0, 28, 184, 1, 10, 0, 10, 0], # PAGE 10
    [188, 253, 5, 0, 28, 212, 1, 11, 0, 11, 0], # PAGE 11
    [188, 253, 5, 0, 31, 144, 1, 12, 0, 12, 0], # PAGE 12
    [188, 253, 5, 0, 31, 252, 1, 13, 0, 13, 0], # PAGE 13
    [188, 253, 5, 0, 31, 72 , 1, 14, 0, 14, 0], # PAGE 14
    [188, 253, 5, 0, 31, 36 , 1, 15, 0, 15, 0], # PAGE 15
    [188, 253, 5, 0, 16, 192, 1, 16, 0, 16, 0], # PAGE 16
    [188, 253, 5, 0, 16, 172, 1, 17, 0, 17, 0], # PAGE 17
    [188, 253, 5, 0, 16, 24 , 1, 18, 0, 18, 0], # PAGE 18
    [188, 253, 5, 0, 16, 116, 1, 19, 0, 19, 0], # PAGE 19
    [188, 253, 5, 0, 19, 48 , 1, 20, 0, 20, 0], # PAGE 20
    [188, 253, 5, 0, 19, 92 , 1, 21, 0, 21, 0], # PAGE 21
    [188, 253, 5, 0, 19, 232, 1, 22, 0, 22, 0], # PAGE 22
    [188, 253, 5, 0, 19, 132, 1, 23, 0, 23, 0], # PAGE 23
    [188, 253, 5, 0, 21, 96 , 1, 24, 0, 24, 0], # PAGE 24
    [188, 253, 5, 0, 21, 12 , 1, 25, 0, 25, 0], # PAGE 25
    [188, 253, 5, 0, 21, 184, 1, 26, 0, 26, 0]  # PAGE 26
]
