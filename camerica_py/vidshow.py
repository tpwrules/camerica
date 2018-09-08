import pygame
import numpy as np
import sys

f = open(sys.argv[1], "rb")

palette = [(c, c, c) for c in range(256)]

frsize = (320*258*2)+(256*4)

def get_frame(i):
    f.seek(i*frsize)
    frame = np.frombuffer(f.read(320*258*2), dtype=np.uint16)
    frame.shape = (258, 320)

    histo = np.frombuffer(f.read(256*4), dtype=np.uint32)
    histo.shape = (256,)

    return frame, histo

curr_frame = 10

disp = pygame.display.set_mode((320*2, 258*2))
frame_surf = None

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                curr_frame -= 1
                if curr_frame < 0:
                    curr_frame = 0
            elif event.key == pygame.K_d:
                curr_frame += 1
                if curr_frame > 2360:
                    curr_frame = 2360

            print(curr_frame)
            frame_data, histo_data = get_frame(curr_frame)
            frame_data = (frame_data >> 4).astype(np.uint8)
            frame_surf = pygame.image.frombuffer(frame_data, (320, 258), "P")
            frame_surf.set_palette(palette)
            frame_surf = frame_surf.convert(disp)
    if event.type == pygame.QUIT:
        break

    if frame_surf is not None:
       pygame.transform.scale(frame_surf, (320*2, 258*2), disp)

    pygame.display.flip()
    clock.tick(60)