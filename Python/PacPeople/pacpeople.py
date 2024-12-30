import pygame
import random

# Initialize PyGame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pacman with Gravity")

# Colors (R,G,B)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Game settings
PLAYER_SIZE = 30
PLAYER_COLOR = BLUE
BOULDER_SIZE = 20
BOULDER_COLOR = RED
GRAVITY = 0.5
PLAYER_JUMP_FORCE = -10
PLAYER_MOVE_SPEED = 5
BOULDER_SPEED = 3
BOULDER_SPAWN_INTERVAL = 2000  # milliseconds

# Initialize player
player = pygame.Rect(WIDTH // 2, HEIGHT // 2, PLAYER_SIZE, PLAYER_SIZE)
player_vel_y = 0
is_on_ground = False

# Boulder list
boulders = []

# Clock and timer
clock = pygame.time.Clock()
boulder_timer = pygame.USEREVENT + 1
pygame.time.set_timer(boulder_timer, BOULDER_SPAWN_INTERVAL)

# Main game loop
running = True
while running:
    screen.fill(WHITE)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == boulder_timer:
            # Spawn a new boulder from a random side
            if random.choice([True, False]):
                boulders.append(pygame.Rect(0, random.randint(0, HEIGHT // 2), BOULDER_SIZE, BOULDER_SIZE))  # Left side
            else:
                boulders.append(pygame.Rect(WIDTH - BOULDER_SIZE, random.randint(0, HEIGHT // 2), BOULDER_SIZE, BOULDER_SIZE))  # Right side

    # Player controls
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.x -= PLAYER_MOVE_SPEED
    if keys[pygame.K_RIGHT]:
        player.x += PLAYER_MOVE_SPEED
    if keys[pygame.K_UP] and is_on_ground:
        player_vel_y = PLAYER_JUMP_FORCE
        is_on_ground = False

    # Apply gravity to player
    player_vel_y += GRAVITY
    player.y += int(player_vel_y)

    # Check for ground collision
    if player.y + PLAYER_SIZE >= HEIGHT:
        player.y = HEIGHT - PLAYER_SIZE
        player_vel_y = 0
        is_on_ground = True

    # Update and draw boulders
    for boulder in boulders[:]:
        # Apply gravity to boulders
        boulder.y += int(GRAVITY)
        
        # Move boulders horizontally based on their spawn side
        if boulder.x < WIDTH // 2:
            boulder.x += BOULDER_SPEED
        else:
            boulder.x -= BOULDER_SPEED

        # Remove boulders that go off the screen
        if boulder.y > HEIGHT:
            boulders.remove(boulder)
        
        # Draw boulder
        pygame.draw.rect(screen, BOULDER_COLOR, boulder)

    # Draw player
    pygame.draw.rect(screen, PLAYER_COLOR, player)

    # Collision detection between player and boulders
    for boulder in boulders:
        if player.colliderect(boulder):
            print("Game Over!")  # Placeholder action for collision
            running = False

    # Update display and tick the clock
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
