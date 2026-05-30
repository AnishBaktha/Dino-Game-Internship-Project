"""Dino Game in Python

A game similar to the famous Chrome Dino Game, built using pygame-ce.
Original intern: @bassemfarid
Additional author: [Your Name Here]
Commit hash: [paste your commit hash here after committing]
"""

import pygame
import random

# Initialize Pygame and create a window
pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Dino Game")
clock = pygame.time.Clock()
running = True  # Pygame main loop, kills pygame when False

# Game state variables
is_playing = False  # Start on the menu screen
GROUND_Y = 300      # The Y-coordinate of the ground level
JUMP_SPEED = -20    # The speed at which the player jumps

# Load level assets (loaded once outside the loop for performance)
SKY_SURF = pygame.image.load("graphics/level/sky.png").convert()
GROUND_SURF = pygame.image.load("graphics/level/ground.png").convert()

game_font = pygame.font.Font(pygame.font.get_default_font(), 40)

# --- Player assets ---
player_walk_1 = pygame.image.load("graphics/player/player_walk_1.png").convert_alpha()
player_walk_2 = pygame.image.load("graphics/player/player_walk_2.png").convert_alpha()
player_jump_surf = pygame.image.load("graphics/player/player_jump.png").convert_alpha()

player_walk = [player_walk_1, player_walk_2]
player_index = 0
player_surf = player_walk[player_index]
player_rect = player_surf.get_rect(bottomleft=(80, GROUND_Y))

# --- Enemy assets ---
egg_frame_1 = pygame.image.load("graphics/egg/egg_1.png").convert_alpha()
egg_frame_2 = pygame.image.load("graphics/egg/egg_2.png").convert_alpha()
egg_frames = [egg_frame_1, egg_frame_2]
egg_frame_index = 0
egg_surf = egg_frames[egg_frame_index]

# --- Player state ---
players_gravity_speed = 0
jump_count = 0           # Tracks how many times the player has jumped (max 2)

# --- Enemy state ---
enemy_list = []          # List of enemy Rects currently on screen
enemy_speed = 5

# --- Score state ---
score = 0
high_score = 0
start_time = 0           # Stores the ticks (//100) when the current run started

# --- Timers (custom pygame events) ---
enemy_timer = pygame.USEREVENT + 1
pygame.time.set_timer(enemy_timer, 1200)

animation_timer = pygame.USEREVENT + 2
pygame.time.set_timer(animation_timer, 150)

egg_animation_timer = pygame.USEREVENT + 3
pygame.time.set_timer(egg_animation_timer, 300)

# --- Load high score from file ---
try:
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())
except:
    high_score = 0


# ---------- FUNCTIONS ----------

def display_score():
    """Calculate and draw the current score on screen. Returns the score value."""
    # start_time is stored in ticks//100 units, so we match that here
    current_time = pygame.time.get_ticks() // 100 - start_time

    score_surf = game_font.render(f"Score: {current_time}", False, "Black")
    score_rect = score_surf.get_rect(center=(400, 50))

    # Draw background box behind score text
    pygame.draw.rect(screen, "#c0e8ec", score_rect.inflate(20, 20))
    pygame.draw.rect(screen, "#c0e8ec", score_rect.inflate(20, 20), 8)
    screen.blit(score_surf, score_rect)

    return current_time


def animate_player():
    """Switch between walk frames, or show jump frame when airborne."""
    global player_index, player_surf

    if player_rect.bottom < GROUND_Y:
        # Player is in the air — show jump surface
        player_surf = player_jump_surf
    else:
        # Player is on the ground — cycle through walk frames
        player_index += 0.1
        if player_index >= len(player_walk):
            player_index = 0
        player_surf = player_walk[int(player_index)]


def animate_egg():
    """Cycle the egg enemy between its two animation frames."""
    global egg_frame_index, egg_surf

    egg_frame_index = 1 - egg_frame_index  # Toggle between 0 and 1
    egg_surf = egg_frames[egg_frame_index]


