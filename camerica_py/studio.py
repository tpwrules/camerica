import sys
import pygame
import numpy as np

import vidhandler
from draw import get_drawer

# launch the display and pygame stuff
disp = pygame.display.set_mode((320*2+136, 256*2+72))
clock = pygame.time.Clock()

# load up whatever font pygame gives us to draw status
pygame.font.init()
font = pygame.font.SysFont("", 24)

# construct the class to draw the image on screen
drawer = get_drawer("merlin")(disp)

# construct buffers for the current displayed frame, to be written
# by the handler
framebuf_handler = np.empty((256, 320), dtype=np.uint16)
histobuf_handler = np.empty((1, 512), dtype=np.uint32)

# save the buffers made by the drawer so we can copy into them
framebuf = drawer.framebuf
histobuf = drawer.histobuf

mode = sys.argv[1]

handler = None
if mode == "live":
    handler = vidhandler.VidLiveHandler(320, 256, 60,
        (framebuf_handler, histobuf_handler))
elif mode == "record":
    handler = vidhandler.VidRecordHandler(320, 256, 60, 
        (framebuf_handler, histobuf_handler), sys.argv[2])
elif mode == "play":
    handler = vidhandler.VidPlaybackHandler(320, 256, 60,
        (framebuf_handler, histobuf_handler), sys.argv[2])
        
if handler is None:
    raise Exception("invalid mode. use 'live', 'record', or 'play'")
    
frames = 0
            
histo_min_pix = 0
histo_max_pix = 512
histo_center = 256

# build list of status texts
# evens are left justified, odds are right-justified
# one row gap between them

statuses = [
    "Display FPS",
    "",
    "Current frame", # frames
    "",
    "Dropped frames", # frames
    "",
    "Saved frames", # frames
    "",
]

try:
    while True:
        # pump events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and mode == "play":
                    handler.playpause()
                elif event.key == pygame.K_LEFT and mode == "play":
                    if handler.curr_frame > 0:
                        handler.seek(handler.curr_frame-1)
                elif event.key == pygame.K_RIGHT and mode == "play":
                    if handler.curr_frame < handler.total_frames-1:
                        handler.seek(handler.curr_frame+1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if pos[1] < 512+8:
                    if mode != "play":
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
        
        # and use the drawer to make it show on the screen
        drawer.draw(histo_min_pix, histo_max_pix)
        
        # determine new status texts
        # current number of frames
        statuses[3] = str(3)
        # number of frames dropped so far
        statuses[5] = str(handler.dropped_frames)
        # total frames recorded/available to play
        statuses[7] = str(handler.total_frames)
        
        # erase the status area
        disp.fill((0, 0, 0), (640+8, 0, 128, 512))
        
        # draw the status items
        status_y = 20
        for name, value in zip(statuses[::2], statuses[1::2]):
            pixels = font.render(name, True, (255, 255, 255), (0, 0, 0))
            disp.blit(pixels, (640+8, status_y))
            status_y += 26
            
            pixels = font.render(value, True, (255, 255, 255), (0, 0, 0))
            disp.blit(pixels, (640+136-pixels.get_width(), status_y))
            status_y += 26+13
        
        frames += 1
        if frames % 30 == 0:
            statuses[1] = str(int(clock.get_fps()+.5))
        
        pygame.display.update()
        clock.tick(30)
finally:
    handler.stop()
    