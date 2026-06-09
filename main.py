import pygame
from config import *
import common
import heycyan
import io
import time
from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np

# SETUP
pygame.init()
pygame.font.init()
pygame.mixer.init()

# RESOLUTIONS
screen = pygame.display.set_mode(RENDER_RES, vsync=True)
pygame.display.set_caption(f'Water Sensor Demo')

# DEVICES
# glass1 = heycyan.HeyCyan('E02_45E6', 'A937F620-1BA2-583F-51F1-D53418614922')
glass1 = heycyan.HeyCyan('E02_45E6', '05:9D:08:41:45:E6')

# AI MODEL
model = load_model("assets/model/keras_model.h5", compile=False)
img_data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
class_names = open("assets/model/labels.txt", "r").readlines()

# GAME LOOP VARIABLES
running = True
fullscreen = False
debug = False
clock = pygame.time.Clock()
img = None
redraw = True
device_connect_state = None
device_battery_state = None
device_power_state = None
next_update = time.time()


title = common.Text('RISK VISION - Demo #1', common.Fonts.mono, 56, common.Colors.darkgray, (350, 60))
label = common.Text('Take photo to begin', common.Fonts.mono, 36, common.Colors.darkgray, (WINDOW_RES_WIDTH*0.5,WINDOW_RES_HEIGHT*0.95))
battery = common.BatteryIcon(glass1, (1830,20))
connect = common.ConnectIcon(glass1, (1750,20))

while running:
    for event in pygame.event.get():
        match event.type:

            # Window control
            case pygame.QUIT:
                running = False

            # Keyboard input
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        running = False

                    case pygame.K_f:
                        match fullscreen:
                            case True:
                                # If fullscreen, make windowed
                                pygame.display.set_mode(RENDER_RES, vsync=True)
                                fullscreen = False
                            case False:
                                # If windowed, make fullscreen
                                window = pygame.display.set_mode(RENDER_RES, pygame.FULLSCREEN, vsync=True)
                                fullscreen = True

                    case pygame.K_d:
                        if debug:
                            debug = False
                        else:
                            debug = True

    ################################################################################

    if redraw:
        screen.fill(common.Colors.gray)
        title.draw(screen)
        label.draw(screen)
        connect.draw(screen)
        battery.draw(screen)

        if img:
            screen.blit(img, img.get_rect(center = screen.get_rect().center))
        redraw = False


    if glass1.client and glass1.client.is_connected != device_connect_state:
        device_connect_state = glass1.client.is_connected
        redraw = True

    if glass1.battery and glass1.battery != device_battery_state:
        device_battery_state = glass1.battery
        redraw = True

    if glass1.power_source and glass1.power_source != device_power_state:
        device_power_state = glass1.power_source
        redraw = True

    if glass1.img_available or time.time() > next_update:

        
        try:
            ble_photo = io.BytesIO(bytes(glass1.ble_photo))
            img = pygame.image.load(ble_photo).convert()
            img = pygame.transform.smoothscale_by(img,3)
        except pygame.error:
            pass

        try:
            ble_photo = io.BytesIO(bytes(glass1.ble_photo))
            image = Image.open(ble_photo).convert("RGB")
            image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
            image_array = np.asarray(image)
            normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
            img_data[0] = normalized_image_array

            # Predicts the model
            prediction = model.predict(img_data)
            index = np.argmax(prediction)
            class_name = class_names[index]
            confidence_score = prediction[0][index]
            object_label = class_name[2:].strip()
            label.update(object_label)
        except:
            pass

        glass1.img_available = False
        redraw = True

        next_update = time.time() + 1

    ################################################################################

    dt = clock.tick(TARGET_FRAMERATE)
    pygame.display.update()

glass1.stop()
pygame.quit()
