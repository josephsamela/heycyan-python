import asyncio
import threading
import os
import time
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

import logging
logging.basicConfig(level=logging.INFO)

from .constants import *

class HeyCyan:
    def __init__(self, device_name, device_address):
        self.device_name = device_name
        self.device_address = device_address
        self.client = None

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
        self.ble_photo_current_page_total_chunks = 6
        self.ble_photo_current_chunk = 0
        self.ble_page_transfer_in_progress = False
        self.filename = None
        self.img_available = False

        # DEVICE BACKGROUND THREAD
        self._loop = asyncio.new_event_loop()
        self._running = True
        self._thread = threading.Thread(target=self.start)
        self._thread.start()

    @property
    def connected(self):
        if self.client and self.client.is_connected:
            return True
        else:
            return False

    def start(self):
        '''
        Device setup. Run ._init() to connect device then keep event loop running.
        '''
        asyncio.run_coroutine_threadsafe(self._init(), self._loop)
        self._loop.run_forever()

    def stop(self):
        '''
        Device teardown. Gracefully disconnect from device and stop the event loop.
        '''
        # Signal thread to stop
        self._running = False

        # Disconnect from device
        if self.client and self.client.is_connected:
            future = asyncio.run_coroutine_threadsafe(self.client.disconnect(), self._loop)
            future.result()

        # Cancel all tasks in the event loop
        tasks = [t for t in asyncio.all_tasks(self._loop)]            
        if not tasks:
            for task in tasks:
                task.cancel()

        # Then stop the event loop
        self._loop.stop()

    async def _init(self):
        '''
        Setup new device by connecting over BLE. Once connected, subscribe to 
        DEVICE_NOTIFY_CHARACTERISTIC and get device power and version information.
        '''
        attempt=1
        while not self.client or not self.client.is_connected:

            if not self._running:
                return

            try:
                logging.info(f'Connecting to {self.device_name}...')
                await self.connect()
                await self.subscribe()
                await self.get_power_info()
                await self.get_version_info()
                logging.info(f'Connected to {self.device_name} software {self.software_version} battery {self.battery}%')
            except Exception as e:
                logging.info(f'Failed to connect to {self.device_name}. Attempt {attempt} {e}')
                attempt+=1

    async def connect(self):
        '''
        Connect to BLE device. Retry failed connect up to retry_attempts.
        '''
        self.client = await establish_connection(
            BleakClientWithServiceCache,
            device=self.device_address,
            name=self.device_name,
            max_attempts=3,
            disconnected_callback=self.disconnect
        )

    def disconnect(self, client):
        '''
        Callback when device disconnect. On disconnect call self._init() to reconnect the device.
        '''
        logging.info(f'Device {self.device_name} disconnected')
        asyncio.run_coroutine_threadsafe(
            coro=self._init(),
            loop=asyncio.get_running_loop()
        )

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
        For purposes of this application there are only a few types of message ID we're interested in.

        MSG_ID    DESCRIPTION
        66        Response to MSG_GET_POWER_INFO.
        67        Response to MSG_GET_VERSION_INFO.
        115       Notification that device STATE changed.
        253       Response to BLE Photo transfer.
        'chunk'   Chunk of a multi-part message.
        '''
        msg = HeyCyanMessage(msg)
        logging.debug(f'{sender} {msg.msg}')

        # If a BLE page transfer is in-progress save the photo data.
        if self.ble_page_transfer_in_progress:
            await self.ble_photo_data(msg.msg)
            return

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

            case 65:

                if msg.header[4] in [220, 189]:
                    await self.write(MSG_RECORD_AUDIO_STOP)
                    await self.get_photo_ble()
            
            case 115:
                # Device STATE has changed
                match msg.action:

                    case 2:
                        # Recording has started.
                        # This application only wants users to take BLE photos. If user triggers another device function
                        # such as recording video, recording audio, or AI voice mode; send message to stop that function
                        # and take a BLE photo instead.
                        match msg.header[6]:
                            case 3:
                                await self.write(MSG_VOICE_MODE_STOP)                        
                            case 11:
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
                        logging.info(f'{self.device_name} took a BLE Photo')

                        self.ble_photo = []
                        self.ble_photo_current_page = 0
                        self.ble_photo_total_pages = 0
                        self.ble_photo_current_page_total_chunks = 6
                        self.ble_photo_current_chunk = 0
                        self.filename = f'{time.time()}.jpg'

                        await self.ble_photo_req_page(page=0)

            case 253:
                # First chunk of new BLE Photo page is received.
                await self.ble_photo_page_start(msg)

            case _:
                # Log unrouted messages
                logging.info(f'{msg.header} {msg.payload}')

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
        logging.info(f'{self.device_name} Requesting BLE Photo page {page} / {self.ble_photo_total_pages}')
        if page >= len(MSG_TRANSFER_PHOTO_BLE_PAGES):
            # If image filesize is large and requires more pages then 
            # there are page request commands for, save incomplete image.
            await self.ble_photo_save()
        else:
            await self.write(MSG_TRANSFER_PHOTO_BLE_PAGES[page])

    async def ble_photo_page_start(self, msg):
        '''
        Handle start of new BLE Photo data page. BLE Photo data is received in multiple PAGES. 
        Each PAGE is split across multiple CHUNKS. Only the first CHUNK of each PAGE contains 
        a header. The header indicates the current page number and the total number of pages.
        '''
        self.ble_photo_total_pages = msg.header[7]-1
        self.ble_photo_current_page = msg.header[9]
        self.ble_photo_current_chunk = 0
        self.ble_page_transfer_in_progress = True

        if msg.header[2] == 250:
            self.ble_photo_current_page_total_chunks = 6

        # Process photo data
        await self.ble_photo_data(msg.payload)

    async def ble_photo_data(self, data):
        '''
        Handle received BLE Photo data.
        '''
        # Add chunk of photo data to BLE Photo
        self.ble_photo.extend(data)

        # Save photo
        self.img_available = True

        # Increment current chunk
        self.ble_photo_current_chunk += 1

        # If this is the last page and JPG is complete with EOI marker; transfer is complete
        if self.ble_photo_current_page >= self.ble_photo_total_pages and self.ble_photo[-2:] == [255,217]:
            self.ble_page_transfer_in_progress = False
            await self.ble_photo_save()
            return

        # If this is the final chunk of the current page, request the next page
        if self.ble_photo_current_chunk >= self.ble_photo_current_page_total_chunks:
            self.ble_page_transfer_in_progress = False
            await self.ble_photo_req_page(self.ble_photo_current_page+1)

    async def ble_photo_save(self):
        '''
        Save BLE photo data to file. BLE photos are JFIF format.
        Only call this after entire image data was received.
        '''
        try:
            with open(self.filename, "wb") as f:
                f.write(bytes(self.ble_photo))
            logging.info(f'Saved {self.device_name} BLE Photo to {self.filename}')
        except PermissionError as e:
            logging.error(f'Could not save {self.filename} {e}')

class HeyCyanMessage:
    def __init__(self, msg):
        self.msg = list(msg)
        if self.msg[0] == 188:
                self.header = self.msg[0:11]
                self.payload = self.msg[11:]
                self.id = self.header[1]
                self.action = self.header[2]
