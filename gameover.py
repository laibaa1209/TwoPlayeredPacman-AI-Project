import pygame
import sys
import os
import math
from pygame import mixer

# Initialize Pygame
pygame.init()
mixer.init()

# Screen settings
TILE = 25
ROWS, COLS = 21, 21
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE
SCOREBOARD_WIDTH = 200
MAIN_WIDTH = WIDTH + SCOREBOARD_WIDTH
MAIN_HEIGHT = HEIGHT

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 191, 255)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
TITLE_ORANGE = (255, 165, 0)
DARK_GRAY = (40, 40, 40)
BACKGROUND_BLUE = (10, 10, 30)

# Fonts
FONT_PATH = 'AI-PROJECT-25/font/BalAstaral.ttf'
try:
    title_font = pygame.font.Font(FONT_PATH, 72)
    score_font = pygame.font.Font(FONT_PATH, 36)
    button_font = pygame.font.Font(FONT_PATH, 24)
except:
    title_font = pygame.font.SysFont('Courier', 72, bold=True)
    score_font = pygame.font.SysFont('Courier', 36, bold=True)
    button_font = pygame.font.SysFont('Courier', 24, bold=True)

# Load sounds
try:
    game_over_sound = mixer.Sound('AI-PROJECT-25/sound/game-over-160612.mp3')
    death_sound = mixer.Sound('AI-PROJECT-25/sound/game_over.mp3')
    death_sound.set_volume(0.3)
except:
    print("Sound files not found - continuing without sound")
    death_sound = None

# Ghost data and images (reuse from frontpage)
ghost_data = [
    {"name": "Inky", "color": CYAN, "filename": "AI-PROJECT-25/images/inky.png"},
    {"name": "Blinky", "color": RED, "filename": "AI-PROJECT-25/images/blinky.png"},
    {"name": "Clyde", "color": ORANGE, "filename": "AI-PROJECT-25/images/clyde.png"},
    {"name": "Pinky", "color": PINK, "filename": "AI-PROJECT-25/images/pinky.png"}
]
ghost_images = []
for ghost in ghost_data:
    try:
        img = pygame.image.load(ghost['filename']).convert_alpha()
        img = pygame.transform.scale(img, (60, 60))
        ghost_images.append(img)
    except:
        surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(surf, ghost['color'], (30, 30), 25)
        pygame.draw.circle(surf, WHITE, (20, 20), 8)
        pygame.draw.circle(surf, WHITE, (40, 20), 8)
        pygame.draw.circle(surf, BLACK, (20, 20), 4)
        pygame.draw.circle(surf, BLACK, (40, 20), 4)
        ghost_images.append(surf)

# Maze pattern for background
maze_pattern = []
for i in range(0, WIDTH, 40):
    for j in range(0, HEIGHT, 40):
        if (i + j) % 5 == 0:
            maze_pattern.append((i, j))

def draw_text_with_shadow(surface, text, font, color, shadow_color, pos, shadow_offset=4, glow_radius=8, alpha=255, center=True):
    # Draw soft shadow/glow
    base = font.render(text, True, color)
    shadow = font.render(text, True, shadow_color)
    rect = base.get_rect(center=pos) if center else base.get_rect(topleft=pos)
    for i in range(glow_radius, 0, -2):
        s = pygame.Surface((rect.width + i*2, rect.height + i*2), pygame.SRCALPHA)
        s.blit(shadow, (i, i))
        s.set_alpha(int(alpha * 0.15))
        surface.blit(s, rect.move(-i, -i))
    surface.blit(base, rect)

def animate_game_over(surface, text, font, color, shadow_color, pos, t):
    # Bounce and glow effect
    scale = 1.0 + 0.08 * abs(math.sin(t * 0.08))
    alpha = min(255, int(255 * (t / 60)))
    font_size = int(font.get_height() * scale)
    try:
        temp_font = pygame.font.Font(FONT_PATH, font_size)
    except:
        temp_font = pygame.font.SysFont('Courier', font_size, bold=True)
    draw_text_with_shadow(surface, text, temp_font, color, shadow_color, pos, shadow_offset=6, glow_radius=12, alpha=alpha)

