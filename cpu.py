import pygame
import random
from const import FONT_SPRIRITES, KEYMAP


class CPU:
    def __init__(self, rom, display, audio):
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
        self.key_input_state = None
        self.last_key_press_time = 0
        self.audio = audio

        self.clock = pygame.time.Clock()

    def set_key_input_state(self, value):
        if self.last_key_press_time > 2:
            self.key_input_state = value
            self.last_key_press_time = 0

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
        self.next_pc()

    def next_pc(self):
        # self.pc = (self.pc + 2) & 0x0FFF
        self.pc += 2
        self.last_key_press_time += 1
        if self.pc < 0x200 or self.pc >= 0x1000:
            raise Exception(f"pc error: {self.pc}")

    def execute_category_one(self, opcode):
        self.pc = opcode & 0x0FFF

    def execute_category_two(self, opcode):
        self.sp += 1
        self.stack[self.sp] = self.pc
        self.pc = opcode & 0x0FFF

    def execute_category_three(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        if self.V_register[X] == kk:
            self.next_pc()
        self.next_pc()

    def execute_category_four(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        if self.V_register[X] != kk:
            self.next_pc()
        self.next_pc()

    def execute_category_five(self, opcode):
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4
        if self.V_register[X] == self.V_register[Y]:
            self.next_pc()
        self.next_pc()

    def execute_category_six(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V_register[X] = kk
        self.next_pc()

    def execute_category_seven(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V_register[X] = (self.V_register[X] + kk) & 0xFF
        self.next_pc()

    def execute_category_eight(self, opcode):
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4
        match opcode & 0x000F:
            case 0:
                self.V_register[X] = self.V_register[Y]
            case 1:
                self.V_register[X] |= self.V_register[Y]
            case 2:
                self.V_register[X] &= self.V_register[Y]
            case 3:
                self.V_register[X] ^= self.V_register[Y]
            case 4:
                result = self.V_register[X] + self.V_register[Y]
                self.V_register[0xF] = 1 if result > 0xFF else 0
                self.V_register[X] = result & 0xFF  # 8bitにラップ
            case 5:
                self.V_register[0xF] = 1 if self.V_register[X] > self.V_register[Y] else 0
                self.V_register[X] = (self.V_register[X] - self.V_register[Y]) & 0xFF  # 8bitにラップ
            case 6:
                # Vxの最下位ビットをフラグレジスタにセット
                self.V_register[0xF] = self.V_register[X] & 0x1
                self.V_register[X] >>= 1
            case 7:
                self.V_register[0xF] = 1 if self.V_register[Y] > self.V_register[X] else 0
                self.V_register[X] = (self.V_register[Y] - self.V_register[X]) & 0xFF
            case 0xE:
                self.V_register[0xF] = (self.V_register[X] & 0x80) >> 7  # 最上位ビット7bitをVFにセット
                self.V_register[X] = (self.V_register[X] << 1) & 0xFF  # 8bitにラップ
        self.next_pc()

    def execute_category_nine(self, opcode):
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4
        if self.V_register[X] != self.V_register[Y]:
            self.next_pc()
        self.next_pc()

    def execute_category_a(self, opcode):
        self.I_register = opcode & 0x0FFF
        self.next_pc()

    def execute_category_b(self, opcode):
        self.pc = self.V_register[0] + opcode & 0x0FFF

    def execute_category_c(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V_register[X] = kk & random.randint(0, 255)
        self.next_pc()

    def execute_category_d(self, opcode):
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4
        N = opcode & 0x000F
        x = self.V_register[X] % self.display.width
        y = self.V_register[Y] % self.display.height
        self.V_register[0xF] = 0
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
        self.next_pc()

    def execute_category_e(self, opcode):
        X = (opcode & 0x0F00) >> 8
        NN = opcode & 0x00FF
        match NN:
            case 0x9E:
                if self.key_input_state == self.V_register[X]:
                    self.next_pc()
            case 0xA1:
                if self.key_input_state != self.V_register[X]:
                    self.next_pc()
        self.next_pc()

    def execute_category_f(self, opcode):
        X = (opcode & 0x0F00) >> 8
        match (opcode & 0x00FF):
            case 0x07:
                # ディレイタイマの値をVXにセット
                self.V_register[X] = self.delay_timer
                self.next_pc()
            case 0x0A:
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            self.set_key_input_state(KEYMAP.get(event.key))
                            self.V_register[X] = self.key_input_state
                            self.next_pc()
                            return
            case 0x15:
                # VXの値をディレイタイマにセット
                self.delay_timer = self.V_register[X]
                self.next_pc()
            case 0x18:
                # 音を鳴らす
                self.audio.play(False, 80, 0)
                self.next_pc()
            case 0x1E:
                # Vレジスタの値をIレジスタに加算
                self.I_register += self.V_register[X]
                self.next_pc()
            case 0x29:
                # Iレジスタにスプライトのアドレスをセット
                self.I_register = self.V_register[X] * 5
                self.next_pc()
            case 0x33:
                self.ram[self.I_register] = self.V_register[X] // 100
                self.ram[self.I_register + 1] = (self.V_register[X] // 10) % 10
                self.ram[self.I_register + 2] = self.V_register[X] % 10
                self.next_pc()
            case 0x55:
                for i, data in enumerate(self.V_register[:X + 1]):
                    self.ram[self.I_register + i] = data
                self.I_register += X + 1
                self.next_pc()
            case 0x65:
                for i, data in enumerate(self.ram[self.I_register: self.I_register + X + 1]):
                    self.V_register[i] = data
                self.I_register += X + 1
                self.next_pc()
            case _:
                print(f"missing opcode(f): 0x{opcode:04X}")
                raise opcode

    def execute(self, opcode):
        category = (opcode & 0xF000) >> 12
        match category:
            case 0x0:
                self.execute_category_zero(opcode)
            case 0x1:
                self.execute_category_one(opcode)
            case 0x2:
                self.execute_category_two(opcode)
            case 0x3:
                self.execute_category_three(opcode)
            case 0x4:
                self.execute_category_four(opcode)
            case 0x5:
                self.execute_category_five(opcode)
            case 0x6:
                self.execute_category_six(opcode)
            case 0x7:
                self.execute_category_seven(opcode)
            case 0x8:
                self.execute_category_eight(opcode)
            case 0x9:
                self.execute_category_nine(opcode)
            case 0xA:
                self.execute_category_a(opcode)
            case 0xB:
                self.execute_category_b(opcode)
            case 0xC:
                self.execute_category_c(opcode)
            case 0xD:
                self.execute_category_d(opcode)
            case 0xE:
                self.execute_category_e(opcode)
            case 0xF:
                self.execute_category_f(opcode)
            case _:
                print(f"missing opcode: 0x{opcode:04X}")
                raise opcode

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1

    def run(self):
        opcode = self.get_bytes()
        # print(f'opcode: 0x{opcode:04X}')
        # print(self.pc)
        self.execute(opcode)
        self.display.update()
        self.update_timers()
