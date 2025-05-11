import pygame
from pygame import mixer

# Global sound object
chomp_sound = None

class Player:
    def __init__(self, x, y, frames, maze, tile_size, keys, pellets):
        # Basic properties
        self.x = x
        self.y = y
        self.frames = frames  # Sprites for each direction
        self.tile_size = tile_size
        self.maze = maze  # Maze structure (walls and paths)
        self.keys = keys  # Key controls for movement
        self.pellets = pellets  # Set of available pellets
        self.chomp_sound = None  # Will be set by main game

        # Animation control
        self.frame_delay = 5  # How fast the animation changes
        self.frame_timer = 0
        self.current_frame = 0

        # Movement control
        self.move_delay = 6  # Increased from 4 to 6 for slower movement
        self.move_timer = 0
        self.can_move = True
        self.target_x = x * tile_size  # For smooth movement
        self.target_y = y * tile_size
        self.current_x = x * tile_size
        self.current_y = y * tile_size
        self.move_speed = 1  # Reduced from 2 to 1 for smoother, slower movement

        # Gameplay state
        self.direction = 'right'  # Start facing right
        self.score = 0
        self.alive = True
        self.lives = 3
        self.is_dying = False
        self.death_timer = 0
        self.death_animation_frames = 8  # Number of frames in death animation
        self.respawn_timer = 0
        self.respawn_delay = 90  # Reduced from 150 to 90 frames (3 seconds at 30 FPS)
        self.start_x = x  # Store starting position
        self.start_y = y

        # Power-up mode
        self.power_up = False
        self.power_up_timer = 0
        
        # Pellet eating control
        self.pellet_eat_timer = 0
        self.pellet_eat_delay = 1  # Reduced from 2 to 1 frame for more responsive pellet eating

    def update_maze(self, new_maze):
        self.maze = new_maze

    def update_pellets(self, pellets):
        self.pellets = pellets

    def eat_pellet(self, consumed_pellets):
        """Check if the player is on a pellet, eat it, and update score."""
        if (self.y, self.x) in self.pellets:
            self.pellets.remove((self.y, self.x))
            consumed_pellets.add((self.y, self.x))
            self.score += 10  # Add points for eating a pellet
            self.frame_delay = 3  # Temporarily speed up animation
            
            # Play chomp sound for each pellet
            if self.chomp_sound:
                # Stop any currently playing chomp sound
                self.chomp_sound.stop()
                # Play the sound once
                self.chomp_sound.play()
            
            pygame.time.set_timer(pygame.USEREVENT, 500)  # Restore normal speed after 500ms

    def move(self, keys_pressed, other_player_pos):
        """Move the player based on key input and maze walls."""
        # Don't move if player is dead or dying
        if not self.alive or self.is_dying or self.respawn_timer > 0:
            return

        # Update movement timer
        if not self.can_move:
            self.move_timer += 1
            if self.move_timer >= self.move_delay:
                self.move_timer = 0
                self.can_move = True
            return

        dx, dy = 0, 0  # Default movement: no movement

        # Handle input
        if keys_pressed[self.keys['up']]:
            dy = -1
            self.direction = 'up'
        elif keys_pressed[self.keys['down']]:
            dy = 1
            self.direction = 'down'
        elif keys_pressed[self.keys['left']]:
            dx = -1
            self.direction = 'left'
        elif keys_pressed[self.keys['right']]:
            dx = 1
            self.direction = 'right'

        # Calculate new position
        new_x = self.x + dx
        new_y = self.y + dy

        # Check boundaries and avoid the other player
        if (0 <= new_y < len(self.maze) and
            0 <= new_x < len(self.maze[0]) and
            (new_x, new_y) != other_player_pos):
            
            if self.maze[new_y][new_x] == 0:  # 0 = walkable path
                self.x = new_x
                self.y = new_y
                self.target_x = new_x * self.tile_size
                self.target_y = new_y * self.tile_size
                self.can_move = False  # Start movement cooldown

    def kill_ghost(self, ghost):
        """Kill a ghost if the player is powered up."""
        if self.power_up:
            ghost.alive = False
            self.score += 50  # Bonus for killing a ghost

    def be_killed(self):
        """Handle the player being killed (lose a life and respawn)."""
        if not self.is_dying and self.alive:
            self.is_dying = True
            self.death_timer = 0
            self.lives -= 1
            print(f"Player died. Lives remaining: {self.lives}")  # Debug print
            
            if self.lives <= 0:
                self.alive = False
                print("Player is out of lives!")  # Debug print
            else:
                self.respawn_timer = self.respawn_delay
                print(f"Player will respawn in {self.respawn_delay} frames")  # Debug print

    def update(self):
        """Update animation and movement."""
        if self.is_dying:
            self.death_timer += 1
            if self.death_timer >= self.death_animation_frames:
                self.is_dying = False
                if self.lives > 0:
                    self.respawn_timer = self.respawn_delay
                return

        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer == 0:
                # Respawn at starting position
                self.x = self.start_x
                self.y = self.start_y
                self.current_x = self.x * self.tile_size
                self.current_y = self.y * self.tile_size
                self.target_x = self.current_x
                self.target_y = self.current_y
                self.alive = True
                print(f"Player respawned at ({self.x}, {self.y})")  # Debug print
            return

        if not self.alive:
            return  # Don't animate if player is dead

        # Smooth movement interpolation
        if self.current_x != self.target_x:
            dx = self.target_x - self.current_x
            self.current_x += dx * 0.2  # Smooth interpolation
        if self.current_y != self.target_y:
            dy = self.target_y - self.current_y
            self.current_y += dy * 0.2  # Smooth interpolation

        # Update animation frame
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames[self.direction])

        # Update power-up countdown
        if self.power_up:
            self.power_up_timer -= 1
            if self.power_up_timer <= 0:
                self.power_up = False  # Power-up ends

    def check_ghost_collision(self, ghosts):
        """Check if the player collides with any ghost."""
        for ghost in ghosts:
            if (self.x, self.y) == ghost.tile_position():
                if not self.is_dying and self.alive:  # Only process collision if not already dying and still alive
                    self.be_killed()
                return True  # Collision happened
        return False  # No collision

    def draw(self, surface):
        """Draw the player sprite with optional effects."""
        if not self.frames:
            return  # No sprite loaded

        if self.is_dying:
            # Draw death animation
            death_frame = min(self.death_timer, self.death_animation_frames - 1)
            # Create a simple death animation by drawing a shrinking circle
            radius = int(self.tile_size * (1 - death_frame / self.death_animation_frames))
            pygame.draw.circle(surface, (255, 255, 0),
                             (self.current_x + self.tile_size // 2,
                              self.current_y + self.tile_size // 2),
                             radius)
            return

        if not self.alive or self.respawn_timer > 0:
            return  # Don't draw if dead or respawning

        # Select current sprite frame
        sprite = self.frames[self.direction][self.current_frame]

        # Resize sprite if needed
        if sprite.get_size() != (self.tile_size, self.tile_size):
            sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))

        # Center the sprite using interpolated position
        offset = (self.tile_size - sprite.get_width()) // 2
        surface.blit(sprite, (self.current_x + offset, self.current_y + offset))

        # Draw red circle if player is powered up
        if self.power_up:
            pygame.draw.circle(surface, (255, 0, 0),
                             (self.current_x + self.tile_size // 2,
                              self.current_y + self.tile_size // 2),
                             self.tile_size // 2, 2)
