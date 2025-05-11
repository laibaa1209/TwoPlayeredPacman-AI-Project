from collections import deque
import heapq
import random
import time

# --- BFS Algorithm ---
def bfs(start, goal, maze):
    queue = deque([(start, [])])
    visited = set([start])
    
    while queue:
        (x, y), path = queue.popleft()
        
        if (x, y) == goal:
            return path
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and
                (nx, ny) not in visited and maze[ny][nx] != 1):  # Changed from == 0 to != 1
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
    
    return []


# --- A* Algorithm ---
class Node:
    def __init__(self, x, y, parent=None):
        self.x = x
        self.y = y
        self.parent = parent
        self.g = 0
        self.h = 0
        self.f = 0

    def __lt__(self, other):
        return self.f < other.f

def astar(start, goal, maze):
    open_list = []
    closed_set = set()

    start_node = Node(*start)
    goal_node = Node(*goal)
    heapq.heappush(open_list, start_node)

    while open_list:
        current = heapq.heappop(open_list)
        if (current.x, current.y) == (goal_node.x, goal_node.y):
            path = []
            while current:
                path.append((current.x, current.y))
                current = current.parent
            return path[::-1]

        closed_set.add((current.x, current.y))

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = current.x + dx, current.y + dy
            if (0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and
                (nx, ny) not in closed_set and maze[ny][nx] != 1):  # Changed from == 0 to != 1
                neighbor = Node(nx, ny, current)
                neighbor.g = current.g + 1
                neighbor.h = abs(goal_node.x - nx) + abs(goal_node.y - ny)
                neighbor.f = neighbor.g + neighbor.h
                heapq.heappush(open_list, neighbor)

    return []


# --- Minimax Ghost Logic ---
# Cache for minimax evaluations
minimax_cache = {}
move_cache = {}

def minimax_get_possible_moves(pos, maze):
    """Get possible moves with caching"""
    cache_key = (pos, tuple(map(tuple, maze)))
    if cache_key in move_cache:
        return move_cache[cache_key]
        
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    moves = []
    for dx, dy in directions:
        nx, ny = pos[0] + dx, pos[1] + dy
        if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] != 1:
            moves.append((nx, ny))
    
    move_cache[cache_key] = moves
    return moves

def minimax_evaluate(ghost_pos, pacman_pos, maze):
    """Optimized evaluation function without A* calls"""
    # Calculate Manhattan distance
    manhattan_dist = abs(ghost_pos[0] - pacman_pos[0]) + abs(ghost_pos[1] - pacman_pos[1])
    
    # Calculate number of possible moves for ghost and Pacman
    ghost_moves = len(minimax_get_possible_moves(ghost_pos, maze))
    pacman_moves = len(minimax_get_possible_moves(pacman_pos, maze))
    
    # Calculate distance to nearest corner
    corners = [(0, 0), (0, len(maze)-1), (len(maze[0])-1, 0), (len(maze[0])-1, len(maze)-1)]
    corner_dist = min(abs(ghost_pos[0] - c[0]) + abs(ghost_pos[1] - c[1]) for c in corners)
    
    # Calculate if ghost is cutting off Pacman's escape routes
    escape_routes = 0
    for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
        nx, ny = pacman_pos[0] + dx, pacman_pos[1] + dy
        if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] != 1:
            ghost_to_route = abs(ghost_pos[0] - nx) + abs(ghost_pos[1] - ny)
            if ghost_to_route < manhattan_dist:
                escape_routes += 1
    
    # Combine factors for evaluation
    score = -manhattan_dist * 2  # Higher weight for distance
    score += (4 - escape_routes) * 30  # Bonus for cutting off escape routes
    score += ghost_moves * 5  # Bonus for having more options
    score -= pacman_moves * 5  # Penalty for Pacman having more options
    score -= corner_dist * 3  # Penalty for being far from corners
    
    return score

def minimax_search(ghost_pos, pacman_pos, maze, depth, alpha, beta, maximizing, start_time, time_limit=0.05):
    """Minimax search with time limit and move ordering"""
    # Check time limit
    if time.time() - start_time > time_limit:
        return minimax_evaluate(ghost_pos, pacman_pos, maze)
        
    if depth == 0:
        return minimax_evaluate(ghost_pos, pacman_pos, maze)

    # Cache key
    cache_key = (ghost_pos, pacman_pos, depth, maximizing)
    if cache_key in minimax_cache:
        return minimax_cache[cache_key]

    if maximizing:
        max_eval = -float('inf')
        # Get and sort moves by evaluation
        moves = minimax_get_possible_moves(ghost_pos, maze)
        moves.sort(key=lambda m: minimax_evaluate(m, pacman_pos, maze), reverse=True)
        
        for move in moves:
            if maze[move[1]][move[0]] != 1:  # Check walkability
                eval = minimax_search(move, pacman_pos, maze, depth - 1, alpha, beta, False, start_time, time_limit)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
        minimax_cache[cache_key] = max_eval
        return max_eval
    else:
        min_eval = float('inf')
        # Get and sort moves by evaluation
        moves = minimax_get_possible_moves(pacman_pos, maze)
        moves.sort(key=lambda m: minimax_evaluate(ghost_pos, m, maze))
        
        for move in moves:
            if maze[move[1]][move[0]] != 1:  # Check walkability
                eval = minimax_search(ghost_pos, move, maze, depth - 1, alpha, beta, True, start_time, time_limit)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
        minimax_cache[cache_key] = min_eval
        return min_eval

