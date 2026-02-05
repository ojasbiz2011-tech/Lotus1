import random
import copy
import time
from collections import deque

# --- CONFIGURATION ---
GRID_SIZE = 6
# Note: TILE_SIZE is handled on frontend, logic only needs grid coords

class Block:
    def __init__(self, col, row, length, orientation, is_target=False):
        self.col = col
        self.row = row
        self.length = length
        self.orientation = orientation
        self.is_target = is_target

def check_grid_collision(c, r, b, all_blocks):
    # Boundary
    if c < 0 or r < 0: return True
    if b.orientation == 'H':
        if c + b.length > GRID_SIZE: return True
        cells = set((c + i, r) for i in range(b.length))
    else:
        if r + b.length > GRID_SIZE: return True
        cells = set((c, r + i) for i in range(b.length))
    
    # Overlap
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

# A backup level in case generation times out (Prevents loading stuck)
BACKUP_LEVEL = [
    {"id":0, "col":0, "row":2, "length":2, "orientation":"H", "is_target":True},
    {"id":1, "col":2, "row":0, "length":3, "orientation":"V", "is_target":False},
    {"id":2, "col":4, "row":0, "length":2, "orientation":"V", "is_target":False},
    {"id":3, "col":0, "row":4, "length":2, "orientation":"V", "is_target":False},
    {"id":4, "col":2, "row":3, "length":2, "orientation":"H", "is_target":False},
    {"id":5, "col":4, "row":2, "length":3, "orientation":"V", "is_target":False},
    {"id":6, "col":0, "row":0, "length":2, "orientation":"H", "is_target":False},
    {"id":7, "col":3, "row":5, "length":2, "orientation":"H", "is_target":False}
]

def generate_puzzle():
    # 1.5 Second Timeout as requested
    start_time = time.time()
    
    while time.time() - start_time < 1.5:
        # Target: Row 2, Random Col 0-2 (From your code)
        temp_blocks = [Block(random.randint(0, 1), 2, 2, 'H', True)]
        
        # High Density: 14-18 blocks (From your code)
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
            
            # OG Logic: No horizontal blocks on row 2 except hero
            if r == 2 and o == 'H':
                fails += 1
                continue
                
            nb = Block(c, r, l, o)
            if not check_grid_collision(c, r, nb, temp_blocks):
                temp_blocks.append(nb)
            else:
                fails += 1
        
        # Verify Solvability (At least 8 moves to be fun)
        if len(temp_blocks) >= 10:
            result = solve_board(temp_blocks)
            if result >= 8:
                # Convert to JSON for frontend
                data = []
                for i, b in enumerate(temp_blocks):
                    data.append({
                        "id": i, "col": b.col, "row": b.row, 
                        "length": b.length, "orientation": b.orientation, 
                        "is_target": b.is_target
                    })
                return data

    # If 1.5s passes and no level is found, return backup (Prevents Stuck Screen)
    return BACKUP_LEVEL
