import os
# --- WEB FIX: Run Pygame in Headless Mode (No Window) ---
os.environ["SDL_VIDEODRIVER"] = "dummy" 

import pygame
import sys
import random
import copy
from collections import deque

# --- CONFIGURATION ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
GRID_SIZE = 6
TILE_SIZE = 85
GRID_OFFSET_X = (SCREEN_WIDTH - (GRID_SIZE * TILE_SIZE)) // 2
GRID_OFFSET_Y = 160

# --- LIGHT WOOD THEME ---
COLOR_BG = (250, 242, 230)            # Creamy Wall
COLOR_FRAME = (101, 67, 33)           # Dark Walnut
COLOR_WELL = (180, 130, 70)           # Warm Oak (The board background)

# Block Colors
COLOR_RED = (205, 70, 70)             # Hero (Red Wood)
COLOR_H = (235, 210, 150)             # Pine (Horizontal)
COLOR_V = (210, 180, 130)             # Ash (Vertical)
COLOR_TEXT = (80, 50, 30)

class Block:
    def __init__(self, col, row, length, orientation, is_target=False):
        self.col = col
        self.row = row
        self.length = length
        self.orientation = orientation
        self.is_target = is_target
        self.initial_pos = (col, row)
        self.gap = 3

        if self.orientation == 'H':
            self.width = length * TILE_SIZE - (self.gap * 2)
            self.height = TILE_SIZE - (self.gap * 2)
            self.color = COLOR_RED if is_target else COLOR_H
        else:
            self.width = TILE_SIZE - (self.gap * 2)
            self.height = length * TILE_SIZE - (self.gap * 2)
            self.color = COLOR_V

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.update_pixel_pos()

    def update_pixel_pos(self):
        self.rect.topleft = (GRID_OFFSET_X + (self.col * TILE_SIZE) + self.gap,
                             GRID_OFFSET_Y + (self.row * TILE_SIZE) + self.gap)

    # Note: This draw function exists but won't be seen on the server
    def draw(self, surface):
        shadow = self.rect.copy()
        shadow.x += 4; shadow.y += 4
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 40), s.get_rect(), border_radius=6)
        surface.blit(s, shadow.topleft)

        pygame.draw.rect(surface, self.color, self.rect, border_radius=6)

        pygame.draw.line(surface, (255, 255, 255), (self.rect.left+3, self.rect.top+2), (self.rect.right-3, self.rect.top+2), 2)
        pygame.draw.line(surface, (255, 255, 255), (self.rect.left+2, self.rect.top+3), (self.rect.left+2, self.rect.bottom-3), 2)
        pygame.draw.line(surface, (0, 0, 0), (self.rect.left+3, self.rect.bottom-2), (self.rect.right-3, self.rect.bottom-2), 2)
        pygame.draw.line(surface, (0, 0, 0), (self.rect.right-2, self.rect.top+3), (self.rect.right-2, self.rect.bottom-3), 2)

# --- LOGIC ENGINE ---

def check_grid_collision(c, r, b, all_blocks):
    if c < 0 or r < 0: return True
    if b.orientation == 'H':
        if c + b.length > GRID_SIZE: return True
        cells = set((c + i, r) for i in range(b.length))
    else:
        if r + b.length > GRID_SIZE: return True
        cells = set((c, r + i) for i in range(b.length))
    
    for o in all_blocks:
        if o is b: continue
        o_cells = set((o.col + i, o.row) if o.orientation == 'H' else (o.col, o.row + i) for i in range(o.length))
        if not cells.isdisjoint(o_cells): return True
    return False

def solve_board(blocks):
    sim = [copy.copy(b) for b in blocks]
    try:
        target_idx = next(i for i, b in enumerate(sim) if b.is_target)
    except StopIteration: return -1

    start_state = tuple((b.col, b.row) for b in sim)
    queue = deque([(start_state, 0)])
    visited = {start_state}
    
    max_depth = 40 
    
    while queue:
        state, depth = queue.popleft()
        if depth > max_depth: return -1 
        
        for i, pos in enumerate(state):
            sim[i].col, sim[i].row = pos
            
        if sim[target_idx].col == GRID_SIZE - 2:
            return depth 
            
        for i, b in enumerate(sim):
            moves = [(-1, 0), (1, 0)] if b.orientation == 'H' else [(0, -1), (0, 1)]
            for dc, dr in moves:
                if not check_grid_collision(b.col+dc, b.row+dr, b, sim):
                    ns = list(state)
                    ns[i] = (b.col+dc, b.row+dr)
                    nt = tuple(ns)
                    if nt not in visited:
                        visited.add(nt)
                        queue.append((nt, depth+1))
    return -1

# --- WEB ADAPTER (The "Few Lines Added at the End") ---
def generate_level_data():
    pygame.init() # Safe because of SDL_VIDEODRIVER dummy
    # We don't need set_mode here for logic, just the Rects
    
    # 1.5 Second Timeout Loop (Same as your logic)
    import time
    start_time = time.time()
    
    while time.time() - start_time < 1.5:
        temp_blocks = [Block(random.randint(0, 1), 2, 2, 'H', True)]
        target_count = random.randint(14, 18)
        fails = 0
        
        while len(temp_blocks) < target_count and fails < 50:
            l = random.choice([2, 2, 3])
            o = random.choice(['H', 'V'])
            
            if o == 'H':
                c = random.randint(0, GRID_SIZE - l)
                r = random.randint(0, GRID_SIZE - 1)
            else:
                c = random.randint(0, GRID_SIZE - 1)
                r = random.randint(0, GRID_SIZE - l)
            
            if r == 2 and o == 'H': 
                fails += 1
                continue
                
            nb = Block(c, r, l, o)
            if not check_grid_collision(c, r, nb, temp_blocks):
                temp_blocks.append(nb)
            else:
                fails += 1
        
        if len(temp_blocks) >= 13:
            result = solve_board(temp_blocks)
            if result >= 10:
                # SUCCESS! Convert Pygame Objects to JSON Data
                data = []
                for i, b in enumerate(temp_blocks):
                    data.append({
                        "id": i, "col": b.col, "row": b.row, 
                        "length": b.length, "orientation": b.orientation, 
                        "is_target": b.is_target
                    })
                return data

    # Fallback if timeout
    return generate_level_data()