def minimax_choose_move(current_pos, pacman_pos, maze, depth=3):
    """Choose the best move using minimax with time limit and caching"""
    start_time = time.time()
    best_score = -float('inf')
    best_move = current_pos
    
    # Get all possible moves
    possible_moves = minimax_get_possible_moves(current_pos, maze)
    
    # Filter out unwalkable moves and last position
    if not hasattr(minimax_choose_move, 'last_pos'):
        minimax_choose_move.last_pos = current_pos
    
    walkable_moves = [move for move in possible_moves 
                     if maze[move[1]][move[0]] != 1 and 
                     move != minimax_choose_move.last_pos]
    
    if not walkable_moves:
        return current_pos
        
    # Sort moves by initial evaluation for better pruning
    walkable_moves.sort(key=lambda m: minimax_evaluate(m, pacman_pos, maze), reverse=True)
    
    # Evaluate each move
    for move in walkable_moves:
        score = minimax_search(move, pacman_pos, maze, depth - 1, -float('inf'), float('inf'), False, start_time)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Update last position
    minimax_choose_move.last_pos = current_pos
            
    # Clear old cache entries periodically
    if len(minimax_cache) > 1000:
        minimax_cache.clear()
    if len(move_cache) > 1000:
        move_cache.clear()
        
    return best_move


# --- Genetic Algorithm for Inky ---
DIRECTIONS = ['up', 'down', 'left', 'right']

class GhostDNA:
    def __init__(self, gene_length=10):
        self.genes = [random.choice(DIRECTIONS) for _ in range(gene_length)]
        self.fitness = 0

    def crossover(self, partner):
        child = GhostDNA(len(self.genes))
        midpoint = random.randint(0, len(self.genes) - 1)
        child.genes = self.genes[:midpoint] + partner.genes[midpoint:]
        return child

    def mutate(self, mutation_rate=0.1):
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                self.genes[i] = random.choice(DIRECTIONS)

class GeneticGhostAI:
    def __init__(self, population_size=20, gene_length=10):
        self.population = [GhostDNA(gene_length) for _ in range(population_size)]
        self.generation = 0
        self.best = self.population[0]  # Initialize best with first individual

    def evaluate(self, evaluate_fn):
        for dna in self.population:
            dna.fitness = evaluate_fn(dna.genes)
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        self.best = self.population[0] if self.population else None

    def evolve(self, mutation_rate=0.1):
        if not self.population:
            return
            
        new_population = [self.best] if self.best else []  # Keep the best one if it exists
        while len(new_population) < len(self.population):
            parent1 = self.select()
            parent2 = self.select()
            child = parent1.crossover(parent2)
            child.mutate(mutation_rate)
            new_population.append(child)
        self.population = new_population
        self.generation += 1

    def select(self):
        total_fitness = sum(dna.fitness for dna in self.population)
        if total_fitness == 0:
            return random.choice(self.population)
        pick = random.uniform(0, total_fitness)
        current = 0
        for dna in self.population:
            current += dna.fitness
            if current > pick:
                return dna

# Fitness function for Inky
def calculate_fitness(path, ghost_pos, pacman_pos, maze):
    score = 0
    x, y = ghost_pos
    last_pos = (x, y)
    escape_routes_cut = 0
    
    for direction in path:
        if direction == 'up' and y > 0 and maze[y - 1][x] == 0:
            y -= 1
        elif direction == 'down' and y < len(maze) - 1 and maze[y + 1][x] == 0:
            y += 1
        elif direction == 'left' and x > 0 and maze[y][x - 1] == 0:
            x -= 1
        elif direction == 'right' and x < len(maze[0]) - 1 and maze[y][x + 1] == 0:
            x += 1
            
        # Reward approaching Pac-Man
        distance = abs(x - pacman_pos[0]) + abs(y - pacman_pos[1])
        score += 1 / (distance + 1)
        
        # Reward cutting off escape routes
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = pacman_pos[0] + dx, pacman_pos[1] + dy
            if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] == 0:
                ghost_to_route = abs(x - nx) + abs(y - ny)
                if ghost_to_route < distance:
                    escape_routes_cut += 1
        
        # Penalize moving back and forth
        if (x, y) == last_pos:
            score -= 0.5
            
        last_pos = (x, y)
    
    # Add bonus for cutting off escape routes
    score += escape_routes_cut * 2
    
    return score