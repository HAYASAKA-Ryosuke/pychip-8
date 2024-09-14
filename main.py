class CPU:
    def __init__(self, rom, display):
        # RAM全体が4KB
        self.ram = [0] * 0x200
        self.ram[0x200:0x200 + len(rom)] = rom
        self.ram.extend([0] * (4096 - len(self.ram)))
        self.display = display

        self.Vx_register = [0] * 16  # レジスタ(Vx)
        self.I_register = 0  # indexレジスタ(Iのこと)
        self.Vy_register = False  # Vyレジスタのこと
        self.pc = 0x200  # 0x200からスタート｡0x000~0x1FFはインタプリタ領域なので使用不可｡
        self.stack = [0] * 16  # スタックは16bitの配列
        self.sp = 0  # スタックポインタは8bit
        self.key = [0] * 16
        self.delay_timer = 0

    def cls(self):
        # display clear
        self.display.clear()
        pass

    def get_bytes(self):
        opcode = (self.ram[self.pc] << 8) | self.ram[self.pc + 1]
        return opcode

    def set_index_register(self, opcode):
        address = opcode & 0x0FFF
        self.I_register = address

    def execute_category_four(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        if self.Vx_register[X] != kk:
            self.pc += 2

    def execute_category_six(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.Vx_register[X] = kk

    def execute_category_seven(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.Vx_register[X] += kk

    def execute_category_eight(self, opcode):
        X = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.Vx_register[X] += kk

    def execute_category_f(self, opcode):
        X = (opcode & 0x0F00) >> 8
        match (opcode & 0x00FF):
            case 0x1E:
                # Vxレジスタの値をIレジスタに加算
                self.I_register += self.Vx_register[X]
            case 0x07:
                # ディレイタイマの値をVXにセット
                self.Vx_register[X] = self.delay_timer
            case 0x15:
                # VXの値をディレイタイマにセット
                self.delay_timer = self.Vx_register[X]

    def execute_category_d(self, opcode):
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4
        N = opcode & 0x000F
        collision = False
        x = X % self.display.col
        y = Y % self.display.row
        for row in range(N):
            sprites = self.ram[self.I_register + row]
            for col in range(8):
                sprite_pixel = (sprites >> (7 - col)) & 0x1
                screen_pixel = self.display.screen[y + row][(x + col) % self.display.col]
                new_pixel = screen_pixel ^ sprite_pixel

                if screen_pixel == 1 and new_pixel == 0:
                    collision = True
                self.display.screen[y + row][(x + col) % self.display.col] = new_pixel
        if collision:
            self.Vy_register = True

    def execute(self, opcode):
        category = (opcode & 0xF000) >> 12
        match category:
            case 0xA:
                self.set_index_register(opcode)
            case 0xF:
                self.execute_category_f(opcode)
            case 0x4:
                self.execute_category_four(opcode)
            case 0x6:
                self.execute_category_six(opcode)
            case 0x7:
                self.execute_category_seven(opcode)
            case 0x8:
                self.execute_category_eight(opcode)
            case 0xD:
                self.execute_category_d(opcode)
            case _:
                print(f"missing opcode: 0x{opcode:04X}")
                raise opcode

    def run(self):
        opcode = self.get_bytes()
        print(f"Fetched opcode: 0x{opcode:04X}")
        print(self.pc)
        self.execute(opcode)
        self.pc += 2


class MonoDisplay:
    # 64x32ピクセルのモノクロディスプレイ
    def __init__(self, col=64, row=32):
        self.col = col
        self.row = row
        self.spriate = {'0': [0xF0, 0x90, 0x90, 0x90, 0xF0]}
        self.screen = [[0 for i in range(row)] for j in range(col)]

    def clear(self):
        self.screen = [[0 for i in range(self.row)] for j in range(self.col)]


if __name__ == '__main__':
    with open('./test.ch8', 'rb') as f:
        rom = f.read()
    display = MonoDisplay()
    cpu = CPU(rom, display)
    for i in range(100):
        cpu.run()
