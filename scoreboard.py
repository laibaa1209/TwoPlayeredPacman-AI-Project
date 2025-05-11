import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Screen settings (smaller rectangle window)
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Men Title Screen")

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
WHITE = (255, 255, 255)
BLUE = (0, 191, 255)
DARK_GRAY = (50, 50, 50)  # Shadow color for borders and text

# Fonts
try:
    pixel_font = pygame.font.Font('AI-PROJECT-25/font/BalAstaral.ttf', 70)  # Make sure the font file is in the same directory
except:
    pixel_font = pygame.font.SysFont('Courier', 70, bold=True)

# Scoreboard Class
class Scoreboard:
    def __init__(self, surface):
        self.surface = surface
        self.width = surface.get_width()
        self.height = surface.get_height()
        self.game_over = False
        self.winner = None
        self.player1_score = 0
        self.player2_score = 0
        self.player1_lives = 3
        self.player2_lives = 3
        
        # Load fonts
        try:
            self.font = pygame.font.Font('AI-PROJECT-25/font/BalAstaral.ttf', 24)
            self.small_font = pygame.font.Font('AI-PROJECT-25/font/BalAstaral.ttf', 16)
        except:
            self.font = pygame.font.SysFont('Courier', 24, bold=True)
            self.small_font = pygame.font.SysFont('Courier', 16, bold=True)

    def update_scores(self, player1_score, player2_score):
        self.player1_score = player1_score
        self.player2_score = player2_score

    def update_lives(self, player1_lives, player2_lives):
        self.player1_lives = player1_lives
        self.player2_lives = player2_lives

    def set_game_over(self, winner):
        self.game_over = True
        self.winner = winner

    # Function to draw rounded rectangle with shadow
    def draw_rounded_rect_with_shadow(self, rect, color, border_color, border_width, radius, shadow_offset=(5, 5)):
        x, y, w, h = rect
        # Draw shadow first (darker color)
        pygame.draw.rect(self.surface, DARK_GRAY, (x + shadow_offset[0], y + shadow_offset[1], w, h), border_radius=radius)
        # Draw the main rounded rectangle
        pygame.draw.rect(self.surface, color, rect, border_radius=radius)
        pygame.draw.rect(self.surface, border_color, rect, width=border_width, border_radius=radius)

    # Function to draw outlined text with shadow
    def draw_text_with_shadow(self, text, color, center_pos, shadow_offset=(2, 2)):
        # Draw shadow
        shadow = self.font.render(text, True, DARK_GRAY)
        shadow_rect = shadow.get_rect(center=(center_pos[0] + shadow_offset[0], center_pos[1] + shadow_offset[1]))
        self.surface.blit(shadow, shadow_rect)
        
        # Draw text
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=center_pos)
        self.surface.blit(text_surface, text_rect)

    # Function to draw pixel heart
    def draw_pixel_heart(self, x, y, color, pixel_size=4):
        heart_pattern = [
            " 00 00 ",
            "0000000",
            "0000000",
            " 00000 ",
            "  000  ",
            "   0   "
        ]
        for row_idx, row in enumerate(heart_pattern):
            for col_idx, pixel in enumerate(row):
                if pixel == '0':
                    rect = pygame.Rect(x + col_idx * pixel_size, y + row_idx * pixel_size, pixel_size, pixel_size)
                    pygame.draw.rect(self.surface, color, rect)

    # Function to draw proper Pac-Man (mouth cut out)
    def draw_pacman(self, x, y, color, facing_left=True):
        mouth_angle = math.pi / 4  # 45 degrees
        start_angle = mouth_angle if facing_left else (-mouth_angle)
        end_angle = (2 * math.pi) - mouth_angle if facing_left else (2 * math.pi) + mouth_angle
        # Create a Pac-Man shape using pygame.draw.polygon for mouth cut
        pacman_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(pacman_surface, color, (30, 30), 30)
        if facing_left:
            pygame.draw.polygon(pacman_surface, (0, 0, 0, 0), [(30, 30),
                                                               (60, 15),
                                                               (60, 45)])
        else:
            pygame.draw.polygon(pacman_surface, (0, 0, 0, 0), [(30, 30),
                                                               (0, 15),
                                                               (0, 45)])
        self.surface.blit(pacman_surface, (x - 30, y - 30))

    def draw_scoreboard(self):
        # Colors
        YELLOW = (255, 255, 0)
        BLUE = (0, 191, 255)
        WHITE = (255, 255, 255)
        DARK_GRAY = (40, 40, 40)
        RED = (255, 0, 0)
        
        # Draw background
        pygame.draw.rect(self.surface, (0, 0, 0), (0, 0, self.width, self.height))
        
        # Calculate positions for centered layout
        center_x = self.width // 2
        spacing = self.width // 4
        
        # Draw Player 1 info (left side)
        self.draw_text_with_shadow(f"P1: {self.player1_score}", YELLOW, (center_x - spacing, 15))
        # Draw "Lives:" text and hearts for Player 1
        self.draw_text_with_shadow("Lives:", YELLOW, (center_x - spacing - 30, 35))
        heart_x = center_x - spacing + 20
        for i in range(self.player1_lives):
            self.draw_pixel_heart(heart_x + (i * 25), 30, RED, 3)
        
        # Draw Player 2 info (right side)
        self.draw_text_with_shadow(f"P2: {self.player2_score}", BLUE, (center_x + spacing, 15))
        # Draw "Lives:" text and hearts for Player 2
        self.draw_text_with_shadow("Lives:", BLUE, (center_x + spacing - 30, 35))
        heart_x = center_x + spacing + 20
        for i in range(self.player2_lives):
            self.draw_pixel_heart(heart_x + (i * 25), 30, RED, 3)
        
        # Draw game over message if game is over
        if self.game_over:
            if self.winner == "Tie":
                self.draw_text_with_shadow("IT'S A TIE!", WHITE, (center_x, 25))
            else:
                self.draw_text_with_shadow(f"{self.winner} WINS!", WHITE, (center_x, 25))

# Main loop
def main():
    clock = pygame.time.Clock()
    scoreboard = Scoreboard(screen)

    while True:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Call the draw_scoreboard function from the Scoreboard class
        scoreboard.draw_scoreboard()

        pygame.display.flip()
        clock.tick(60)

# Run the game
if __name__ == "__main__":
    main()
