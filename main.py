import pygame
import random
import math
from scoreboard import Scoreboard
from player import Player
from ghosts2 import Ghost  # Updated import to match the new ghosts.py file
from gate import Gate
from collections import deque
from pygame import mixer
from frontpage import front_page
from gameover import game_over_screen
import sys
from sprite import load_sprite_sheet
import json
import os

# Cage settings

CAGE_COLOR = (0, 200, 255)  # Light blue for boundaries
GATE_COLOR = (255, 255, 255)
CAGE_RECT = pygame.Rect(180, 220, 160, 100)  # x, y, width, height
GATE_Y = CAGE_RECT.y + CAGE_RECT.height - 2
GATE_HIT_LIMIT = 4
TELEPORTERS = {  # Define teleporter pairs (x1, y1): (x2, y2)
    (2, 2): (18, 18),
    (18, 2): (2, 18)
    }
gate_hits = 0
gate_broken = False
gate_disturb_timer = 0
ghosts_escaped = 0
consumed_pellets = set()

# Maze and tile settings
ROWS, COLS = 21, 21
TILE = 25
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE

# Scoreboard and main window settings
SCOREBOARD_HEIGHT = 60  # Height for scoreboard at top
MAIN_WIDTH = WIDTH
MAIN_HEIGHT = HEIGHT + SCOREBOARD_HEIGHT

# Create the main screen with space for scoreboard
screen = pygame.display.set_mode((MAIN_WIDTH, MAIN_HEIGHT))
pygame.display.set_caption("Pac-Man")

# Create separate surfaces for maze and scoreboard
maze_surface = pygame.Surface((WIDTH, HEIGHT))
scoreboard_surface = pygame.Surface((WIDTH, SCOREBOARD_HEIGHT))

# Load sprites
pacman_right, pacman2_right, ghost_frames = load_sprite_sheet()

# Initialize scoreboard with the scoreboard surface
scoreboard = Scoreboard(scoreboard_surface)

# Function to load high score
def load_high_score():
    try:
        if os.path.exists('highscore.json'):
            with open('highscore.json', 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
    except:
        pass
    return 0

# Function to save high score
def save_high_score(score):
    try:
        data = {'high_score': score}
        with open('highscore.json', 'w') as f:
            json.dump(data, f)
    except:
        pass

# Load initial high score
high_score = load_high_score()

def handle_teleporters(entity):
    for (x1, y1), (x2, y2) in TELEPORTERS.items():
        if entity.x == x1 and entity.y == y1:
            entity.x, entity.y = x2, y2
        elif entity.x == x2 and entity.y == y2:
            entity.x, entity.y = x1, y1

def reserve_ghost_box():
    # Calculating the center of the maze to place the ghost cage
    mid_r, mid_c = ROWS // 2, COLS // 2
    for r in range(mid_r - 1, mid_r + 2):
        for c in range(mid_c - 2, mid_c + 3):
            maze[r][c] = 0  # Make it a path (not wall)

def draw_ghost_cage():
    # Coordinates
    mid_r, mid_c = ROWS // 2, COLS // 2
    top = (mid_r - 1) * TILE
    bottom = (mid_r + 2) * TILE
    left = (mid_c - 2) * TILE
    right = (mid_c + 3) * TILE

    GATE_TILES = (CAGE_MID_ROW + 2, CAGE_MID_COL)

    # Mark cage walls as impassable (maze[y][x] = 2 for walls)
    for r in range(mid_r - 1, mid_r + 3):  # Top and Bottom walls
        maze[r][mid_c - 2] = 2  # Left wall
        maze[r][mid_c + 3] = 2  # Right wall
    for c in range(mid_c - 2, mid_c + 4):  # Left and Right walls
        maze[mid_r - 1][c] = 2  # Top wall
        maze[mid_r + 2][c] = 2  # Bottom wall

    # Cage boundaries (visual representation)
    pygame.draw.line(maze_surface, CAGE_COLOR, (left, top), (right, top), 2)    # Top
    pygame.draw.line(maze_surface, CAGE_COLOR, (left, bottom), (right, bottom), 2)  # Bottom
    pygame.draw.line(maze_surface, CAGE_COLOR, (left, top), (left, bottom), 2)   # Left
    pygame.draw.line(maze_surface, CAGE_COLOR, (right, top), (right, bottom), 2) # Right

    # Draw gate only if not broken and tile is a path
    gate_tile_r, gate_tile_c = GATE_TILES
    if maze[gate_tile_r][gate_tile_c] == 0:  # Gate is walkable
        gate_x = gate_tile_c * TILE
        gate_y = gate_tile_r * TILE
        flicker_color = GATE_COLOR
        pygame.draw.line(maze_surface, flicker_color, (gate_x, gate_y), (gate_x + TILE, gate_y), 2)

def remove_dead_ends(iterations=30):
    for _ in range(iterations):
        for r in range(1, ROWS-1):
            for c in range(1, COLS-1):
                if maze[r][c] == 0:
                    neighbors = [(r+1, c), (r-1, c), (r, c+1), (r, c-1)]
                    walls = [maze[nr][nc] for nr, nc in neighbors]
                    if walls.count(1) == 3:  # It's a dead end
                        random.shuffle(neighbors)
                        for nr, nc in neighbors:
                            if maze[nr][nc] == 1:
                                maze[nr][nc] = 0
                                break

def generate_maze(r, c):
    maze[r][c] = 0
    dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
    random.shuffle(dirs)

    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] == 1:
            maze[r + dr // 2][c + dc // 2] = 0
            generate_maze(nr, nc)

def regenerate_maze():
    mid_r, mid_c = ROWS // 2, COLS // 2
    global maze, pellets
    maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]
    
    # Generate maze first
    generate_maze(1, 1)
    
    # Then reserve ghost box
    reserve_ghost_box()
    
    # Remove dead ends
    remove_dead_ends(50)
    
    # Draw ghost cage last
    draw_ghost_cage()
    
    # Initialize pellets
    pellets = set((r, c) for r in range(ROWS) for c in range(COLS) if maze[r][c] == 0)
    pellets -= consumed_pellets
    for r, c in CAGE_TILES:
        pellets.discard((r, c))
    pellets.discard(GATE_TILE)

