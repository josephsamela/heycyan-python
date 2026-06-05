import pygame
import heycyan

def main():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((500,500), vsync=True)
    clock = pygame.time.Clock()
    running = True

    glass1 = heycyan.HeyCyan('E02_45E6', 'A937F620-1BA2-583F-51F1-D53418614922')

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if glass1.connected:
            screen.fill("green")
        else:
            screen.fill("red")

        # flip() the display to put your work on screen
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60


    glass1.stop()

    pygame.quit()



if __name__ == "__main__":
    main()