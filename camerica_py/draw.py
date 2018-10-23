# handle drawing to the display
import pygame
import numpy as np

def get_drawer(camera):
    if camera == "merlin":
        return MerlinDrawer
    else:
        raise ValueError("unrecognized camera '{}'".format(camera)) 

class Drawer:
    def __init__(self, camera, disp, profile=False):
        self.disp = disp
        self.profile = profile
        
        self.camera = camera
        if camera == "merlin":
            self.width = 320
            self.height = 256
        else:
            raise ValueError("unrecognized camera '{}'".format(camera))
        
        # allocate array to hold histogram data
        self.histobuf = np.empty((1, 512), dtype=np.uint32)
        
        # allocate a buffer for the histogram's pixel data
        self.histo_pix = np.empty((64, 512), dtype=np.uint8)
        # and a surface version of that buffer to draw it on the screen
        palette = [(c, c, c) for c in range(256)]
        self.histo_surf = pygame.image.frombuffer(self.histo_pix, (512, 64), "P")
        self.histo_surf.set_palette(palette)
    
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
        self.draw_frame(offset, scale)
        self.draw_histo(histo_min, histo_max)
        
    def draw_histo(self, histo_min, histo_max):
        # first calculate the maximum value, for display normalization
        hmax = np.max(self.histobuf)
        # the levels mean the pixel should be on in this row
        levels = np.linspace(hmax, 0, 64, endpoint=False, dtype=np.uint32)
        levels.shape = (64, 1)
        np.copyto(self.histo_pix, ((self.histobuf > levels)*255).astype(np.uint8))
        cols = np.arange(512)
        self.histo_pix[:, (cols >= histo_min) & (cols < histo_max)] |= 0x80

        self.disp.blit(self.histo_surf, ((640-512)/2, 512+8))
        
class MerlinDrawer(Drawer):
    def __init__(self, disp, profile=False):
        super().__init__("merlin", disp, profile)
        
        # allocate frame buffer with 32 bit pixels so we have
        # room to scale
        self.framebuf = np.empty((256, 320), dtype=np.int32)
        
        # allocate pixel data for the image
        self.frame_pix = np.empty((256*2, 320*2), dtype=np.uint8)
        # and it as a surface so we can draw it to the screen
        palette = [(c, c, c) for c in range(256)]
        self.frame_surf = pygame.image.frombuffer(self.frame_pix, (320*2, 256*2), "P")
        self.frame_surf.set_palette(palette)
        
    # stolen from stackoverflow https://stackoverflow.com/questions/7525214/how-to-scale-a-numpy-array
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
        
        