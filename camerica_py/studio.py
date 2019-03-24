# display splash screen ASAP so it can get its glory
# while we import and construct the rest of the program

import pygame
splash = pygame.image.load("splash/splash.png")
disp_size = (320*2+136, 256*2+72+48)
disp = pygame.display.set_mode(disp_size)
pygame.display.set_caption("Camerica Studio")
disp.blit(splash, ((disp_size[0]-splash.get_width())//2, (disp_size[1]-splash.get_height())//2))
pygame.display.update()

import numpy as np
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

import vidhandler
from draw import get_drawer
from camerica_hw import detect_hardware
import cameras
import widgets
import tkwidgets

have_hardware = detect_hardware()

def set_mode(new_camera, mode, filename=None):
    global camera, drawer, handler, sys_mode, have_hardware, \
        framebuf_handler, histobuf_handler, statuses
    if not have_hardware:
        if mode == "live" or mode == "record":
            raise Exception(
                "cannot enter {} without hardware".format(mode))
    
    # deactivate the old modes
    if handler is not None:
        handler.stop()
    
    handler = None
    drawer = None
    camera = None
    
    if new_camera is not None:
        camera = new_camera
    else:
        camera = cameras.NoCamera()
    
    if isinstance(camera, cameras.NoCamera) and mode != "play":
        mode = "idle"
        
    # preserve FPS
    statuses = statuses[:2]
        
    if mode == "live":
        handler = vidhandler.VidLiveHandler(camera)
        statuses.extend([
            "Mode: "+mode, camera.name,
            "Current frame", "",
            "Dropped frames", "",
        ])
    elif mode == "record":
        handler = vidhandler.VidRecordHandler(camera, filename)
        statuses.extend([
            "Mode: "+mode, camera.name,
            "Current frame", "",
            "Dropped frames", "",
            "Saved frames", "",
            "Disk buffer", "",
        ])
    elif mode == "play":
        handler = vidhandler.VidPlaybackHandler(filename)
        camera = handler.camera
        statuses.extend([
            "Mode: "+mode, camera.name,
            "Current frame", "",
            "Dropped frames", "",
            "Saved frames", "",
            "Disk buffer", "",
        ])
    else:
        framebuf_handler = None
        histobuf_handler = None
        disp.fill((0, 0, 255), (0, 0, 640, 512))
        disp.fill((0, 0, 0), ((640-512)/2, 512+8, 512, 64))
        statuses.extend([
            "Mode: "+mode, camera.name,
        ])
        
    
    if mode != "idle":
        drawer = get_drawer(camera)(disp)
        framebuf_handler = handler.framebuf
        histobuf_handler = handler.histobuf

    sys_mode = mode

def select_camera():
    global camera
    camera_idx = tkwidgets.asklist("Hardware Setup",
        "Select the attached camera hardware",
        (cam.name for cam in cameras.cam_list),
        0 if camera is None else camera.hw_type.value)
    if camera_idx is None:
        return None
    return cameras.cam_list[camera_idx]

clock = pygame.time.Clock()

# start tk for our various dialogs
tk_root = tkinter.Tk()
tk_root.withdraw()

# load up whatever font pygame gives us to draw status
pygame.font.init()
font = pygame.font.SysFont("", 24)
button_font = pygame.font.SysFont("", 18)
statuses = ["Display FPS", ""]

# start with no handler or camera by default
handler = None
set_mode(None, "idle")

# but we do want to switch to live mode if there is hardware
# so the user has something to see
if have_hardware:
    new_camera = select_camera()
    if new_camera is not cameras.NoCamera and new_camera is not None:
        set_mode(new_camera(), "live")

frames = 0
           
histo_widget = widgets.HistoWidget(disp, ((640-512)/2, 512+8))
seekbar_widget = widgets.SeekbarWidget(disp, (0, 512+72+8))
widget_list = [histo_widget, seekbar_widget,
    widgets.ButtonWidget(disp, (640+8, 512+8), 50, button_font, "click!")]

try:
    while True:
        # pump events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and sys_mode == "play":
                    handler.playpause()
                elif event.key == pygame.K_LEFT and sys_mode == "play":
                    if handler.vid_frame > 0:
                        handler.seek(handler.vid_frame-1)
                elif event.key == pygame.K_RIGHT and sys_mode == "play":
                    if handler.vid_frame < handler.saved_frames-1:
                        handler.seek(handler.vid_frame+1)
                elif event.key == pygame.K_c and \
                        (sys_mode == "live" or sys_mode == "idle"):
                    if not have_hardware:
                        continue
                    # change attached camera. only meaningful while live
                    new_camera = select_camera()
                    if new_camera is not None:
                        set_mode(new_camera(), sys_mode)
                elif event.key == pygame.K_l and sys_mode != "live":
                    # switch to live mode
                    # ignore if no hardware
                    if not have_hardware:
                        continue
                    set_mode(camera, "live")
                elif event.key == pygame.K_r and sys_mode == "live":
                    # switch to recording mode
                    fname = asksaveasfilename(
                        filetypes=(("Camerica Videos", "*.vid"),))
                    if len(fname) == 0:
                        continue
                    set_mode(camera, "record", fname)
                elif event.key == pygame.K_p and \
                        (sys_mode == "live" or sys_mode == "idle"):
                    fname = askopenfilename(
                        filetypes=(("Camerica Videos", "*.vid"),))
                    if len(fname) == 0:
                        continue
                    set_mode(camera, "play", fname)
                elif event.key == pygame.K_i:
                    set_mode(camera, "idle")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1: continue
                pos = pygame.mouse.get_pos()
                for widget in widget_list:
                    widget.mouseclick(True,
                        (pos[0]-widget.rect.left, pos[1]-widget.rect.top))
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button != 1: continue
                pos = pygame.mouse.get_pos()
                for widget in widget_list:
                    widget.mouseclick(False,
                        (pos[0]-widget.rect.left, pos[1]-widget.rect.top))
            elif event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                for widget in widget_list:
                    widget.mousemove(
                        (pos[0]-widget.rect.left, pos[1]-widget.rect.top))
        if event.type == pygame.QUIT:
            break
            
        # copy the current video frame to the buffer
        # under a lock, so we don't tear it
        if handler is not None and drawer is not None:
            handler.lock_frame()
            np.copyto(drawer.framebuf, framebuf_handler)
            np.copyto(drawer.histobuf, histobuf_handler)
            handler.unlock_frame()
        
            # and use the drawer to make it show on the screen
            drawer.draw(histo_widget.min_bin, histo_widget.max_bin)
        
        if seekbar_widget.new_position and sys_mode == "play":
            seekbar_widget.new_position = False
            handler.seek(
                int(seekbar_widget.position*handler.saved_frames))
                
        if sys_mode == "play" and handler.saved_frames > 0:
            seekbar_widget.draw(handler.vid_frame/handler.saved_frames)
        else:
            seekbar_widget.draw(1)
        
        # determine new status texts
        # disk buffer fullness
        if sys_mode == "record":
            entries = 10-handler.vf.vf_written_bufs.qsize()
            statuses[11] = "{}%".format(int(entries*100/10))
        elif sys_mode == "play":
            entries = 10-handler.vf.vf_bufs_to_read.qsize()
            statuses[11] = "{}%".format(int(entries*100/10))
            
        if sys_mode != "idle":
            # current number of frames
            statuses[5] = str(handler.current_frame+1)
            # number of frames dropped so far
            statuses[7] = str(handler.dropped_frames)
            if sys_mode != "live":
                # total frames recorded/available to play
                statuses[9] = str(handler.saved_frames)
        
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
            
        # draw the buttons which also got erased
        for widget in widget_list:
            if isinstance(widget, widgets.ButtonWidget):
                widget.draw()
        
        frames += 1
        if frames % 30 == 0:
            statuses[1] = str(int(clock.get_fps()+.5))
        
        pygame.display.update()
        clock.tick(30)
finally:
    if handler is not None:
        handler.stop()
    