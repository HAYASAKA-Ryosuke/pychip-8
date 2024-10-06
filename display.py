import sys
import pygame
from const import FONT_SPRIRITES


class MonoDisplay:

    SCALE = 10

    # 64x32ピクセルのモノクロディスプレイ
    def __init__(self, width=64, height=32):
        pygame.init()
        self.width = width
        self.height = height
        self.pixels = [[0 for x in range(self.width)] for y in range(self.height)]
        self.original_screen = pygame.Surface((self.width, self.height))
        self.display_screen = pygame.display.set_mode((self.width * self.SCALE, self.height * self.SCALE))
        self.pixel_array = pygame.surfarray.pixels3d(self.original_screen)

    def clear(self):
        self.pixels = [[0 for i in range(self.width)] for j in range(self.height)]

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        scaled_surface = pygame.transform.scale(self.original_screen, (self.width * self.SCALE, self.height * self.SCALE))
        self.display_screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()

    def draw(self):
        for y in range(len(self.pixels)):
            for x in range(len(self.pixels[y])):
                if self.pixels[y][x] == 1:
                    self.original_screen.set_at((x, y), (255, 255, 255))
                else:
                    self.original_screen.set_at((x, y), (0, 0, 0))

    def debug(self):
        for y in range(len(FONT_SPRIRITES)):
            byte = FONT_SPRIRITES[y]
            for x in range(8):
                if (byte >> (7 - x)) & 0x1:
                    self.original_screen.set_at((x, y), (255, 255, 255))

