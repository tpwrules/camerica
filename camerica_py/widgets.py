import pygame

class Widget:
    def __init__(self, disp, pos, size):
        self.disp = disp
        self.rect = pygame.Rect(pos, size)
        
    def is_hit(self, pos):
        return self.rect.collidepoint(pos)
        
class HistoWidget(Widget):
    def __init__(self, disp, pos):
        super().__init__(disp, pos, (512, 64))
        
        self.min_bin = 0
        self.max_bin = 512
        
        self.mouse_clicked = False
        self.click_pos = None
        
    def mouseclick(self, down, pos):
        self.mouse_clicked = down
        if down:
            self.click_pos = pos
            # determine which part of the histogram was clicked on
            if abs(pos[0]-self.min_bin) == 5:
                self.click_obj = "min"
            elif abs(pos[0]-self.max_bin) == 5:
                self.click_obj = "max"
            else:
                self.click_obj = "mid"
        self.mousemove(pos)
        
    def mousemove(self, pos):
        if not self.mouse_clicked:
            return
        if self.click_obj == "mid":
            # get center of histogram
            center = (self.max_bin + self.min_bin)//2
            dist_left = center-self.min_bin
            dist_right = self.max_bin-center
            # offset distances from click
            self.min_bin = pos[0]-dist_left
            self.max_bin = pos[0]+dist_right
            if self.min_bin < 0:
                self.min_bin = 0
            if self.min_bin > 511:
                self.min_bin = 511
            if self.max_bin < 1:
                self.max_bin = 1
            if self.max_bin > 512:
                self.max_bin = 512
        