import pygame
import sys
import os
from pygame import mixer
import math

# Initialize Pygame
pygame.init()
mixer.init()

# Screen settings (match main game dimensions)
TILE = 25
ROWS, COLS = 21, 21
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 191, 255)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
DARK_GRAY = (40, 40, 40)
TITLE_ORANGE = (255, 165, 0)
BACKGROUND_BLUE = (10, 10, 30)  # Dark blue background

# Fonts
try:
    title_font = pygame.font.Font('AI-PROJECT-25/font/BalAstaral.ttf', 48)
    medium_font = pygame.font.Font('AI-PROJECT-25/font/BalAstaral.ttf', 24)
    small_font = pygame.font.Font('AI-PROJECT-25/font/BalAstaral.ttf', 16)
except:
    try:
        title_font = pygame.font.Font('AI-PROJECT-25/font/BalAstaral.ttf', 48)
        medium_font = pygame.font.Font('PressStart2P-Regular.ttf', 24)
        small_font = pygame.font.Font('PressStart2P-Regular.ttf', 16)
    except:
        title_font = pygame.font.SysFont('Courier', 48, bold=True)
        medium_font = pygame.font.SysFont('Courier', 24, bold=True)
        small_font = pygame.font.SysFont('Courier', 16, bold=True)

# Load sounds
try:
    menu_sound = mixer.Sound('AI-PROJECT-25/sound/pacman_beginning.wav')
    menu_sound.set_volume(0.5)
    menu_sound.play(-1)  # Loop menu music
except Exception as e:
    print(f"Error loading menu sound: {e}")
    menu_sound = None

# Ghost data with more personality
ghost_data = [
    {"name": "Inky", "color": CYAN, "filename": "AI-PROJECT-25/images/inky.png", "personality": "Ambush"},
    {"name": "Blinky", "color": RED, "filename": "AI-PROJECT-25/images/blinky.png", "personality": "Angry"},
    {"name": "Clyde", "color": ORANGE, "filename": "AI-PROJECT-25/images/clyde.png", "personality": "Shy"},
    {"name": "Pinky", "color": PINK, "filename": "AI-PROJECT-25/images/pinky.png", "personality": "Tricky"}
]

# Load ghost images with proper transparency
ghost_images = []
for ghost in ghost_data:
    try:
        img = pygame.image.load(ghost['filename']).convert_alpha()
        img = pygame.transform.scale(img, (60, 60))  # Slightly smaller
        ghost_images.append(img)
    except:
        try:
            img = pygame.image.load(ghost['filename'].split('/')[-1]).convert_alpha()
            img = pygame.transform.scale(img, (60, 60))
            ghost_images.append(img)
        except:
            # Create placeholder with proper transparency
            surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(surf, ghost['color'], (30, 30), 25)
            # Eyes
            pygame.draw.circle(surf, WHITE, (20, 20), 8)
            pygame.draw.circle(surf, WHITE, (40, 20), 8)
            pygame.draw.circle(surf, BLACK, (20, 20), 4)
            pygame.draw.circle(surf, BLACK, (40, 20), 4)
            ghost_images.append(surf)

