import pygame
import numpy
from cpu import CPU
from display import MonoDisplay
from const import KEYMAP


def generate_beep_sound(freq, duration, sampling_rate):
    arr_size = sampling_rate * duration * 2
    x = numpy.linspace(0, arr_size, arr_size)
    y = numpy.sin(2 * numpy.pi * freq / sampling_rate * x) * 10000
    y = y.astype(numpy.int16)
    return y.reshape(int(y.shape[0]/2), 2)


if __name__ == '__main__':
    with open('./chipquarium.ch8', 'rb') as f:
        rom = f.read()
    display = MonoDisplay()
    wave = generate_beep_sound(440, 1, 44100)
    pygame.mixer.init(frequency=44100, size=-16, channels=1)
    audio = pygame.sndarray.make_sound(numpy.array(wave * (2 ** 16 // 2 - 1), dtype=numpy.int16))
    cpu = CPU(rom, display, audio)
    display.update()
    fps = 60
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                cpu.set_key_input_state(KEYMAP.get(event.key))
            if event.type == pygame.KEYUP:
                cpu.set_key_input_state(None)
        cpu.run()
        cpu.clock.tick(fps)
