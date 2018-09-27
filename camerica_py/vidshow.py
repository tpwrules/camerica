import pygame
import numpy as np
import sys
from vidfile import VidfileReader

palette = [(c, c, c) for c in range(256)]

def get_frame(i):
    
    return frame, histo

curr_frame = 10

disp = pygame.display.set_mode((320*2, 256*2))
frame_surf = None

clock = pygame.time.Clock()

frame_data = np.empty((256, 320), dtype=np.uint16)
histo_data = np.empty((256,), dtype=np.uint32)

frame_backing = np.empty((256, 320), dtype=np.uint8)

frame_surf = pygame.image.frombuffer(frame_backing, (320, 256), "P")
frame_surf.set_palette(palette)

vf = VidfileReader(sys.argv[1])

cf = 0

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
    if event.type == pygame.QUIT:
        break
        
    vf.next_frame(frame_data, histo_data)
    np.copyto(frame_backing, frame_data>>4)

    pygame.transform.scale(frame_surf.convert(disp), (320*2, 256*2), disp)

    pygame.display.flip()
    clock.tick(60)
    cf += 1
    if cf % 30 == 0:
        print(clock.get_fps())
    #print(clock.get_fps())