def player_input(event):
    """Handle jump input. Allows up to 2 jumps (double jump)."""
    global players_gravity_speed, jump_count

    if (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_SPACE
        and jump_count < 2
    ):
        players_gravity_speed = JUMP_SPEED
        jump_count += 1


def apply_gravity():
    """Apply gravity to the player each frame and clamp to the ground."""
    global players_gravity_speed, jump_count

    players_gravity_speed += 1
    player_rect.y += players_gravity_speed

    # Land on the ground
    if player_rect.bottom >= GROUND_Y:
        player_rect.bottom = GROUND_Y
        jump_count = 0  # Reset jump count when grounded


def move_enemies(enemies):
    """Move all enemies left and draw them. Remove enemies that leave the screen."""
    if enemies:
        for enemy in enemies:
            enemy.x -= enemy_speed
            screen.blit(egg_surf, enemy)

        # Keep only enemies still on screen
        enemies = [enemy for enemy in enemies if enemy.right > 0]

    return enemies


def collisions(player, enemies):
    """Return False if the player collides with any enemy, otherwise True."""
    for enemy in enemies:
        if player.colliderect(enemy):
            return False
    return True


def draw_menu():
    """Draw the start/game-over menu screen."""
    screen.fill("black")

    title_surf = game_font.render("Dino Game", False, "White")
    title_rect = title_surf.get_rect(center=(400, 100))

    controls_surf = game_font.render("SPACE to start  |  Double jump", False, "White")
    controls_rect = controls_surf.get_rect(center=(400, 180))

    high_score_surf = game_font.render(f"High Score: {high_score}", False, "White")
    high_score_rect = high_score_surf.get_rect(center=(400, 260))

    screen.blit(title_surf, title_rect)
    screen.blit(controls_surf, controls_rect)
    screen.blit(high_score_surf, high_score_rect)

    # Only show final score if the player has played at least once
    if score > 0:
        game_over_surf = game_font.render(f"Final Score: {score}", False, "White")
        game_over_rect = game_over_surf.get_rect(center=(400, 320))
        screen.blit(game_over_surf, game_over_rect)


# ---------- MAIN GAME LOOP ----------

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if is_playing:
            # Pass jump input to the player handler
            player_input(event)

            # Spawn a new enemy when the enemy timer fires
            if event.type == enemy_timer:
                enemy_list.append(
                    egg_surf.get_rect(
                        bottomleft=(random.randint(850, 1100), GROUND_Y)
                    )
                )

            # Cycle player walk animation frames
            if event.type == animation_timer:
                animate_player()

            # Cycle egg animation frames
            if event.type == egg_animation_timer:
                animate_egg()

        else:
            # On the menu: press SPACE to start a new run
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                is_playing = True

                # Reset all state for the new run
                enemy_list.clear()
                player_rect.bottomleft = (80, GROUND_Y)
                players_gravity_speed = 0
                jump_count = 0

                # Record the start time in the same units as display_score uses
                start_time = pygame.time.get_ticks() // 100

    if is_playing:
        # --- Draw background ---
        screen.blit(SKY_SURF, (0, 0))
        screen.blit(GROUND_SURF, (0, GROUND_Y))

        # --- Score ---
        score = display_score()

        # Scale difficulty: enemy speed increases every 50 score points
        enemy_speed = 5 + score // 50

        # --- Player ---
        apply_gravity()
        screen.blit(player_surf, player_rect)

        # --- Enemies ---
        enemy_list = move_enemies(enemy_list)

        # --- Collision check ---
        is_playing = collisions(player_rect, enemy_list)

        # --- Update high score ---
        if score > high_score:
            high_score = score

    else:
        draw_menu()

    pygame.display.update()
    clock.tick(60)  # Cap at 60 FPS

# Save high score to file when the game closes
with open("highscore.txt", "w") as file:
    file.write(str(high_score))

pygame.quit()