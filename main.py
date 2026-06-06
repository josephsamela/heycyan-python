import pygame
from config import *
import common
import heycyan

# SETUP
pygame.init()
pygame.font.init()
pygame.mixer.init()

# RESOLUTIONS
WINDOW_RES_WIDTH = pygame.display.Info().current_w
WINDOW_RES_HEIGHT = pygame.display.Info().current_h

SCALE_RES_WIDTH = WINDOW_RES_WIDTH
SCALE_RES_HEIGHT = SCALE_RES_WIDTH*(9/16)
SCALE_RES_HEIGHT_OFFSET = (WINDOW_RES_HEIGHT - SCALE_RES_HEIGHT)/2

window = pygame.display.set_mode((SCALE_RES_WIDTH,SCALE_RES_HEIGHT), vsync=True)
screen = pygame.Surface((RENDER_RES_WIDTH,RENDER_RES_HEIGHT)).convert()

# GAME LOOP VARIABLES
glass1 = heycyan.HeyCyan('E02_45E6', 'A937F620-1BA2-583F-51F1-D53418614922')
running = True
fullscreen = False
debug = False
clock = pygame.time.Clock()
img = None

title = common.Text('RISK VISION', common.Fonts.mono, 72, common.Colors.darkgray, (WINDOW_RES_WIDTH*0.5,WINDOW_RES_HEIGHT*0.1))
label = common.Text('Water Sensor', common.Fonts.mono, 36, common.Colors.darkgray, (WINDOW_RES_WIDTH*0.5,WINDOW_RES_HEIGHT*0.8))
battery = common.BatteryIcon(glass1, (40,20))
connect = common.ConnectIcon(glass1, (120,20))

pygame.display.set_caption(f'Water Sensor Demo')
debug_overlay = common.Text('', common.Fonts.mono, 24, common.Colors.white, (WINDOW_RES_WIDTH*0.5,WINDOW_RES_HEIGHT*0.1))

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
                                WINDOW_RES_WIDTH = int(pygame.display.Info().current_w/2)
                                WINDOW_RES_HEIGHT = int(WINDOW_RES_WIDTH*(9/16))
                                pygame.display.set_mode((WINDOW_RES_WIDTH,WINDOW_RES_HEIGHT), vsync=True)
                                fullscreen = False
                            case False:
                                # If windowed, make fullscreen
                                WINDOW_RES_WIDTH, WINDOW_RES_HEIGHT = pygame.display.get_desktop_sizes()[0]

                                SCALE_RES_WIDTH = WINDOW_RES_WIDTH
                                SCALE_RES_HEIGHT = SCALE_RES_WIDTH*(9/16)
                                SCALE_RES_HEIGHT_OFFSET = (WINDOW_RES_HEIGHT - SCALE_RES_HEIGHT)/2

                                window = pygame.display.set_mode((WINDOW_RES_WIDTH,WINDOW_RES_HEIGHT), pygame.FULLSCREEN, vsync=True)
                                fullscreen = True

                    case pygame.K_d:
                        if debug:
                            debug = False
                        else:
                            debug = True

    ################################################################################

    screen.fill(common.Colors.gray)
    title.draw(screen)
    label.draw(screen)
    connect.draw(screen)
    battery.draw(screen)

    if glass1.img_available:
        try:
            img = pygame.image.load(glass1.filename).convert()
            img = pygame.transform.smoothscale_by(img,3)
        except:
            pass
        glass1.img_available = False

    if img:
        screen.blit(img, img.get_rect(center = screen.get_rect().center))

    ################################################################################

    # Draw screen to window
    if screen.size == window.size:
        # If screen and window are the same size; blit straight to window
        window.blit(screen)
    elif (screen.width/screen.height) == (window.width/window.height):
        # If screen and window are different sizes, but have the same aspect ratio; scale
        pygame.transform.scale(screen, (WINDOW_RES_WIDTH,WINDOW_RES_HEIGHT), window)
    else:
        # If screen and window are different sizes and have different aspect ratios; scale screen and draw to window vertical center (letterbox)
        resized_screen = pygame.transform.scale(screen, (SCALE_RES_WIDTH,SCALE_RES_HEIGHT))
        window.blit(resized_screen, (0, SCALE_RES_HEIGHT_OFFSET))

    dt = clock.tick(TARGET_FRAMERATE)

    if debug:
        debug_overlay.origin = (WINDOW_RES_WIDTH*0.5, WINDOW_RES_HEIGHT*0.1)
        debug_overlay.update(f'WINDOW {WINDOW_RES_WIDTH}x{WINDOW_RES_HEIGHT} | RENDER {RENDER_RES_WIDTH}x{RENDER_RES_HEIGHT} | FRAMERATE {round(clock.get_fps(),1)} FPS')
        debug_overlay.draw(window)

    dt = clock.tick(60)
    pygame.display.update()

glass1.stop()
pygame.quit()