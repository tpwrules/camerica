import pygame

class Widget:
    def __init__(self, disp, pos, size):
        self.disp = disp
        self.rect = pygame.Rect(pos, size)
        self.self_rect = pygame.Rect((0, 0), size)
        
    def is_hit(self, pos):
        return self.rect.collidepoint(pos)
        
    def is_self_hit(self, pos):
        return self.self_rect.collidepoint(pos)
        
class HistoWidget(Widget):
    def __init__(self, disp, pos):
        super().__init__(disp, pos, (512, 64))
        
        self.min_bin = 0
        self.max_bin = 512
        
        self.drag_min_bin = 0
        self.drag_max_bin = 512
        
        self.mouse_clicked = False
        self.click_pos = None
        
        self.sizer_cursor = pygame.cursors.compile(
            pygame.cursors.sizer_x_strings)

    def mouseclick(self, down, pos):
        if not down:
            self.mouse_clicked = False
        elif down:
            obj = self.get_hover_obj(pos)
            if obj != "none":
                self.mouse_clicked = True
                self.click_pos = pos
                # determine which part of the histogram was clicked on
                self.click_obj = obj
                self.mousemove(pos)
        
    def get_hover_obj(self, pos):
        if pos[1] < 0 or pos[1] > 63 or pos[0] < -7 or pos[0] > 510+7:
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
            # use separate drag min/max so histogram doesn't get chopped
            # as the user drags it closer to the edges
            center = (self.drag_max_bin + self.drag_min_bin)//2
            dist_left = center-self.drag_min_bin
            dist_right = self.drag_max_bin-center
            # offset distances from click
            self.drag_min_bin = pos[0]-dist_left
            self.drag_max_bin = pos[0]+dist_right
            
            self.min_bin = self.drag_min_bin
            self.max_bin = self.drag_max_bin
            if self.min_bin < 0:
                self.min_bin = 0
            if self.min_bin > 511:
                self.min_bin = 511
            if self.max_bin < 1:
                self.max_bin = 1
            if self.max_bin > 512:
                self.max_bin = 512
            if self.min_bin == self.max_bin:
                if self.max_bin == 512:
                    self.min_bin -= 1
                else:
                    self.max_bin += 1
        elif self.click_obj == "min":
            self.min_bin = max(pos[0], 0)
            if self.min_bin >= self.max_bin:
                self.min_bin = self.max_bin-1
            self.drag_min_bin = self.min_bin
            self.drag_max_bin = self.max_bin
        elif self.click_obj == "max":
            self.max_bin = min(pos[0], 512)
            if self.max_bin <= self.min_bin:
                self.max_bin = self.min_bin+1
            self.drag_min_bin = self.min_bin
            self.drag_max_bin = self.max_bin

class SeekbarWidget(Widget):
    def __init__(self, disp, pos):
        super().__init__(disp, pos, (776, 40))
        self.pos_rel = pygame.Rect(0, 0, 776, 40)
        
        self.new_position = False
        
        # the seekbar is from (10, 15) to (766, 45)
        # the seek handle is 20x60
        
        self.seekbar_rect = pygame.Rect(5, 15, 766, 10).move(pos)
        self.seekhandle_rect = pygame.Rect(0, 0, 10, 40).move(pos)
        
        self.position = 0 # from 0 to 1
        
        self.handle_pos = 0 # top left corner, max 766
        
        self.mouse_clicked = False
            
    def mouseclick(self, down, pos):
        self.mouse_clicked = down and self.is_self_hit(pos)
        self.mousemove(pos)
        
    def mousemove(self, pos):
        if self.mouse_clicked and self.pos_rel.collidepoint(pos):
            new_pos = max(min(pos[0]-5, 766), 0)/766
            if new_pos != self.position:
                self.new_position = True
                self.position = max(min(pos[0]-5, 766), 0)/766
        
    def draw(self, pos):
        self.handle_pos = int(pos*766)
        pygame.draw.rect(self.disp, (0, 0, 0), self.rect)
        pygame.draw.rect(self.disp, (200, 200, 200), self.seekbar_rect)
        pygame.draw.rect(self.disp, (100, 100, 100),
            self.seekhandle_rect.move(self.handle_pos, 0))