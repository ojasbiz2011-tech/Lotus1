import random
import copy
import time
from collections import deque

# --- CONFIGURATION ---
GRID_SIZE = 6

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

# Fallback Level (just in case 1.5s isn't enough)
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
    start_time = time.time()
    
    # 1.5 Second Limit as requested
    while time.time() - start_time < 1.5:
        temp_blocks = [Block(random.randint(0, 1), 2, 2, 'H', True)]
        target_count = random.randint(14, 18) # High Density
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
        
        # Exact condition from your code: >= 13 blocks, >= 10 moves
        if len(temp_blocks) >= 13:
            result = solve_board(temp_blocks)
            if result >= 10:
                data = []
                for i, b in enumerate(temp_blocks):
                    data.append({
                        "id": i, "col": b.col, "row": b.row, 
                        "length": b.length, "orientation": b.orientation, 
                        "is_target": b.is_target
                    })
                return data

    return BACKUP_LEVEL
