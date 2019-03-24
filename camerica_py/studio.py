# display splash screen ASAP so it can get its glory
# while we import and construct the rest of the program

import time
splash_start = time.monotonic()

# eat pygame's welcome and support messages
import contextlib
with contextlib.redirect_stdout(None):
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
        framebuf_handler, histobuf_handler, statuses, \
        curr_mode_text, curr_camera_which_text, button_font
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
    
    if not have_hardware:
        new_camera = None
    
    if not have_hardware and mode != "play":
        mode = "idle"
    
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
            "Current frame", "",
            "Dropped frames", "",
        ])
    elif mode == "record":
        handler = vidhandler.VidRecordHandler(camera, filename)
        statuses.extend([
            "Current frame", "",
            "Dropped frames", "",
            "Saved frames", "",
            "Disk buffer", "",
        ])
    elif mode == "play":
        handler = vidhandler.VidPlaybackHandler(filename)
        camera = handler.camera
        statuses.extend([
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
        
    
    if mode != "idle":
        drawer = get_drawer(camera)(disp)
        framebuf_handler = handler.framebuf
        histobuf_handler = handler.histobuf
        
    curr_camera_which_text = button_font.render(camera.name,
        True, (255, 255, 255), (0, 0, 0))
    curr_mode_text = button_font.render("Current mode: "+mode,
        True, (255, 255, 255), (0, 0, 0))
        
    if mode == "idle":
        mode_live_widget.set_enabled(not isinstance(camera, cameras.NoCamera))
        mode_record_widget.set_enabled(False)
        mode_play_widget.set_enabled(True)
    elif mode == "live":
        mode_live_widget.set_enabled(True)
        mode_record_widget.set_enabled(True)
        mode_play_widget.set_enabled(True)
    elif mode == "record" or mode == "play":
        mode_live_widget.set_enabled(have_hardware)
        mode_record_widget.set_enabled(False)
        mode_play_widget.set_enabled(False)
    mode_camera_widget.set_enabled(
        have_hardware and (mode == "idle" or mode == "live"))

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

frames = 0
           
histo_widget = widgets.HistoWidget(disp, ((640-512)/2, 512+8))
seekbar_widget = widgets.SeekbarWidget(disp, (0, 512+72+8))
mode_idle_widget = \
    widgets.ButtonWidget(disp, (640+8, 440), 50, button_font, "Idle")
mode_live_widget = \
    widgets.ButtonWidget(disp, (640+8+(136/2), 440), 50, button_font, "Live")
mode_record_widget = \
    widgets.ButtonWidget(disp, (640+8, 470), 50, button_font, "Record")
mode_play_widget = \
    widgets.ButtonWidget(disp, (640+8+(136/2), 470), 50, button_font, "Play")

mode_camera_widget = \
    widgets.ButtonWidget(disp, (640+8, 380), 100, button_font, "Select Camera")

widget_list = [histo_widget, seekbar_widget,
    mode_idle_widget, mode_live_widget,
    mode_record_widget, mode_play_widget,
    mode_camera_widget]
    
# start with no handler or camera by default
handler = None
set_mode(None, "idle")

# but we do want to switch to live mode if there is hardware
# so the user has something to see
if have_hardware:
    new_camera = select_camera()
    if new_camera is not cameras.NoCamera and new_camera is not None:
        set_mode(new_camera(), "live")
    
curr_camera_text = button_font.render("Current camera:",
    True, (255, 255, 255), (0, 0, 0))

# set when a button or key is pressed to change modes
# the main loop then acts on the last requested action
next_mode = ""

# ensure splash gets the love it deserves
splash_time = time.monotonic() - splash_start
if splash_time < 5:
    time.sleep(5-splash_time)

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
                elif event.key == pygame.K_c:
                    next_mode = "select_camera"
                elif event.key == pygame.K_l:
                    next_mode = "live"
                elif event.key == pygame.K_r:
                    next_mode = "record"
                elif event.key == pygame.K_p:
                    next_mode = "play"
                elif event.key == pygame.K_i:
                    next_mode = "idle"
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
            
        # check any of the buttons to see if they were clicked
        # they will get un-clicked when drawn later in the loop
        if mode_idle_widget.clicked:
            next_mode = "idle"
        elif mode_live_widget.clicked:
            next_mode = "live"
        elif mode_record_widget.clicked:
            next_mode = "record"
        elif mode_play_widget.clicked:
            next_mode = "play"
        elif mode_camera_widget.clicked:
            next_mode = "select_camera"
            
        # change modes based on request:
        if next_mode == "":
            pass
        elif next_mode == "idle":
            # it's always possible to go idle
            set_mode(camera, "idle")
        elif next_mode == "live":
            # can only go live if there's a camera to go live on
            if not isinstance(camera, cameras.NoCamera):
                set_mode(camera, "live")
        elif next_mode == "record":
            # can only record if currently previewing
            if sys_mode == "live":
                fname = asksaveasfilename(
                    filetypes=(("Camerica Video", "*.vid"),))
                set_mode(camera, "record", fname)
        elif next_mode == "play":
            # we can play if it doesn't interrupt a recording
            if sys_mode != "record":
                fname = askopenfilename(
                    filetypes=(("Camerica Video", "*.vid"),))
                set_mode(camera, "play", fname)
        elif next_mode == "select_camera":
            # can only select camera if there's the possibility
            # of a camera being attached
            # and only if we're previewing
            if have_hardware and sys_mode != "play" and sys_mode != "record":
                new_camera = select_camera()
                if new_camera is not None:
                    set_mode(new_camera(), sys_mode)
            
        next_mode = ""
            
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
            statuses[9] = "{}%".format(int(entries*100/10))
        elif sys_mode == "play":
            entries = 10-handler.vf.vf_bufs_to_read.qsize()
            statuses[9] = "{}%".format(int(entries*100/10))
            
        if sys_mode != "idle":
            # current number of frames
            statuses[3] = str(handler.current_frame+1)
            # number of frames dropped so far
            statuses[5] = str(handler.dropped_frames)
            if sys_mode != "live":
                # total frames recorded/available to play
                statuses[7] = str(handler.saved_frames)
        
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
                widget.clicked = False
                widget.draw()
        
        # and button labels
        disp.blit(curr_camera_text, (640+8, 344))
        disp.blit(curr_camera_which_text, (640+8, 360))
        disp.blit(curr_mode_text, (640+8, 420))
        
        frames += 1
        if frames % 30 == 0:
            statuses[1] = str(int(clock.get_fps()+.5))
        
        pygame.display.update()
        clock.tick(30)
finally:
    if handler is not None:
        handler.stop()
    