# PacMan animation class (from frontpage)
class PacMan:
    def __init__(self, color, x, y, direction='right'):
        self.color = color
        self.x = x
        self.y = y
        self.size = 30
        self.mouth_angle = 0
        self.mouth_direction = 1
        self.direction = direction
        self.animation_speed = 0.5
        self.base_y = y
    def update(self):
        self.mouth_angle += self.mouth_direction * self.animation_speed
        if self.mouth_angle > 45 or self.mouth_angle < 0:
            self.mouth_direction *= -1
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.size//2)
        # Mouth
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
        else:
            points = [
                (self.x, self.y),
                (self.x - self.size//2 * (self.mouth_angle/45), self.y + self.size//2),
                (self.x + self.size//2 * (self.mouth_angle/45), self.y + self.size//2)
            ]
        pygame.draw.polygon(surface, BLACK, points)
        # Eye
        pygame.draw.circle(surface, BLACK, (self.x + 8, self.y - 8), 4)

def draw_ghosts_chasing_pacmen(surface, t, y, yellow_pacman, blue_pacman):
    # Animate ghosts and Pac-Men moving left to right in a loop
    spacing = 80
    total = 6  # 4 ghosts + 2 pacmen
    start_x = int((t * 3) % (WIDTH + spacing * total)) - spacing * total // 2
    # Draw ghosts
    for i in range(4):
        surface.blit(ghost_images[i], (start_x + i*spacing, y))
    # Animate Pac-Man
    yellow_pacman.x = start_x + 4*spacing + 30
    yellow_pacman.y = y + 30
    yellow_pacman.update()
    yellow_pacman.draw(surface)
    blue_pacman.x = start_x + 5*spacing + 30
    blue_pacman.y = y + 30
    blue_pacman.update()
    blue_pacman.draw(surface)

def draw_outlined_text(surface, text, font, color, outline_color, pos, outline_width=3, center=True):
    base = font.render(text, True, color)
    outline = font.render(text, True, outline_color)
    rect = base.get_rect(center=pos) if center else base.get_rect(topleft=pos)
    # Draw outline
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            if dx != 0 or dy != 0:
                surface.blit(outline, rect.move(dx, dy))
    # Draw main text
    surface.blit(base, rect)

def draw_ghosts_and_pacmen(surface, center_x, y):
    # Draw: ghost, ghost, ghost, ghost, yellow pacman, blue pacman (all in a row)
    spacing = 70
    start_x = center_x - (2*spacing + 30)
    # Draw ghosts
    for i in range(4):
        surface.blit(ghost_images[i], (start_x + i*spacing, y))
    # Draw yellow Pac-Man
    pygame.draw.circle(surface, YELLOW, (start_x + 4*spacing + 35, y+30), 30)
    pygame.draw.polygon(surface, BLACK, [
        (start_x + 4*spacing + 35, y+30),
        (start_x + 4*spacing + 65, y+10),
        (start_x + 4*spacing + 65, y+50)
    ])
    # Draw blue Pac-Man
    pygame.draw.circle(surface, BLUE, (start_x + 5*spacing + 35, y+30), 30)
    pygame.draw.polygon(surface, BLACK, [
        (start_x + 5*spacing + 35, y+30),
        (start_x + 5*spacing + 65, y+10),
        (start_x + 5*spacing + 65, y+50)
    ])

class Button:
    def __init__(self, x, y, width, height, text, font, text_color, button_color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.button_color = button_color
        self.hover_color = hover_color
        self.hover = False
        self.alpha = 0  # For fade-in animation

    def update(self):
        if self.alpha < 255:
            self.alpha = min(255, self.alpha + 5)

    def check_hover(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        # Create button surface with alpha
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        color = self.hover_color if self.hover else self.button_color
        pygame.draw.rect(button_surface, (*color, self.alpha), (0, 0, self.rect.width, self.rect.height), border_radius=10)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.rect.width//2, self.rect.height//2))
        button_surface.blit(text_surface, text_rect)
        
        # Draw button with fade effect
        surface.blit(button_surface, self.rect)

def draw_text_with_animation(surface, text, font, color, pos, alpha, scale=1.0):
    text_surface = font.render(text, True, color)
    text_surface.set_alpha(alpha)
    
    # Scale the text
    if scale != 1.0:
        new_size = (int(text_surface.get_width() * scale), int(text_surface.get_height() * scale))
        text_surface = pygame.transform.scale(text_surface, new_size)
    
    text_rect = text_surface.get_rect(center=pos)
    surface.blit(text_surface, text_rect)

def game_over_screen(winner, player1_score, player2_score):
    screen = pygame.display.set_mode((MAIN_WIDTH, MAIN_HEIGHT))
    pygame.display.set_caption("Game Over")
    
    # Play game over sound once
    if game_over_sound:
        game_over_sound.play()
    # Play death sound in a loop
    if death_sound:
        death_sound.play(-1)
    
    # Center positions
    center_x = MAIN_WIDTH // 2
    center_y = MAIN_HEIGHT // 2
    
    # Create PacMan instances for animation
    yellow_pacman = PacMan(YELLOW, 0, 0, direction='right')
    yellow_pacman.animation_speed = 0.5
    blue_pacman = PacMan(BLUE, 0, 0, direction='right')
    blue_pacman.animation_speed = 0.5
    
    # Create restart button
    button_width, button_height = 200, 50
    button_x = center_x - button_width // 2
    button_y = center_y + 200
    button = Button(button_x, button_y, button_width, button_height, "Play Again", button_font,
                   WHITE, ORANGE, RED)
    
    clock = pygame.time.Clock()
    running = True
    t = 0  # Animation timer
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button.rect.collidepoint(pygame.mouse.get_pos()):
                    return True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
        
        # Draw front page style background
        screen.fill(BACKGROUND_BLUE)
        for x, y in maze_pattern:
            if (x + y) % 160 == 0:
                pygame.draw.circle(screen, (30, 30, 60), (x, y), 1)
        
        # Animate GAME OVER text
        animate_game_over(screen, "GAME OVER", title_font, RED, WHITE, (center_x, center_y - 150), t)
        
        # Winner text
        if t > 30:
            if winner == "Tie":
                draw_text_with_shadow(screen, "GHOST WINS!", title_font, WHITE, RED, (center_x, center_y - 60), shadow_offset=6, glow_radius=10)
            else:
                winner_color = YELLOW if winner == "Player 1" else BLUE
                draw_text_with_shadow(screen, f"{winner} WINS!", title_font, winner_color, RED, (center_x, center_y - 60), shadow_offset=6, glow_radius=10)
        # Scores
        if t > 40:
            draw_text_with_shadow(screen, f"Player 1: {player1_score}", score_font, YELLOW, BLACK, (center_x, center_y + 30), shadow_offset=4, glow_radius=8)
            draw_text_with_shadow(screen, f"Player 2: {player2_score}", score_font, BLUE, BLACK, (center_x, center_y + 70), shadow_offset=4, glow_radius=8)
        # Animated chase scene
        if t > 60:
            draw_ghosts_chasing_pacmen(screen, t, center_y + 120, yellow_pacman, blue_pacman)
        # Button
        button.update()
        button.check_hover(pygame.mouse.get_pos())
        button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
        t += 1
    
    return False 