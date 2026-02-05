import pygame
import random
import copy
import time
from collections import deque

pygame.init()

GRID_SIZE = 6
TILE_SIZE = 85

class Block:
    def __init__(self, col, row, length, orientation, is_target=False):
        self.col = col
        self.row = row
        self.length = length
        self.orientation = orientation
        self.is_target = is_target
        # Visual data for collision checks
        self.gap = 3
        if self.orientation == 'H':
            self.width = length * TILE_SIZE - (self.gap * 2)
            self.height = TILE_SIZE - (self.gap * 2)
        else:
            self.width = TILE_SIZE - (self.gap * 2)
            self.height = length * TILE_SIZE - (self.gap * 2)
        self.rect = pygame.Rect(0, 0, self.width, self.height)

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
    
    # Lower depth for speed
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

def generate_puzzle():
    start_time = time.time()
    best_data = None
    max_difficulty = -1
    
    # TIGHT TIMEOUT: 1.0 second max.
    # If we exceed this, we return 'best_data' immediately.
    while time.time() - start_time < 1.0:
        
        # 1. Target Block (Red) - Always Row 2, Col 0 or 1
        target_col = random.randint(0, 1)
        temp_blocks = [Block(target_col, 2, 2, 'H', True)]
        
        # 2. Add Obstacles (9 to 13 blocks)
        target_count = random.randint(9, 13)
        fails = 0
        
        while len(temp_blocks) < target_count and fails < 100:
            l = random.choice([2, 2, 3])
            o = random.choice(['H', 'V'])
            
            if o == 'H':
                c = random.randint(0, GRID_SIZE - l)
                r = random.randint(0, GRID_SIZE - 1)
            else:
                c = random.randint(0, GRID_SIZE - 1)
                r = random.randint(0, GRID_SIZE - l)
            
            if r == 2 and o == 'H': # Avoid cluttering exit row
                fails += 1
                continue
                
            nb = Block(c, r, l, o)
            if not check_grid_collision(c, r, nb, temp_blocks):
                temp_blocks.append(nb)
            else:
                fails += 1
        
        # 3. Solve Check
        if len(temp_blocks) >= 6:
            result = solve_board(temp_blocks)
            
            if result > 0:
                data = []
                for i, b in enumerate(temp_blocks):
                    data.append({
                        "id": i, "col": b.col, "row": b.row, "length": b.length, "orientation": b.orientation, "is_target": b.is_target
                    })
                
                if result > max_difficulty:
                    max_difficulty = result
                    best_data = data
                
                # If puzzle is decent (6+ moves), return instantly
                if result >= 6: 
                    return data

    # 4. Fallback
    if best_data:
        return best_data
    
    # Emergency fallback (should theoretically never hit here with 1.0s timeout)
    return generate_puzzle()
