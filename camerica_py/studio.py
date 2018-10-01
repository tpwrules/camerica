import sys
import pygame
import numpy as np

import vidhandler

# launch the display and pygame stuff
disp = pygame.display.set_mode((320*2, 256*2+72))
clock = pygame.time.Clock()

# construct buffers for the current displayed frame, to be written
# by the handler
framebuf_handler = np.empty((256, 320), dtype=np.uint16)
histobuf_handler = np.empty((1, 256), dtype=np.uint32)
# and then ones for the frame we are working on displaying
framebuf = np.empty((256*2, 320*2), dtype=np.uint8)
histobuf = np.empty((1, 256), dtype=np.uint32)

histo_levels = np.empty((1, 64), dtype=np.uint32)
histo_pix = np.empty((64, 256), dtype=np.uint8)

# make a surface with the current frame as its backing
palette = [(c, c, c) for c in range(256)]
frame_surf = pygame.image.frombuffer(framebuf, (320*2, 256*2), "P")
frame_surf.set_palette(palette)

# and one for the histogram too
histo_surf = pygame.image.frombuffer(histo_pix, (256, 64), "P")
histo_surf.set_palette(palette)

# construct the live video handler
handler = vidhandler.VidLiveHandler(320, 256, 60, 
    (framebuf_handler, histobuf_handler))
    
frames = 0
    
# stolen from stackoverflow https://stackoverflow.com/questions/7525214/how-to-scale-a-numpy-array
def scale(A, B, k):     # fill A with B scaled by k
    Y = A.shape[0]
    X = A.shape[1]
    for y in range(0, k):
        for x in range(0, k):
            A[y:Y:k, x:X:k] = B
            
try:
    while True:
        # pump events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
        if event.type == pygame.QUIT:
            break
            
        # copy the current video frame to the buffer
        # under a lock, so we don't tear it
        handler.lock_frame()
        scale(framebuf, framebuf_handler>>4, 2)
        np.copyto(histobuf, histobuf_handler)
        handler.unlock_frame()  
        # and finally blit it to the screen
        disp.blit(frame_surf, (0, 0))
        
        # now handle the histogram
        # first calculate the maximum value, for display normalization
        hmax = np.max(histobuf)
        # the levels mean the pixel should be on in this row
        levels = np.linspace(0, hmax, 64, endpoint=False, dtype=np.uint32)
        levels.shape = (64, 1)
        histo_pix[:] = (histobuf > levels)*255
        
        disp.blit(histo_surf, (0, 512+8))
        
        frames += 1
        if frames % 30 == 0:
            print(clock.get_fps())
        
        pygame.display.flip()
        clock.tick(30)
finally:
    handler.stop()
    
    
    