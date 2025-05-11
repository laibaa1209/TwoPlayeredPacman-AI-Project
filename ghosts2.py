import pygame
import random
from search_agents import bfs, astar, minimax_choose_move, minimax_get_possible_moves, GeneticGhostAI, calculate_fitness

# Constants for genetic algorithm
DIRECTIONS = ['up', 'down', 'left', 'right']

class Ghost:
    def __init__(self, id, x, y, frames, tile_size, maze, gate):
        self.id = id
        self.x = x
        self.y = y
        self.tile_size = tile_size
        self.frames = frames
        self.rect = pygame.Rect(self.x * tile_size, self.y * tile_size, tile_size, tile_size)
        self.maze = maze
        self.gate = gate

        self.has_escaped = False
        self.bump_count = 0
        self.speed = 2.0  # Increased speed
        self.direction_name = 'down'
        self.current_frame = 0
        self.frame_counter = 0
        self.move_delay = 8
        self.move_timer = 0
        self.can_move = True
        self.alive = True
        self.path = []  # Store current path

        self.trained_path = []
        if self.id == 4:
            try:
                with open("trained_clyde_path.txt", "r") as f:
                    self.trained_path = eval(f.read())
            except FileNotFoundError:
                print("Trained path not found. Using smart movement.")

    def update_maze(self, new_maze):
        """Update maze and handle collisions/pellets"""
        self.maze = new_maze
        # Clear current path to force recalculation with new maze
        self.path = []
        # Verify current position is still valid
        current_pos = self.tile_position()
        if not self.is_walkable(current_pos[0], current_pos[1]):
            # Find nearest walkable position
            for y in range(len(self.maze)):
                for x in range(len(self.maze[0])):
                    if self.is_walkable(x, y):
                        self.rect.centerx = x * self.tile_size + self.tile_size // 2
                        self.rect.centery = y * self.tile_size + self.tile_size // 2
                        break

    def tile_position(self):
        """Get current tile coordinates based on center position"""
        return (round(self.rect.centerx / self.tile_size), 
                round(self.rect.centery / self.tile_size))

    def draw(self, surface):
        sprite = self.frames[self.direction_name][self.current_frame]
        sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
        surface.blit(sprite, self.rect.topleft)

    def is_walkable(self, x, y):
        """Check if a tile is walkable"""
        if x < 0 or y < 0 or x >= len(self.maze[0]) or y >= len(self.maze):
            return False
            
        # Get gate tile position
        gate_tile = (self.gate.gate_rect.centerx // self.tile_size, 
                    self.gate.gate_rect.centery // self.tile_size)
        
        # Allow ghosts to pass through gate tiles
        if (x, y) == gate_tile:
            return True
            
        return self.maze[y][x] != 1  # 1 means wall, anything else is walkable

    def update(self, ghosts, pacman_positions):
        """Update ghost state and movement"""
        if not self.alive:
            return

        # Update animation
        self.frame_counter += 1
        if self.frame_counter >= 5:
            self.frame_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames[self.direction_name])

        # Update position
        self.x = self.rect.centerx // self.tile_size
        self.y = self.rect.centery // self.tile_size

        # Movement logic
        if not self.has_escaped:
            self.escape_cage()
        else:
            self.chase_pacman(pacman_positions, ghosts)

    def escape_cage(self):
        """Escape logic with improved movement"""
        gate_tile = (self.gate.gate_rect.centerx // self.tile_size, 
                    self.gate.gate_rect.centery // self.tile_size)

        # Attack gate if not broken
        if not self.gate.broken:
            gate_hitbox = self.gate.gate_rect.inflate(6, 6)
            if gate_hitbox.collidepoint(self.rect.center):
                self.gate.hit()
                self.gate.flicker_timer = 10
                return

        # Use A* to find path to gate
        current_pos = self.tile_position()
        if not self.path:
            self.path = astar(current_pos, gate_tile, self.maze)
            if not self.path:
                # If no path found, try direct movement
                dx = gate_tile[0] - current_pos[0]
                dy = gate_tile[1] - current_pos[1]
                if abs(dx) > abs(dy):
                    self.rect.centerx += self.speed * (1 if dx > 0 else -1)
                    self.direction_name = 'right' if dx > 0 else 'left'
                else:
                    self.rect.centery += self.speed * (1 if dy > 0 else -1)
                    self.direction_name = 'down' if dy > 0 else 'up'
                return

        # Move along path
        if self.path:
            next_pos = self.path[0]
            target_x = next_pos[0] * self.tile_size + self.tile_size // 2
            target_y = next_pos[1] * self.tile_size + self.tile_size // 2
            
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            
            if abs(dx) > abs(dy):
                self.rect.centerx += self.speed * (1 if dx > 0 else -1)
                self.direction_name = 'right' if dx > 0 else 'left'
            else:
                self.rect.centery += self.speed * (1 if dy > 0 else -1)
                self.direction_name = 'down' if dy > 0 else 'up'
            
            # Check if reached next position
            if (abs(self.rect.centerx - target_x) < self.speed and 
                abs(self.rect.centery - target_y) < self.speed):
                self.rect.center = (target_x, target_y)
                self.path.pop(0)
                
                # Check if reached gate
                if self.tile_position() == gate_tile and self.gate.broken:
                    self.has_escaped = True
                    print(f"Ghost {self.id} has escaped!")

    def choose_target(self, player1_pos, player2_pos, current_pos, all_ghosts=None):
        """Each ghost targets a specific Pacman with improved targeting after kills"""
        # Handle dead pacman cases
        if player1_pos == (-1, -1) and player2_pos == (-1, -1):
            # Both Pacmans are dead, choose random walkable position
            walkable_positions = []
            for y in range(len(self.maze)):
                for x in range(len(self.maze[0])):
                    if self.is_walkable(x, y):
                        walkable_positions.append((x, y))
            return random.choice(walkable_positions) if walkable_positions else current_pos

        # Each ghost has a specific targeting strategy
        if self.id == 1:  # Pinky - uses BFS
            # If one Pacman is dead, target the other one
            if player1_pos == (-1, -1):
                return player2_pos
            if player2_pos == (-1, -1):
                return player1_pos
            # If both alive, target Pacman 1 (yellow)
            return player1_pos

        elif self.id == 2:  # Blinky - uses A*
            # If one Pacman is dead, target the other one
            if player1_pos == (-1, -1):
                return player2_pos
            if player2_pos == (-1, -1):
                return player1_pos
            # If both alive, target Pacman 2 (blue)
            return player2_pos

        elif self.id == 3:  # Clyde - uses Minimax
            # If one Pacman is dead, target the other one
            if player1_pos == (-1, -1):
                return player2_pos
            if player2_pos == (-1, -1):
                return player1_pos
            # If both alive, target the Pacman that's further away
            dist_to_p1 = abs(current_pos[0] - player1_pos[0]) + abs(current_pos[1] - player1_pos[1])
            dist_to_p2 = abs(current_pos[0] - player2_pos[0]) + abs(current_pos[1] - player2_pos[1])
            return player1_pos if dist_to_p1 >= dist_to_p2 else player2_pos

        elif self.id == 4:  # Inky - uses Genetic Algorithm
            # If one Pacman is dead, target the other one
            if player1_pos == (-1, -1):
                return player2_pos
            if player2_pos == (-1, -1):
                return player1_pos
            # If both alive, target the Pacman that's closer
            dist_to_p1 = abs(current_pos[0] - player1_pos[0]) + abs(current_pos[1] - player1_pos[1])
            dist_to_p2 = abs(current_pos[0] - player2_pos[0]) + abs(current_pos[1] - player2_pos[1])
            return player1_pos if dist_to_p1 <= dist_to_p2 else player2_pos

    def chase_pacman(self, pacman_positions, all_ghosts=None):
        """Each ghost uses its specific algorithm without fallbacks"""
        try:
            player1_pos, player2_pos = pacman_positions
            current_pos = self.tile_position()
            
            # Choose target based on ghost's strategy
            target = self.choose_target(player1_pos, player2_pos, current_pos, all_ghosts)
            
            # Each ghost uses its specific algorithm
            if self.id == 1:  # Pinky - uses BFS
                target = self.get_pinky_target(target)
                if not self.path:
                    # Try BFS up to 3 times before falling back
                    for attempt in range(3):
                        self.path = bfs(current_pos, target, self.maze)
                        if self.path:
                            break
                        print(f"Pinky (Ghost {self.id}) BFS attempt {attempt + 1} failed, retrying...")
                    if not self.path:
                        print(f"Pinky (Ghost {self.id}) falling back to smart random move - All BFS attempts failed")
                        self.path = [self.smart_random_move(current_pos, target)]
                
            elif self.id == 2:  # Blinky - uses A*
                if not self.path:
                    # Try A* up to 3 times before falling back
                    for attempt in range(3):
                        self.path = astar(current_pos, target, self.maze)
                        if self.path:
                            break
                        print(f"Blinky (Ghost {self.id}) A* attempt {attempt + 1} failed, retrying...")
                    if not self.path:
                        print(f"Blinky (Ghost {self.id}) falling back to smart random move - All A* attempts failed")
                        self.path = [self.smart_random_move(current_pos, target)]
                
            elif self.id == 3:  # Clyde - uses Minimax
                if not self.path:
                    try:
                        # Try Minimax up to 3 times before falling back
                        for attempt in range(3):
                            possible_moves = minimax_get_possible_moves(current_pos, self.maze)
                            if possible_moves:
                                best_move = minimax_choose_move(current_pos, target, self.maze, depth=4)
                                
                                if best_move == current_pos:
                                    print(f"Clyde (Ghost {self.id}) Minimax attempt {attempt + 1} returned current position, retrying...")
                                    continue
                                    
                                if best_move and best_move != current_pos and self.is_walkable(best_move[0], best_move[1]):
                                    self.path = [best_move]
                                    break
                                else:
                                    print(f"Clyde (Ghost {self.id}) Minimax attempt {attempt + 1} invalid move, retrying...")
                                    # Try alternative moves
                                    for move in possible_moves:
                                        if move != current_pos and self.is_walkable(move[0], move[1]):
                                            self.path = [move]
                                            break
                                    if self.path:
                                        break
                    except Exception as e:
                        print(f"Clyde (Ghost {self.id}) falling back to smart random move - Minimax error: {str(e)}")
                        self.path = [self.smart_random_move(current_pos, target)]
                        
            elif self.id == 4:  # Inky - uses Genetic Algorithm
                if not self.path:
                    try:
                        # Create genetic AI instance if not exists
                        if not hasattr(self, 'genetic_ai'):
                            self.genetic_ai = GeneticGhostAI()
                        
                        # Try Genetic Algorithm up to 3 times before falling back
                        for attempt in range(3):
                            def evaluate_path(genes):
                                return calculate_fitness(genes, current_pos, target, self.maze)
                            
                            self.genetic_ai.evaluate(evaluate_path)
                            self.genetic_ai.evolve()
                            
                            if self.genetic_ai.best and hasattr(self.genetic_ai.best, 'genes'):
                                direction = self.genetic_ai.best.genes[0]
                                dx, dy = 0, 0
                                if direction == 'up':
                                    dy = -1
                                elif direction == 'down':
                                    dy = 1
                                elif direction == 'left':
                                    dx = -1
                                elif direction == 'right':
                                    dx = 1
                                
                                next_pos = (current_pos[0] + dx, current_pos[1] + dy)
                                if self.is_walkable(next_pos[0], next_pos[1]):
                                    self.path = [next_pos]
                                    break
                                else:
                                    print(f"Inky (Ghost {self.id}) Genetic attempt {attempt + 1} invalid move, retrying...")
                            else:
                                print(f"Inky (Ghost {self.id}) Genetic attempt {attempt + 1} no valid solution, retrying...")
                        else:
                            print(f"Inky (Ghost {self.id}) falling back to smart random move - All Genetic attempts failed")
                            self.path = [self.smart_random_move(current_pos, target)]
                    except Exception as e:
                        print(f"Inky (Ghost {self.id}) falling back to smart random move - Genetic algorithm error: {str(e)}")
                        self.path = [self.smart_random_move(current_pos, target)]
            
            # Move along path for all ghosts
            if self.path:
                next_pos = self.path[0]
                target_x = next_pos[0] * self.tile_size + self.tile_size // 2
                target_y = next_pos[1] * self.tile_size + self.tile_size // 2
                
                dx = target_x - self.rect.centerx
                dy = target_y - self.rect.centery
                
                # Check if next position would be walkable before moving
                next_x = self.rect.centerx + self.speed * (1 if dx > 0 else -1)
                next_y = self.rect.centery + self.speed * (1 if dy > 0 else -1)
                next_tile = (round(next_x / self.tile_size), round(next_y / self.tile_size))
                
                if self.is_walkable(next_tile[0], next_tile[1]):
                    if abs(dx) > abs(dy):
                        self.rect.centerx += self.speed * (1 if dx > 0 else -1)
                        self.direction_name = 'right' if dx > 0 else 'left'
                    else:
                        self.rect.centery += self.speed * (1 if dy > 0 else -1)
                        self.direction_name = 'down' if dy > 0 else 'up'
                
                # Check if reached next position
                if (abs(self.rect.centerx - target_x) < self.speed and 
                    abs(self.rect.centery - target_y) < self.speed):
                    self.rect.center = (target_x, target_y)
                    self.path.pop(0)
                
                # Verify we haven't moved into a wall
                new_pos = self.tile_position()
                if not self.is_walkable(new_pos[0], new_pos[1]):
                    # Revert to last valid position
                    self.rect.centerx = current_pos[0] * self.tile_size + self.tile_size // 2
                    self.rect.centery = current_pos[1] * self.tile_size + self.tile_size // 2
                    self.path = []  # Clear path to force recalculation

        except Exception as e:
            print(f"Error in chase_pacman for ghost {self.id}: {str(e)}")
            # No fallback movement - just clear the path
            self.path = []

    def get_pinky_target(self, pacman_pos):
        """Calculate Pinky's target 4 tiles ahead of Pac-Man"""
        # Get the direction Pacman is moving based on the last two positions
        if not hasattr(self, 'last_pacman_pos'):
            self.last_pacman_pos = pacman_pos
            return pacman_pos
        
        dx = pacman_pos[0] - self.last_pacman_pos[0]
        dy = pacman_pos[1] - self.last_pacman_pos[1]
        
        # If Pacman is not moving, use current position
        if dx == 0 and dy == 0:
            return pacman_pos
        
        # Calculate target 4 tiles ahead in the direction of movement
        target = (pacman_pos[0] + dx * 4, pacman_pos[1] + dy * 4)
        
        # If target is not walkable, try adjacent tiles
        if not self.is_walkable(target[0], target[1]):
            # Try perpendicular directions
            if dx != 0:  # Moving horizontally
                if self.is_walkable(target[0], target[1] + 1):
                    target = (target[0], target[1] + 1)
                elif self.is_walkable(target[0], target[1] - 1):
                    target = (target[0], target[1] - 1)
            else:  # Moving vertically
                if self.is_walkable(target[0] + 1, target[1]):
                    target = (target[0] + 1, target[1])
                elif self.is_walkable(target[0] - 1, target[1]):
                    target = (target[0] - 1, target[1])
        
        self.last_pacman_pos = pacman_pos
        return target

    def smart_random_move(self, pos, pacman_pos):
        """Move randomly but biased toward Pac-Man"""
        directions = [(0,1),(1,0),(0,-1),(-1,0)]
        valid_moves = []
        
        # Calculate distance to Pac-Man
        current_dist = abs(pos[0]-pacman_pos[0]) + abs(pos[1]-pacman_pos[1])
        
        for dx, dy in directions:
            nx, ny = pos[0]+dx, pos[1]+dy
            if self.is_walkable(nx, ny):
                # Calculate new distance to Pac-Man
                new_dist = abs(nx-pacman_pos[0]) + abs(ny-pacman_pos[1])
                
                # Weight moves that get closer to Pac-Man more heavily
                if new_dist < current_dist:
                    weight = 4  # Higher weight for moves that get closer
                else:
                    weight = 1  # Lower weight for other moves
                
                valid_moves.extend([(nx, ny)] * weight)
                
        return random.choice(valid_moves) if valid_moves else pos

    def reset(self):
        """Reset ghost to initial state"""
        self.rect.x = self.x * self.tile_size
        self.rect.y = self.y * self.tile_size
        self.has_escaped = False
        self.path = []
        self.direction_name = 'down'
        self.current_frame = 0
        self.frame_counter = 0
        self.move_delay = 0
        self.move_timer = 0
        self.can_move = True
        self.alive = True
        if hasattr(self, 'genetic_ai'):
            delattr(self, 'genetic_ai')