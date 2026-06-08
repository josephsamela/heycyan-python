import pygame
from config import *

class Text:
    def __init__(self, text, font, size, color, origin):

        # Set object properties
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.origin = origin

        # Font size at 1080. This size is scaled relative to window
        relative_font_size = round(WINDOW_RES_HEIGHT*(size/1080))
        self.f = pygame.font.Font(font, relative_font_size)

        self.update(text)

    def update(self, text):
        # Render text to surface
        self.t = self.f.render(text, True, self.color)

    def draw(self, screen):
        # Actually draw text to screen
        screen.blit(self.t, self.t.get_rect(center=self.origin))

class BatteryIcon:
    def __init__(self, device, pos):
        self.device = device
        self.pos = pos
        size = (60,60)
        self.battery0 = pygame.image.load_sized_svg('assets/icons/battery0.svg', size).convert_alpha()
        self.battery10 = pygame.image.load_sized_svg('assets/icons/battery10.svg', size).convert_alpha()
        self.battery20 = pygame.image.load_sized_svg('assets/icons/battery20.svg', size).convert_alpha()
        self.battery40 = pygame.image.load_sized_svg('assets/icons/battery40.svg', size).convert_alpha()
        self.battery60 = pygame.image.load_sized_svg('assets/icons/battery60.svg', size).convert_alpha()
        self.battery80 = pygame.image.load_sized_svg('assets/icons/battery80.svg', size).convert_alpha()
        self.battery100 = pygame.image.load_sized_svg('assets/icons/battery100.svg', size).convert_alpha()
        self.batteryCharging = pygame.image.load_sized_svg('assets/icons/batteryCharging.svg', size).convert_alpha()

    def draw(self, screen):
        icon = self.battery0
        if self.device.power_source == 'power':
            icon = self.batteryCharging
        elif self.device.power_source == 'battery':
            l = self.device.battery
            if l == 100:
                icon = self.battery100
            elif 70 <= l < 99:
                icon = self.battery80
            elif 50 <= l < 70:
                icon = self.battery60
            elif 30 <= l < 50:
                icon = self.battery40
            elif 10 <= l < 30:
                icon = self.battery20
            elif 0 <= l < 10:
                icon = self.battery10
        screen.blit(icon, self.pos)

class ConnectIcon:
    def __init__(self, device, pos):
        self.device = device
        self.pos = pos
        size = (60,60)
        self.deviceConnected = pygame.image.load_sized_svg('assets/icons/deviceConnected.svg', size).convert_alpha()
        self.deviceDisonnected = pygame.image.load_sized_svg('assets/icons/deviceDisconnected.svg', size).convert_alpha()

    def draw(self, screen):
        if self.device.client and self.device.client.is_connected:
            icon = self.deviceConnected
        else:
            icon = self.deviceDisonnected
        screen.blit(icon, self.pos)

class Colors:
    white = '#ffffff'
    gray = '#B5B9C4'
    darkgray = '#383D3B'
    black = '#000000'
    red = '#DE2931'
    green = '#119465'
    blue = '#0351A9'

class Fonts:
    serif = 'assets/fonts/serif.ttf'
    sans = 'assets/fonts/sans.ttf'
    mono = 'assets/fonts/mono.ttf'