def find_nearest_valid_position(maze, start_x, start_y):
    """Find the nearest valid position in the maze."""
    queue = deque([(start_x, start_y)])
    visited = set([(start_x, start_y)])

    while queue:
        x, y = queue.popleft()

        # Check if the current tile is walkable
        if maze[y][x] == 0:
            return (x, y)

        # Explore neighboring tiles
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and (nx, ny) and maze[nx][ny] == 0 not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))

    # Fallback: If no valid position is found, return the start position
    return (start_x, start_y)

def draw_pellets():
    for r, c in pellets:
        pygame.draw.circle(maze_surface, (255, 255, 255), (c * TILE + TILE // 2, r * TILE + TILE // 2), 3)

# Main function:
CAGE_MID_ROW = ROWS // 2
CAGE_MID_COL = COLS // 2
CAGE_WIDTH = 5
CAGE_HEIGHT = 3
CAGE_TILES = [
    (r, c)
    for r in range(CAGE_MID_ROW - 1, CAGE_MID_ROW + 2)
    for c in range(CAGE_MID_COL - 2, CAGE_MID_COL + 3)
]

FOG_COLOR = (0, 0, 0, 150)  # Semi-transparent black
VISION_RADIUS = 5 * TILE  # Radius of visible area

def draw_fog_of_vision():
    fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fog_surface.fill(FOG_COLOR)

    # Clear a circle around Player 1
    pygame.draw.circle(fog_surface, (0, 0, 0, 0), (player1.x * TILE + TILE // 2, player1.y * TILE + TILE // 2), VISION_RADIUS)

    # Clear a circle around Player 2
    pygame.draw.circle(fog_surface, (0, 0, 0, 0), (player2.x * TILE + TILE // 2, player2.y * TILE + TILE // 2), VISION_RADIUS)

    maze_surface.blit(fog_surface, (0, 0))

gate_tile_x = WIDTH // 2
gate_tile_y = HEIGHT // 2 + 2  # Example

pygame.init()
mixer.init()

# Initialize sound
try:
    # Initialize mixer with better settings
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    
    # Load and set up chomp sound with lower volume
    chomp_sound = mixer.Sound('AI-PROJECT-25/sound/pacman_chomp.wav')
    chomp_sound.set_volume(0.05)  # Significantly reduced volume to prevent distortion
    
    # Load beginning sound but don't play it here
    beginning_sound = mixer.Sound('AI-PROJECT-25/sound/pacman_beginning.wav')
    beginning_sound.set_volume(0.2)
except Exception as e:
    print(f"Error loading sounds: {e}")
    chomp_sound = None
    beginning_sound = None

# Initialize all walls
maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]

# Show front page first
if not front_page(high_score):
    pygame.quit()
    sys.exit()

# Start maze generation from (1, 1)
generate_maze(1, 1)
reserve_ghost_box()
remove_dead_ends(50)  # You can tweak the number for more/less loops
draw_ghost_cage()

gate = Gate(maze_surface, maze, TILE)
GATE_TILE = (CAGE_MID_ROW + 2, CAGE_MID_COL)
maze[GATE_TILE[0]][GATE_TILE[1]] = 0  # Make sure it's path

# Initialize pellets
pellets = set((r, c) for r in range(ROWS) for c in range(COLS) if maze[r][c] == 0)
# Exclude ghost cage and gate tiles
for r, c in CAGE_TILES:
    pellets.discard((r, c))
pellets.discard(GATE_TILE)

# Players - Start further from the cage
player1 = Player(3, 3, pacman_right, maze, TILE, {
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT
}, pellets)
player1.chomp_sound = chomp_sound  # Pass the sound to player1

player2 = Player(COLS - 4, ROWS - 4, pacman2_right, maze, TILE, {
    'up': pygame.K_w,
    'down': pygame.K_s,
    'left': pygame.K_a,
    'right': pygame.K_d
}, pellets)
player2.chomp_sound = chomp_sound  # Pass the sound to player2

cage_barrier_broken = {
    "broken": False,
    "hits": 0,
    "escaped_count": 0,
    "escape_cooldown": 0  # frames before next ghost escapes
}

# Initialize ghosts with updated Ghost class
ghosts = [
    Ghost(2, COLS // 2 , ROWS // 2, ghost_frames['blinky'], TILE, maze, gate),  # Updated to use the new Ghost class
    Ghost(4, COLS // 2-1, ROWS // 2, ghost_frames['inky'], TILE, maze, gate),
    Ghost(1, COLS // 2+1, ROWS // 2, ghost_frames['pinky'], TILE, maze, gate),
    Ghost(3, int(COLS // 2-1.7), int(ROWS // 2-0.75) , ghost_frames['clyde'], TILE, maze, gate)
]

center_x = len(maze[0]) // 2
center_y = len(maze) // 2 + 1  # One row below cage center

# Define gate rectangle (adjust width/height if needed)
gate_rect = pygame.Rect(center_x * TILE, center_y * TILE, TILE, TILE)
for ghost in ghosts:
        ghost.gate_rect = gate_rect  # Set this to the correct Rect

def draw(surface):
    # Draw maze walls and paths
    for y in range(ROWS):
        for x in range(COLS):
            color = (0, 0, 255) if maze[y][x] == 1 else (0, 0, 0)
            pygame.draw.rect(surface, color, (x*TILE, y*TILE, TILE, TILE))
    
    draw_pellets()
    draw_ghost_cage()
    player1.draw(surface)
    player2.draw(surface)
    for ghost in ghosts:
        ghost.draw(surface)

run = True
clock = pygame.time.Clock()

while run:
    clock.tick(60)  # Increased from 30 to 60 FPS for smoother gameplay
    
    keys = pygame.key.get_pressed()
    
    if not pygame.key.get_focused():
        continue
    
    # Store player and ghost positions
    stored_player1_pos = (player1.x, player1.y)
    stored_player2_pos = (player2.x, player2.y)
    stored_ghost_positions = [(ghost.x, ghost.y) for ghost in ghosts]
    
    # CHECKING COLLISIONS
    player1.check_ghost_collision(ghosts)
    player2.check_ghost_collision(ghosts)
    
    # Update scoreboard with current scores and lives
    scoreboard.update_scores(player1.score, player2.score)
    scoreboard.update_lives(player1.lives, player2.lives)
    
    # Check for game over conditions
    if not player1.alive and not player2.alive:
        # Both players are dead: Ghost wins
        winner = "Tie"
        if game_over_screen(winner, player1.score, player2.score):
            # Reset game state
            player1 = Player(3, 3, pacman_right, maze, TILE, {
                'up': pygame.K_UP,
                'down': pygame.K_DOWN,
                'left': pygame.K_LEFT,
                'right': pygame.K_RIGHT
            }, pellets)
            
            player2 = Player(COLS - 4, ROWS - 4, pacman2_right, maze, TILE, {
                'up': pygame.K_w,
                'down': pygame.K_s,
                'left': pygame.K_a,
                'right': pygame.K_d
            }, pellets)
            
            # Reset ghosts
            ghosts = [
                Ghost(2, COLS // 2, ROWS // 2, ghost_frames['blinky'], TILE, maze, gate),
                Ghost(4, COLS // 2-1, ROWS // 2, ghost_frames['inky'], TILE, maze, gate),
                Ghost(1, COLS // 2+1, ROWS // 2, ghost_frames['pinky'], TILE, maze, gate),
                Ghost(3, int(COLS // 2-1.7), int(ROWS // 2-0.75), ghost_frames['clyde'], TILE, maze, gate)
            ]
            
            # Reset pellets
            pellets = set((r, c) for r in range(ROWS) for c in range(COLS) if maze[r][c] == 0)
            for r, c in CAGE_TILES:
                pellets.discard((r, c))
            pellets.discard(GATE_TILE)
            
            # Reset scoreboard
            scoreboard = Scoreboard(scoreboard_surface)
            continue
    # Check if all pellets are eaten
    elif len(pellets) == 0:
        # Both players alive, compare scores
        if player1.score > player2.score:
            winner = "Player 1"
            if player1.score > high_score:
                high_score = player1.score
                save_high_score(high_score)
        elif player2.score > player1.score:
            winner = "Player 2"
            if player2.score > high_score:
                high_score = player2.score
                save_high_score(high_score)
        else:
            winner = "Tie"
        if game_over_screen(winner, player1.score, player2.score):
            # Reset pellets
            pellets = set((r, c) for r in range(ROWS) for c in range(COLS) if maze[r][c] == 0)
            for r, c in CAGE_TILES:
                pellets.discard((r, c))
            pellets.discard(GATE_TILE)
            # Reset game state
            player1 = Player(3, 3, pacman_right, maze, TILE, {
                'up': pygame.K_UP,
                'down': pygame.K_DOWN,
                'left': pygame.K_LEFT,
                'right': pygame.K_RIGHT
            }, pellets)
            
            player2 = Player(COLS - 4, ROWS - 4, pacman2_right, maze, TILE, {
                'up': pygame.K_w,
                'down': pygame.K_s,
                'left': pygame.K_a,
                'right': pygame.K_d
            }, pellets)
            
            # Reset ghosts
            ghosts = [
                Ghost(2, COLS // 2, ROWS // 2, ghost_frames['blinky'], TILE, maze, gate),
                Ghost(4, COLS // 2-1, ROWS // 2, ghost_frames['inky'], TILE, maze, gate),
                Ghost(1, COLS // 2+1, ROWS // 2, ghost_frames['pinky'], TILE, maze, gate),
                Ghost(3, int(COLS // 2-1.7), int(ROWS // 2-0.75), ghost_frames['clyde'], TILE, maze, gate)
            ]
            # Reset scoreboard
            scoreboard = Scoreboard(scoreboard_surface)
            continue
    
    if pygame.time.get_ticks() % 30000 < 1000:  # Regenerate every 30 seconds
        # Store current scores and lives
        player1_score = player1.score
        player2_score = player2.score
        player1_lives = player1.lives
        player2_lives = player2.lives
        
        regenerate_maze()
        # Players
        player1.update_maze(maze)
        player2.update_maze(maze)   

        for ghost in ghosts:
            ghost.update_maze(maze)

        # Restore scores and lives
        player1.score = player1_score
        player2.score = player2_score
        player1.lives = player1_lives
        player2.lives = player2_lives
        
        # Reposition players
        player1.x, player1.y = find_nearest_valid_position(maze, *stored_player1_pos)
        player2.x, player2.y = find_nearest_valid_position(maze, *stored_player2_pos)
        
        # Reposition ghosts
        for i, ghost in enumerate(ghosts):
            ghost.x, ghost.y = find_nearest_valid_position(maze, *stored_ghost_positions[i])
    
    # Handle teleporters
    handle_teleporters(player1)
    handle_teleporters(player2)
    for ghost in ghosts:
        handle_teleporters(ghost)
    
    # Update player positions
    player1.move(keys, (player2.x, player2.y))
    player2.move(keys, (player1.x, player1.y))
    
    player1.update()
    player2.update()
    
    player1.eat_pellet(consumed_pellets)
    player2.eat_pellet(consumed_pellets)
    
    # Update ghosts
    for ghost in ghosts:
        pacman_positions = [(player1.x, player1.y), (player2.x, player2.y)]
        ghost.update(ghosts, pacman_positions)
    
    gate.update_gate_visuals()
    
    # Draw everything
    screen.fill((0, 0, 0))
    
    # Draw maze on maze surface
    maze_surface.fill((0, 0, 0))
    draw(maze_surface)
    
    # Draw scoreboard on scoreboard surface
    scoreboard_surface.fill((0, 0, 0))
    scoreboard.draw_scoreboard()
    
    # Blit both surfaces to the main screen
    screen.blit(scoreboard_surface, (0, 0))  # Scoreboard at top
    screen.blit(maze_surface, (0, SCOREBOARD_HEIGHT))  # Maze below scoreboard
    
    pygame.display.update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

pygame.quit()