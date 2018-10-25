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
        
        self.sizer_cursor = pygame.cursors.compile(
            pygame.cursors.sizer_x_strings)

    def mouseclick(self, down, pos):
        if not down:
            self.mouse_clicked = False
        elif down and pos[0] >= 0 and pos[0] < 512 and pos[1] >= 0 and pos[1] < 64:
            self.mouse_clicked = True
            self.click_pos = pos
            # determine which part of the histogram was clicked on
            self.click_obj = self.get_hover_obj(pos)
            self.mousemove(pos)
        
    def get_hover_obj(self, pos):
        if pos[1] < 0 or pos[1] > 63:
            return "none"
        elif abs(pos[0]-self.min_bin) < 7:
            return "min"
        elif abs(pos[0]-self.max_bin) < 7:
            return "max"
        else:
            return "mid"
        
    def mousemove(self, pos):
        if not self.mouse_clicked:
            obj = self.get_hover_obj(pos)
            if obj == "min" or obj == "max":
                pygame.mouse.set_cursor((24, 16), (12, 8), *self.sizer_cursor)
            else:
                pygame.mouse.set_cursor(*pygame.cursors.arrow)
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
        elif self.click_obj == "min":
            self.min_bin = max(pos[0], 0)
            if self.min_bin > self.max_bin:
                self.min_bin = self.max_bin-1
        elif self.click_obj == "max":
            self.max_bin = min(pos[0], 512)
            if self.max_bin < self.min_bin:
                self.max_bin = self.min_bin+1
        