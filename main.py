import sys
import pygame
import random


FONT_SPRIRITES = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80   # F
]


class CPU:
    def __init__(self, rom, display):
        # RAM全体が4KB
        self.ram = [0] * 0x200
        for i in range(len(FONT_SPRIRITES)):
            self.ram[i] = FONT_SPRIRITES[i]
        self.ram[0x200:0x200 + len(rom)] = rom
        self.ram.extend([0] * (4096 - len(self.ram)))
        self.display = display

        self.V_register = [0] * 16  # レジスタ(V)
        self.I_register = 0  # indexレジスタ(Iのこと)
        self.pc = 0x200  # 0x200からスタート｡0x000~0x1FFはインタプリタ領域なので使用不可｡
        self.stack = [0] * 16  # スタックは16bitの配列
        self.sp = 0  # スタックポインタは8bit
        self.key = [0] * 16
        self.delay_timer = 0

    def get_bytes(self):
        opcode = (self.ram[self.pc] << 8) | self.ram[self.pc + 1]
        return opcode

    def set_index_register(self, opcode):
        address = opcode & 0x0FFF
        self.I_register = address

    def execute_category_zero(self, opcode):
        match opcode & 0x00FF:
            case 0xE0:
                self.display.clear()
            case 0xEE:
                self.pc = self.stack[self.sp]
                self.sp -= 1

    def execute_category_one(self, opcode):
        self.pc = opcode & 0x0FFF

    def execute_category_two(self, opcode):
        self.sp += 1
        self.stack[self.sp] = self.pc
        self.pc = opcode & 0x0FFF

    def execute_category_four(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        if self.V_register[X] != kk:
            self.pc += 2

    def execute_category_six(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V_register[X] = kk

    def execute_category_seven(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V_register[X] += kk

    def execute_category_eight(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V_register[X] += kk

    def execute_category_nine(self, opcode):
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4
        if self.V_register[X] != self.V_register[Y]:
            self.pc += 2

    def execute_category_f(self, opcode):
        X = (opcode & 0x0F00) >> 8
        match (opcode & 0x00FF):
            case 0x07:
                # ディレイタイマの値をVXにセット
                self.V_register[X] = self.delay_timer
            case 0x0A:
                # キー入力待ち
                pass
            case 0x15:
                # VXの値をディレイタイマにセット
                self.delay_timer = self.V_register[X]
            case 0x18:
                # 音を鳴らす
                pass
            case 0x1E:
                # Vレジスタの値をIレジスタに加算
                self.I_register += self.V_register[X]
            case 0x29:
                # Iレジスタにスプライトのアドレスをセット
                self.I_register = self.V_register[X] * 5
            case _:
                print(f"missing opcode: 0x{opcode:04X}")
                raise opcode

    def execute_category_c(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V_register[X] = kk & random.randint(0, 255)

    def execute_category_d(self, opcode):
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4
        N = opcode & 0x000F
        x = self.V_register[X] % self.display.width
        y = self.V_register[Y] % self.display.height
        for height in range(N):
            sprites = self.ram[self.I_register + height]
            for width in range(8):
                sprite_pixel = (sprites >> (7 - width)) & 0x1
                screen_x = (x + width) % self.display.width
                screen_y = (y + height) % self.display.height
                screen_pixel = self.display.pixels[screen_y][screen_x]
                new_pixel = screen_pixel ^ sprite_pixel
                if screen_pixel == 1 and new_pixel == 0:
                    self.V_register[0xF] = 1
                self.display.pixels[screen_y][screen_x] = new_pixel
        self.display.draw()

    def execute(self, opcode):
        category = (opcode & 0xF000) >> 12
        match category:
            case 0x0:
                self.execute_category_zero(opcode)
            case 0x1:
                self.execute_category_one(opcode)
            case 0x2:
                self.execute_category_two(opcode)
            case 0x4:
                self.execute_category_four(opcode)
            case 0x6:
                self.execute_category_six(opcode)
            case 0x7:
                self.execute_category_seven(opcode)
            case 0x8:
                self.execute_category_eight(opcode)
            case 0x9:
                self.execute_category_nine(opcode)
            case 0xA:
                self.set_index_register(opcode)
            case 0xC:
                self.execute_category_c(opcode)
            case 0xD:
                self.execute_category_d(opcode)
            case 0xF:
                self.execute_category_f(opcode)
            case _:
                print(f"missing opcode: 0x{opcode:04X}")
                raise opcode

    def run(self):
        opcode = self.get_bytes()
        self.execute(opcode)
        self.display.update()
        self.pc += 2


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


if __name__ == '__main__':
    with open('./test3.ch8', 'rb') as f:
        rom = f.read()
    display = MonoDisplay()
    cpu = CPU(rom, display)
    display.update()
    while True:
        cpu.run()
