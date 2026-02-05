import pygame
import random
import copy
import time
from collections import deque

pygame.init()

# --- CONFIGURATION ---
GRID_SIZE = 6
TILE_SIZE = 85

class Block:
    def __init__(self, col, row, length, orientation, is_target=False):
        self.col = col
        self.row = row
        self.length = length
        self.orientation = orientation
        self.is_target = is_target
        # Visual/Rect data needed for collision logic
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
    # Create a simulation copy
    sim = [copy.copy(b) for b in blocks]
    try:
        target_idx = next(i for i, b in enumerate(sim) if b.is_target)
    except StopIteration: return -1

    # State is represented by a tuple of (col, row) for all blocks
    start_state = tuple((b.col, b.row) for b in sim)
    queue = deque([(start_state, 0)])
    visited = {start_state}
    max_depth = 40 
    
    while queue:
        state, depth = queue.popleft()
        if depth > max_depth: return -1 # Too hard/complex for quick solve
        
        # Apply current state to simulation blocks
        for i, pos in enumerate(state):
            sim[i].col, sim[i].row = pos
            
        # Check Win
        if sim[target_idx].col == GRID_SIZE - 2:
            return depth 
            
        # Explore Moves
        for i, b in enumerate(sim):
            moves = [(-1, 0), (1, 0)] if b.orientation == 'H' else [(0, -1), (0, 1)]
            for dc, dr in moves:
                # Check collision with the layout from THIS state
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
    
    # TIMEOUT STRATEGY: 
    # Try to find a hard level for exactly 1.5 seconds.
    # If we find a "Perfect" level (10+ moves), return instantly.
    # If time runs out, return the hardest one we found so far.
    
    while time.time() - start_time < 1.5:
        
        # 1. Create Random Layout
        temp_blocks = [Block(random.randint(0, 2), 2, 2, 'H', True)]
        target_count = random.randint(13, 16) # KEEPING IT DENSE & HARD
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
            
            if r == 2 and o == 'H': 
                fails += 1
                continue
                
            nb = Block(c, r, l, o)
            if not check_grid_collision(c, r, nb, temp_blocks):
                temp_blocks.append(nb)
            else:
                fails += 1
        
        # 2. Check Solvability
        if len(temp_blocks) >= 8:
            result = solve_board(temp_blocks)
            
            if result > 0:
                # Convert to JSON format
                data = []
                for i, b in enumerate(temp_blocks):
                    data.append({
                        "id": i, "col": b.col, "row": b.row, "length": b.length, "orientation": b.orientation, "is_target": b.is_target
                    })
                
                # If this is the hardest so far, save it
                if result > max_difficulty:
                    max_difficulty = result
                    best_data = data
                
                # If it is HARD ENOUGH (Gold Standard), stop looking and return immediately
                if result >= 12: 
                    return data

    # 3. Time is up! Return the best one we found.
    # If we found nothing solvable (extremely rare), recurse to try again.
    if best_data:
        return best_data
    else:
        return generate_puzzle()

def validate_moves(initial_level_data, move_history):
    blocks = []
    for b in initial_level_data:
        blocks.append(Block(b['col'], b['row'], b['length'], b['orientation'], b['is_target']))
    
    valid_moves = 0
    for m in move_history:
        b = blocks[m['id']]
        if not check_grid_collision(m['col'], m['row'], b, blocks):
             b.col = m['col']
             b.row = m['row']
             valid_moves += 1
    
    target = next(b for b in blocks if b.is_target)
    if target.col == GRID_SIZE - 2:
        return True, valid_moves
    return False, valid_moves
