from bleak import BleakClient
from .constants import *

import logging
logging.basicConfig(level=logging.INFO)

class HeyCyan:
    def __init__(self, device_address):
        self.client = BleakClient(device_address)
        
        # DEVICE VERSION INFO
        self.software_version = ''
        self.hardware_version = ''
        self.wifi_software_version = ''
        self.wifi_hardware_version = ''

        # DEVICE BATTERY INFO
        self.battery = 0
        self.power_source = ''

        # DEVICE BLE PHOTO PROPERTIES
        self.ble_photo = []
        self.ble_photo_current_page = 0
        self.ble_photo_total_pages = 0
        self.ble_photo_current_page_total_chunks = 5
        self.ble_photo_current_chunk = 0

    @property
    def ble_photo_transfer_progress(self):
        return self.ble_photo_current_page / self.ble_photo_total_pages

    async def _init(self):
        '''
        Setup new device by connecting over BLE. Once connected, subscribe to 
        DEVICE_NOTIFY_CHARACTERISTIC and get device power and version information.
        '''
        await self.connect()
        await self.subscribe()
        await self.get_power_info()
        await self.get_version_info()
        logging.info(f'Connected to {self.client.name} software {self.software_version} battery {self.battery}%')

    async def connect(self, retry=0):
        '''
        Connect to BLE device. Retry failed connect up to retry_attempts.
        '''
        logging.info(f'Connect to {self.client.address}...')
        while not self.client.is_connected:
            try:
                await self.client.connect()
                logging.info(f'Connected to {self.client.address}')
                return
            except:
                retry += 1
                logging.info(f'Connect Failed. Retry {retry}')
            if retry >= 5:
                raise Exception(f'Could not connect to {self.client.address} after {retry} failed connection attempts.')

    async def subscribe(self):
        '''
        Subscribe to device DEVICE_NOTIFY_CHARACTERISTIC. Any notification published 
        by device goes to the notification_router() where it is routed to the correct
        callback function based on the message id.
        '''
        await self.client.start_notify(DEVICE_NOTIFY_CHARACTERISTIC, self.notification_router)

    async def write(self, msg):
        '''
        Write msg to DEVICE_WRITE_CHARACTERISTIC. The response to any request written 
        to the device is published as a notification to the DEVICE_NOTIFY_CHARACTERISTIC
        '''
        await self.client.write_gatt_char(DEVICE_WRITE_CHARACTERISTIC, bytes(msg))

    async def notification_router(self, sender, msg):
        '''
        Recieve device notifications and route them to the correct callback function based on the message id.

        For purposes of this application there are three types of message ID we're interested in.

        MSG_ID    DESCRIPTION
        66        Response to MSG_GET_POWER_INFO.
        67        Response to MSG_GET_VERSION_INFO.
        115       Notification that device STATE changed.
        253       Response to BLE Photo transfer.
        'chunk'   Chunk of a multi-part message.
        '''
        msg = HeyCyanMessage(msg)

        logging.debug(f'{sender} {msg.msg}')

        match msg.id:
            
            case 66:
                # Response to MSG_GET_POWER_INFO
                await self.update_power_info(
                    battery=msg.header[6],
                    source=msg.header[7]
                )
            case 67:
                # Response to MSG_GET_VERSION_INFO
                await self.update_version_info(msg)
            
            case 115:
                # Device STATE has changed
                match msg.action:

                    case 2:
                        # Recording has started.
                        # This application only wants users to take BLE photos. If user triggers another device function
                        # such as recording video, recording audio, or AI voice mode; send message to stop that function
                        # and take a BLE photo instead.
                        await self.write(MSG_VOICE_MODE_STOP)
                        await self.write(MSG_RECORD_VIDEO_STOP)
                        await self.write(MSG_RECORD_AUDIO_STOP)
                        await self.get_photo_ble()
                    case 3:
                        # Device power update
                        await self.update_power_info(
                            battery=msg.header[7],
                            source=msg.header[8]
                        )
                    case 5:
                        # BLE Photo was taken.
                        # If BLE photo was taken, reset photo buffer and start data transfer by requesting
                        # the first (ie. Zeroth) page of data. Subsequent pages are called after first is received.
                        self.ble_photo = []
                        await self.ble_photo_req_page(page=0)

            case 253: 
                # First chunk of new BLE Photo page is received.
                if msg.header[3] == 0:
                    # If this is the final page, photo transfer is done, save photo.
                    await self.ble_photo_save()
                else:
                    # If there are more pages, keep requesting data.
                    await self.ble_photo_data(msg)

            case 'chunk':
                # Chunk of BLE Photo data page was received.
                await self.ble_photo_data(msg)

    async def update_version_info(self, msg):   
        '''
        Handle device response to MSG_GET_VERSION_INFO.
        Device version info returned as ascii text without delimeters between fields.
        '''     
        s = bytes(msg.payload).decode()
        self.software_version = s[11:25]        # ie. 3.20.05_251014
        self.hardware_version = s[25:36]        # ie. A02E02_V3.2
        self.wifi_software_version = s[47:65]   # ie. 1.00.26_2511141030
        self.wifi_hardware_version = s[65:89]   # ie. WIFIA02E02_V3.2

    async def update_power_info(self, battery, source):
        '''
        Handle device response to MSG_GET_POWER_INFO or regular power state notification.
        Device sends regular notifications when power state changes. For example, when the 
        device is connected or disconnected from power or when battery percentage has changed.
        '''         
        self.battery = battery
        if source:
            self.power_source = 'power'
        else:
            self.power_source = 'battery'

    async def get_version_info(self):
        '''
        Send MSG_GET_VERSION_INFO to request device version info.
        '''
        await self.write(MSG_GET_VERSION_INFO)

    async def get_power_info(self):
        '''
        Send MSG_GET_POWER_INFO to request current device power info.
        '''
        await self.write(MSG_GET_POWER_INFO)

    async def get_photo_ble(self):
        '''
        Send MSG_TAKE_PHOTO_BLE to take BLE Photo
        '''
        await self.write(MSG_TAKE_PHOTO_BLE)

    async def ble_photo_req_page(self, page):
        '''
        Request page of BLE Photo data.

        Device transfers photos over BLE as JFIF Images at 384 x 288 resolution. Image data transfer is paginated. 
        Each page is recieved in multiple notification messages (ie. chunks). Start by requesting the first page. 
        Receive all chunks of that page. Then request the next page, and so on. For example:

        CLIENT REQUEST                   DEVICE NOTIFY

        MSG_TRANSFER_PHOTO_BLE_PAGE_0 ->
                                      <- BLE_PHOTO_PAGE_0_CHUNK_0
                                      <- BLE_PHOTO_PAGE_0_CHUNK_1
                                      <- BLE_PHOTO_PAGE_0_CHUNK_2
                                      <- BLE_PHOTO_PAGE_0_CHUNK_3
                                      <- BLE_PHOTO_PAGE_0_CHUNK_4
                                      <- BLE_PHOTO_PAGE_0_CHUNK_5
        MSG_TRANSFER_PHOTO_BLE_PAGE_1 ->
                                      <- BLE_PHOTO_PAGE_1_CHUNK_0
                                      <- BLE_PHOTO_PAGE_2_CHUNK_1
                                      <- BLE_PHOTO_PAGE_3_CHUNK_2
                                      <- BLE_PHOTO_PAGE_4_CHUNK_3
                                      <- BLE_PHOTO_PAGE_5_CHUNK_4
                                      <- BLE_PHOTO_PAGE_6_CHUNK_5
        ...

        Continue until all photo data is received.
        '''
        if page >= len(MSG_TRANSFER_PHOTO_BLE_PAGES):
            # If image filesize is large and requires more pages then 
            # there are page request commands for, save incomplete image.
            await self.ble_photo_save()
        else:    
            await self.write(MSG_TRANSFER_PHOTO_BLE_PAGES[page])

    async def ble_photo_data(self, msg):
        '''
        Handle received BLE Photo data. BLE Photo data is received in multiple PAGES. Each PAGE 
        is split across multiple CHUNKS. Only the first CHUNK of each PAGE contains a header.
        The header indicates the current page number and the total number of pages.

        When the last chunk of a page is received, request the next page.
        '''
        # If message contains a header, then it's the start of a new page.
        # Reset fields used to track current page and chunk.
        if msg.header:
            self.ble_photo_total_pages = msg.header[7]
            self.ble_photo_current_page = msg.header[9]
            self.ble_photo_current_chunk = 0

            if msg.header[2] == 250:
                self.ble_photo_current_page_total_chunks = 6
            else:
                self.ble_photo_current_page_total_chunks = 0

        # Add chunk of photo data to BLE Photo
        self.ble_photo.append(msg.payload)

        # Increment current page-chunk counter
        self.ble_photo_current_chunk += 1

        # If this is the final chunk of a page, request the next page
        if self.ble_photo_current_chunk >= self.ble_photo_current_page_total_chunks:
            await self.ble_photo_req_page(self.ble_photo_current_page+1)

    async def ble_photo_save(self):
        '''
        Save BLE photo data to file. BLE photos are JFIF format.
        Only call this after entire image data was received.
        '''
        img=[]
        for chunk in self.ble_photo:
            img.extend(chunk)
        with open("image.jpg", "wb") as f:
            f.write(bytes(img))

class HeyCyanMessage:
    def __init__(self, msg):
        self.msg = list(msg)
        match self.msg[0]:
            case 188:
                self.header = self.msg[0:11]
                self.payload = self.msg[11:]
                self.id = self.header[1]
                self.action = self.header[2]
            case _:
                self.header = []
                self.payload = self.msg
                self.id = 'chunk'
                self.action = None

async def device(device_id):
    glass = HeyCyan(device_id)
    await glass._init()
    return glass
