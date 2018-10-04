import sys
import pygame
import numpy as np

import stacktracer
stacktracer.trace_start("trace.html",interval=5,auto=True)

import vidhandler

# launch the display and pygame stuff
disp = pygame.display.set_mode((320*2, 256*2+72))
clock = pygame.time.Clock()

# construct buffers for the current displayed frame, to be written
# by the handler
framebuf_handler = np.empty((256, 320), dtype=np.uint16)
histobuf_handler = np.empty((1, 512), dtype=np.uint32)
# and then ones for the frame we are working on displaying
framebuf = np.empty((256, 320), dtype=np.int32)
histobuf = np.empty((1, 512), dtype=np.uint32)

frame_pix = np.empty((256*2, 320*2), dtype=np.uint8)

histo_levels = np.empty((1, 64), dtype=np.uint32)
histo_pix = np.empty((64, 512), dtype=np.uint8)

# make a surface with the current frame as its backing
palette = [(c, c, c) for c in range(256)]
frame_surf = pygame.image.frombuffer(frame_pix, (320*2, 256*2), "P")
frame_surf.set_palette(palette)

# and one for the histogram too
histo_surf = pygame.image.frombuffer(histo_pix, (512, 64), "P")
histo_surf.set_palette(palette)

mode = sys.argv[1]

if mode == "live":
    handler = vidhandler.VidLiveHandler(320, 256, 60,
        (framebuf_handler, histobuf_handler))
elif mode == "record":
    handler = vidhandler.VidRecordHandler(320, 256, 60, 
        (framebuf_handler, histobuf_handler), sys.argv[2])
elif mode == "playback":
    handler = vidhandler.VidPlaybackHandler(320, 256, 60,
        (framebuf_handler, histobuf_handler), sys.argv[2])
    
frames = 0
    
# stolen from stackoverflow https://stackoverflow.com/questions/7525214/how-to-scale-a-numpy-array
def scale(A, B, k):     # fill A with B scaled by k
    Y = A.shape[0]
    X = A.shape[1]
    for y in range(0, k):
        for x in range(0, k):
            A[y:Y:k, x:X:k] = B
            
histo_min_pix = 0
histo_max_pix = 512
histo_center = 256

try:
    while True:
        # pump events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and mode == "playback":
                    handler.playpause()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if pos[1] < 512+8:
                    if mode != "playback":
                        continue
                    # handle seek request
                    target = pos[0]*handler.vf.total_frames//640
                    handler.seek(target)
                    continue
                xpos = pos[0]
                if xpos < (640-512)/2:
                    xpos = (640-512)/2
                elif xpos > (640-512)/2+512:
                    xpos = (640-512)/2+512
                xpos -= (640-512)/2
                if event.button == 3: # right click
                    diff = histo_max_pix - histo_center
                    histo_min_pix = xpos - diff
                    histo_max_pix = xpos + diff
                    histo_center = xpos
                    if histo_min_pix < 0:
                        histo_min_pix = 0
                    if histo_max_pix > 512:
                        histo_max_pix = 512
                    if histo_min_pix == histo_max_pix:
                        histo_max_pix += 1
                elif event.button == 1: # left click
                    if xpos < histo_center:
                        histo_min_pix = xpos
                    elif xpos > histo_center:
                        histo_max_pix = xpos
                    histo_center = (histo_max_pix+histo_min_pix)//2
                    if histo_min_pix == histo_max_pix:
                        histo_max_pix += 1
        if event.type == pygame.QUIT:
            break
            
        # copy the current video frame to the buffer
        # under a lock, so we don't tear it
        handler.lock_frame()
        np.copyto(framebuf, framebuf_handler)
        np.copyto(histobuf, histobuf_handler)
        handler.unlock_frame()  
        # perform user requested value scaling
        framebuf -= int(histo_min_pix*128)
        framebuf *= int(512/(histo_max_pix-histo_min_pix))
        framebuf >>= 8
        np.clip(framebuf, 0, 255, out=framebuf)
        scale(frame_pix, framebuf, 2)
        # and finally blit it to the screen
        disp.blit(frame_surf, (0, 0))
        
        # now handle the histogram
        # first calculate the maximum value, for display normalization
        hmax = np.max(histobuf)
        # the levels mean the pixel should be on in this row
        levels = np.linspace(0, hmax, 64, endpoint=False, dtype=np.uint32)
        levels.shape = (64, 1)
        np.copyto(histo_pix, ((histobuf > levels)*255).astype(np.uint8))
        cols = np.arange(512)
        histo_pix[:, (cols > histo_min_pix) & (cols < histo_max_pix)] ^= 0xFF

        disp.blit(histo_surf, ((640-512)/2, 512+8))
        
        frames += 1
        if frames % 30 == 0:
            print(clock.get_fps(), handler.dropped_frames)
        
        pygame.display.update()
        clock.tick(30)
finally:
    pass
    #handler.stop()
    