# Enhanced Pac-Man class with smoother animation
class PacMan:
    def __init__(self, color, x, y):
        self.color = color
        self.x = x
        self.y = y
        self.size = 30  # Slightly smaller
        self.mouth_angle = 0
        self.mouth_direction = 1
        self.direction = 'right'
        self.animation_speed = 0.15
        self.base_y = y  # For floating animation
        
    def update(self):
        # Animate mouth
        self.mouth_angle += self.mouth_direction * self.animation_speed
        if self.mouth_angle > 45 or self.mouth_angle < 0:
            self.mouth_direction *= -1
            
        # Floating animation
        self.y = self.base_y + math.sin(pygame.time.get_ticks() * 0.005) * 5
        
    def draw(self, surface):
        # Body
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.size//2)
        
        # Mouth - changes based on direction and animation
        if self.direction == 'right':
            points = [
                (self.x, self.y),
                (self.x + self.size//2, self.y - self.size//2 * (self.mouth_angle/45)),
                (self.x + self.size//2, self.y + self.size//2 * (self.mouth_angle/45))
            ]
        elif self.direction == 'left':
            points = [
                (self.x, self.y),
                (self.x - self.size//2, self.y - self.size//2 * (self.mouth_angle/45)),
                (self.x - self.size//2, self.y + self.size//2 * (self.mouth_angle/45))
            ]
        elif self.direction == 'up':
            points = [
                (self.x, self.y),
                (self.x - self.size//2 * (self.mouth_angle/45), self.y - self.size//2),
                (self.x + self.size//2 * (self.mouth_angle/45), self.y - self.size//2)
            ]
        else:  # down
            points = [
                (self.x, self.y),
                (self.x - self.size//2 * (self.mouth_angle/45), self.y + self.size//2),
                (self.x + self.size//2 * (self.mouth_angle/45), self.y + self.size//2)
            ]
        
        pygame.draw.polygon(surface, BLACK, points)

# Create Pac-Man instances
yellow_pacman = PacMan(YELLOW, WIDTH//3, HEIGHT - 150)
yellow_pacman.direction = 'right'
blue_pacman = PacMan(BLUE, WIDTH*2//3, HEIGHT - 150)
blue_pacman.direction = 'left'

# Enhanced Button class with better visual feedback
class Button:
    def __init__(self, x, y, width, height, text, font, 
                 text_color, button_color, border_color, border_width, radius):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.button_color = button_color
        self.border_color = border_color
        self.border_width = border_width
        self.radius = radius
        self.hover = False
        self.shadow_offset = 3
        self.click_offset = 1
        self.clicked = False
        self.pulse = 0
        self.pulse_dir = 1
        
    def update(self):
        # Pulsing effect when hovered
        if self.hover:
            self.pulse += 0.05 * self.pulse_dir
            if self.pulse > 0.5 or self.pulse < 0:
                self.pulse_dir *= -1
        
    def draw(self, surface):
        # Position adjustment when clicked
        pos_offset = self.click_offset if self.clicked else 0
        
        # Soft shadow
        shadow_rect = pygame.Rect(
            self.rect.x + self.shadow_offset, 
            self.rect.y + self.shadow_offset, 
            self.rect.width, 
            self.rect.height
        )
        pygame.draw.rect(surface, (20, 20, 20), shadow_rect, border_radius=self.radius)
        
        # Button background with hover effect
        if self.hover:
            pulse_val = 30 + int(10 * self.pulse)
            color = (
                min(self.button_color[0]+pulse_val, 255), 
                min(self.button_color[1]+pulse_val, 255), 
                min(self.button_color[2]+pulse_val, 255)
            )
        else:
            color = self.button_color
            
        pygame.draw.rect(surface, color, 
                         (self.rect.x + pos_offset, self.rect.y + pos_offset, 
                          self.rect.width, self.rect.height), 
                         border_radius=self.radius)
        
        # Button border
        pygame.draw.rect(surface, self.border_color, 
                         (self.rect.x + pos_offset, self.rect.y + pos_offset, 
                          self.rect.width, self.rect.height), 
                         self.border_width, border_radius=self.radius)
        
        # Text with shadow
        text_surf = self.font.render(self.text, True, self.text_color)
        text_shadow = self.font.render(self.text, True, (50, 50, 50))
        text_rect = text_surf.get_rect(center=(self.rect.centerx + pos_offset, 
                                              self.rect.centery + pos_offset))
        
        surface.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover
    
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(pos):
                self.clicked = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False
        return False

# Create button
button = Button(
    WIDTH//2 - 100,  # Reduced width, centered
    HEIGHT - 80,     # Moved up from bottom
    200,            # Reduced width from 300
    40,             # Reduced height from 50
    "START GAME", 
    medium_font,
    YELLOW, 
    TITLE_ORANGE, 
    RED, 
    2, 
    10  # Slightly reduced radius
)

# Dots animation - more dynamic
dots = []
for i in range(30):  # Reduced number of dots
    dots.append({
        'x': i * 20 + 15,  # Reduced spacing
        'y': HEIGHT - 30,  # Moved up
        'size': 4,        # Slightly smaller
        'color': YELLOW,
        'eaten': False,
        'pulse': i % 3
    })

# Background maze pattern
maze_pattern = []
for i in range(0, WIDTH, 40):
    for j in range(0, HEIGHT, 40):
        if (i + j) % 5 == 0:  # Create a grid pattern
            maze_pattern.append((i, j))

# Function to draw text with multiple shadows for depth
def draw_text_with_shadow(surface, text, font, text_color, shadow_color, pos, shadow_offset=2, shadow_steps=2):
    for i in range(shadow_steps, 0, -1):
        shadow = font.render(text, True, 
                           (shadow_color[0]//i, shadow_color[1]//i, shadow_color[2]//i))
        surface.blit(shadow, (pos[0] + shadow_offset*i, pos[1] + shadow_offset*i))
    
    text_surface = font.render(text, True, text_color)
    surface.blit(text_surface, pos)

# Function to draw title box with outline and shadow
def draw_title_box(surface, text, font, text_color, box_color, outline_color, pos, padding=30):
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=pos)
    
    # Box dimensions
    box_width = text_rect.width + padding * 2
    box_height = text_rect.height + padding * 2
    box_rect = pygame.Rect(pos[0] - box_width//2, pos[1] - box_height//2, box_width, box_height)
    
    # Draw shadow
    shadow_rect = box_rect.move(3, 3)
    pygame.draw.rect(surface, (50, 20, 0), shadow_rect, border_radius=20)
    
    # Draw box
    pygame.draw.rect(surface, box_color, box_rect, border_radius=10)
    pygame.draw.rect(surface, outline_color, box_rect, 3, border_radius=10)
    
    # Draw text
    surface.blit(text_surf, text_rect)

# Main function for Front Page
def front_page(high_score=0):
    clock = pygame.time.Clock()
    running = True
    start_game = False
    
    # Create a temporary surface for the front page
    front_surface = pygame.Surface((WIDTH, HEIGHT))
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            
            if button.is_clicked(mouse_pos, event):
                try:
                    select_sound = mixer.Sound('AI-PROJECT-25/sound/pacman_chomp.wav')
                    select_sound.set_volume(0.2)
                    select_sound.play()
                except:
                    pass
                print("Continue to game!")
                start_game = True
                running = False
                # Stop the menu music when transitioning to the game
                try:
                    if menu_sound:
                        menu_sound.stop()
                except:
                    pass
        
        # Update animations
        yellow_pacman.update()
        blue_pacman.update()
        button.check_hover(mouse_pos)
        button.update()
        
        # Draw everything on the front surface
        front_surface.fill(BACKGROUND_BLUE)
        
        # Draw subtle maze pattern in background
        for x, y in maze_pattern:
            if (x + y) % 160 == 0:
                pygame.draw.circle(front_surface, (30, 30, 60), (x, y), 1)
        
        # Draw animated dots with pulsing effect
        for i, dot in enumerate(dots):
            if not dot['eaten']:
                pulse_size = dot['size'] + math.sin(pygame.time.get_ticks() * 0.005 + dot['pulse']) * 2
                pygame.draw.circle(front_surface, dot['color'], (dot['x'], dot['y']), max(2, pulse_size))
        
        # Draw title box with Pac-Man in it - moved down slightly
        title_pos = (WIDTH//2, 50)
        draw_title_box(front_surface, "PAC-MAN", title_font, YELLOW, TITLE_ORANGE, RED, title_pos, 15)
        
        # Adjust scoreboard position
        draw_text_with_shadow(front_surface, "HIGH SCORE", medium_font, YELLOW, DARK_GRAY, 
                            (WIDTH//2.8, 110))
        draw_text_with_shadow(front_surface, str(high_score), medium_font, RED, DARK_GRAY, 
                            (WIDTH//2, 140))
        
        # Adjust ghost section position
        draw_text_with_shadow(front_surface, "GHOST TEAM", medium_font, WHITE, DARK_GRAY, 
                            (WIDTH//2.8, 180))
        
        # Adjust ghost positions
        ghost_y = 220  # Base Y position for ghosts
        ghost_x_spacing = WIDTH // 5
        ghost_x_positions = [
            ghost_x_spacing + i * ghost_x_spacing 
            for i in range(4)
        ]
        
        for i in range(4):
            y_offset = math.sin(pygame.time.get_ticks() * 0.003 + i) * 5
            front_surface.blit(ghost_images[i], (ghost_x_positions[i] - 30, ghost_y + y_offset))
            
            name_text = ghost_data[i]['name']
            pers_text = ghost_data[i]['personality']
            
            # Adjust text positions relative to ghost positions
            draw_text_with_shadow(front_surface, name_text, small_font, ghost_data[i]['color'], 
                                DARK_GRAY, (ghost_x_positions[i] - 20, ghost_y + 70))
            draw_text_with_shadow(front_surface, pers_text, small_font, WHITE, 
                                DARK_GRAY, (ghost_x_positions[i] - 20, ghost_y + 90))
        
        # Draw Pac-Man characters and controls
        yellow_pacman.draw(front_surface)
        draw_text_with_shadow(front_surface, "Player 1", small_font, YELLOW, DARK_GRAY, 
                            (WIDTH//3.7, HEIGHT - 120))
        draw_text_with_shadow(front_surface, "ARROW KEYS", small_font, WHITE, DARK_GRAY, 
                            (WIDTH//4.3, HEIGHT - 100))
        
        blue_pacman.draw(front_surface)
        draw_text_with_shadow(front_surface, "Player 2", small_font, BLUE, DARK_GRAY, 
                            (WIDTH*2//3.3, HEIGHT - 120))
        draw_text_with_shadow(front_surface, "W A S D", small_font, WHITE, DARK_GRAY, 
                            (WIDTH*2//3.2, HEIGHT - 100))
        
        # Draw button
        button.draw(front_surface)
        
        # Draw high score
        high_score_text = f"High Score: {high_score}"
        high_score_surface = medium_font.render(high_score_text, True, WHITE)
        high_score_rect = high_score_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        screen.blit(high_score_surface, high_score_rect)
        
        # Blit the front surface onto the main screen
        screen.blit(front_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)
    
    # Clear the screen before returning
    screen.fill((0, 0, 0))
    pygame.display.flip()
    return start_game

# Run the game
if __name__ == "__main__":
    front_page(0)  # Pass 0 as default high score when running directly