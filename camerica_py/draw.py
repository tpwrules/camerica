# handle drawing to the display
import pygame
import numpy as np
import time

import cameras

neon_available = False
try:
    from neondraw.neondraw import lib, ffi
    if lib.nd_testadd1(4) == 5:
        neon_available = True
except:
    pass

def get_drawer(camera):
    if not isinstance(camera, cameras.Camera):
        raise ValueError("expected Camera, not {}".format(repr(camera)))
    if isinstance(camera, cameras.MerlinCamera):
        if neon_available:
            return NEONMerlinDrawer
        else:
            return MerlinDrawer
    elif isinstance(camera, cameras.Photon640Camera):
        if neon_available:
            return NEONPhoton640Drawer
        else:
            return Photon640Drawer
    else:
        raise Exception("huh?")

class Drawer:
    def __init__(self, disp):
        self.disp = disp
        
        self.perftime = 0
        self.perftimes = 0

        # allocate array to hold histogram data
        self.histobuf = np.empty((1, 512), dtype=np.uint32)
        
        # allocate a buffer for the histogram's pixel data
        self.histo_pix = np.empty((64, 512), dtype=np.uint8)
        # and a surface version of that buffer to draw it on the screen
        palette = [(c, c, c) for c in range(256)]
        self.histo_surf = pygame.image.frombuffer(self.histo_pix, (512, 64), "P")
        self.histo_surf.set_palette(palette)
        
        # preallocate some stuff used for histo so it doesn't go so slow
        self.h_cols = np.arange(512)
    
    def draw(self, histo_min, histo_max):
        # shift pixels to desired offset
        # we have 16 bit pixels and a 9 bit histogram,
        # so multiply offset by 2^7
        offset = int(histo_min*128)
        # to scale the pixels to the selected histogram area
        # we multiply by 512/range. 512/512 (max range) = 1
        # 512/1 (min range) = 512, max scale
        # pre-multiply by 128 to get more accuracy in the division
        # (frame draw will shift pixles right by 8 bits to get high 16
        #  + 7 bits to counter scale multiplication)
        scale = int((512*128)/(histo_max-histo_min))
        now = time.perf_counter()
        self.draw_frame(offset, scale)
        end = time.perf_counter()
        self.perftime += (end-now)
        self.perftimes += 1
        self.draw_histo(histo_min, histo_max)
        
    def stats(self):
        s = "{} us".format(self.perftime*1000000/self.perftimes)
        #self.perftime = 0
        #self.perftimes = 0
        return s
        
    def draw_histo(self, histo_min, histo_max):
        # first calculate the maximum value, for display normalization
        histobuf = self.histobuf
        hmax = np.max(histobuf)
        # the levels mean the pixel should be on in this row
        cols = self.h_cols
        histo_pix = self.histo_pix
        levels = np.linspace(hmax, 0, 64, dtype=np.uint32)
        levels.shape = (64, 1)
        np.greater(levels, histobuf, out=histo_pix)
        histo_pix -= 1
        highlighted = ((cols >= histo_min) & (cols < histo_max)).astype(np.uint8)
        highlighted <<= 7
        histo_pix |= highlighted

        self.disp.blit(self.histo_surf, ((640-512)/2, 512+8))
        
class MerlinDrawer(Drawer):
    def __init__(self, disp):
        super().__init__(disp)
        
        # allocate frame buffer with 32 bit pixels so we have
        # room to scale
        self.framebuf = np.empty((256, 320), dtype=np.int32)
        
        # allocate pixel data for the image
        self.frame_pix = np.empty((256*2, 320*2), dtype=np.uint8)
        # and it as a surface so we can draw it to the screen
        palette = [(c, c, c) for c in range(256)]
        self.frame_surf = pygame.image.frombuffer(
            self.frame_pix, (320*2, 256*2), "P")
        self.frame_surf.set_palette(palette)
        
    # stolen from stackoverflow 
    # https://stackoverflow.com/questions/7525214/how-to-scale-a-numpy-array
    def scale(self, A, B, k): # fill A with B scaled by K
        Y = A.shape[0]
        X = A.shape[1]
        for y in range(0, k):
            for x in range(0, k):
                A[y:Y:k, x:X:k] = B
        
    def draw_frame(self, offset, scale):
        # it's safe to modify the pixel buffer, so
        # let's do our operations in place
        
        # shift pixels to desired offset
        self.framebuf -= offset
        # and scale them too
        self.framebuf *= scale
        # remove low 8 bits of pixel + 7 bit extra scale
        self.framebuf >>= 15
        # and clamp to an 8 bit display pixel
        np.clip(self.framebuf, 0, 255, out=self.framebuf)
        # scale 1x1 pixels to 2x2 for screen
        self.scale(self.frame_pix, self.framebuf, 2)
        # and blit it to the screen
        self.disp.blit(self.frame_surf, (0, 0))
        
class NEONMerlinDrawer(Drawer):
    def __init__(self, disp):
        super().__init__(disp)
        
        # allocate a frame buffer the same size as the camera data
        # the NEON routine handles all the transformations
        self.framebuf = np.empty((256, 320), dtype=np.uint16)
        
    def draw_frame(self, offset, scale):
        # call the NEON routine and let it do the magic
        # we write directly into the display surface, so lock it first
        self.disp.lock()
        lib.nd_conv_merlin(self.framebuf.ctypes.data, # source ptr
            self.disp._pixels_address, # dest ptr
            offset,
            scale)
        self.disp.unlock()

class Photon640Drawer(Drawer):
    def __init__(self, disp):
        super().__init__(disp)
        
        # allocate frame buffer with 32 bit pixels so we have
        # room to scale
        self.framebuf = np.empty((512, 640), dtype=np.int32)
        
        # allocate pixel data for the image
        self.frame_pix = np.empty((512, 640), dtype=np.uint8)
        # and it as a surface so we can draw it to the screen
        palette = [(c, c, c) for c in range(256)]
        self.frame_surf = pygame.image.frombuffer(
            self.frame_pix, (640, 512), "P")
        self.frame_surf.set_palette(palette)
        
    def draw_frame(self, offset, scale):
        # it's safe to modify the pixel buffer, so
        # let's do our operations in place
        
        # shift pixels to desired offset
        self.framebuf -= offset
        # and scale them too
        self.framebuf *= scale
        # remove low 8 bits of pixel + 7 bit extra scale
        self.framebuf >>= 15
        # and clamp to an 8 bit display pixel,
        # then write it to the 8 bit display
        np.clip(self.framebuf, 0, 255, out=self.frame_pix)
        # now blit it to the screen
        self.disp.blit(self.frame_surf, (0, 0))
        
class NEONPhoton640Drawer(Drawer):
    def __init__(self, disp):
        super().__init__(disp)
        
        # allocate a frame buffer the same size as the camera data
        # the NEON routine handles all the transformations
        self.framebuf = np.empty((512, 640), dtype=np.uint16)
        
    def draw_frame(self, offset, scale):
        # call the NEON routine and let it do the magic
        # we write directly into the display surface, so lock it first
        self.disp.lock()
        lib.nd_conv_photon_640(self.framebuf.ctypes.data, # source ptr
            self.disp._pixels_address, # dest ptr
            offset,
            scale)
        self.disp.unlock()