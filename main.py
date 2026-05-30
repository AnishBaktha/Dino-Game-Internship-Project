"""Dino Game in Python

A game similar to the famous Chrome Dino Game, built using pygame-ce.
Original intern: @bassemfarid
Additional author: Anish
Commit hash: [paste your commit hash here after committing]
"""

import pygame
import random

pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Dino Game")
clock = pygame.time.Clock()
running = True

# Game state variables
is_playing = False  # Start on the menu screen
GROUND_Y = 300
JUMP_SPEED = -10

# ↓↓ Player height change ↓↓
PLAYER_HOVER_HEIGHT = 45  # Pixels above GROUND_Y the plane cruises at rest (0 = sitting on the ground)
# ↑↑ Player height change ↑↑

PLAYER_FLOOR_Y = GROUND_Y - PLAYER_HOVER_HEIGHT

# ↓↓ missile height change ↓↓
EGG_HOVER_HEIGHT = 50  # Pixels above GROUND_Y the egg flies (0 = sitting on the ground)
# ↑↑ Egg height change ↑↑

EGG_FLOOR_Y = GROUND_Y - EGG_HOVER_HEIGHT

# Load level assets (loaded once outside the loop for performance)
SKY_SURF = pygame.image.load("graphics/level/sky.png").convert()
GROUND_SURF = pygame.image.load("graphics/level/ground.png").convert()

game_font = pygame.font.SysFont("couriernew", 40, bold=True)

# --- Player assets ---
player_walk_1 = pygame.image.load("graphics/player/player_walk_1.png").convert_alpha()
player_walk_2 = pygame.image.load("graphics/player/player_walk_2.png").convert_alpha()
player_jump_surf = pygame.image.load("graphics/player/player_jump.png").convert_alpha()

player_walk = [player_walk_1, player_walk_2]
player_index = 0
player_surf = player_walk[player_index]
player_rect = player_surf.get_rect(bottomleft=(80, PLAYER_FLOOR_Y))

# --- Enemy assets ---
egg_frame_1 = pygame.image.load("graphics/missile/missile_1.png").convert_alpha()
egg_frame_2 = pygame.image.load("graphics/missile/missile_2.png").convert_alpha()
egg_frames = [egg_frame_1, egg_frame_2]
egg_frame_index = 0
egg_surf = egg_frames[egg_frame_index]

# --- Lives assets ---
lives_surfs = {
    3: pygame.image.load("graphics/lives/3_lives.png").convert_alpha(),
    2: pygame.image.load("graphics/lives/2_lives.png").convert_alpha(),
    1: pygame.image.load("graphics/lives/1_life.png").convert_alpha(),
}

# --- Player state ---
players_gravity_speed = 0
jump_count = 0           # Tracks how many times the player has jumped (max 2)
player_lives = 3

# --- Invincibility state ---
# After a hit the player gets a brief window of invincibility so one missile
# can't drain multiple lives in a single pass.
INVINCIBILITY_DURATION = 90  # frames at 60 fps (~1.5 seconds)
invincibility_timer = 0      # counts down each frame; 0 = vulnerable

# --- Tilt state ---
# Angle in degrees: positive = nose-up (leaning back), 0 = upright.
# We drive a *target* angle based on jump phase and lerp toward it each frame
# so all transitions are silky smooth.
#
# Phase logic per jump:
#   • On jump press   → target snaps to +TILT_MAX immediately (lerp handles smoothing)
#   • While rising    → target stays at +TILT_MAX
#   • Once falling    → target moves toward 0 (or back to TILT_MAX for double-jump)
#   • On landing      → target = 0, angle lerps back to upright
#
# Double-jump: the lerp rate is doubled so the rotation visually accelerates,
# but the angle is still capped at TILT_MAX.
tilt_angle = 0.0
tilt_target = 0.0
# Base lerp strength (fraction of remaining gap closed per frame at 60 fps).
# ~0.14 gives a roughly 10-frame ease-in; doubled for double-jump → ~5 frames.
TILT_LERP_BASE = 0.14
TILT_MAX = 30.0          # Maximum tilt angle (degrees)
TILT_VEL_SCALE = 6.0     # Velocity (px/frame) at which full tilt is reached — lower = tilts faster
tilt_lerp = TILT_LERP_BASE

# --- Ground scroll state ---
# The ground scrolls at a fraction of enemy_speed so it feels like parallax.
GROUND_SPEED_RATIO = 0.6   # 1.0 = same speed as missiles, 0.5 = half speed
ground_scroll_x = 0        # Current left-edge x offset (counts down, wraps at image width)

# --- Enemy state ---
enemy_list = []
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
    current_time = pygame.time.get_ticks() // 100 - start_time

    score_surf = game_font.render(f"Score: {current_time}", False, "#b0a3ae")
    score_rect = score_surf.get_rect(center=(400, 50))
    screen.blit(score_surf, score_rect)

    return current_time


def draw_lives():
    """Draw the current lives sprite in the top-left corner."""
    if player_lives in lives_surfs:
        screen.blit(lives_surfs[player_lives], (20, 30))


def animate_player():
    """Switch between walk frames, or show jump frame when airborne."""
    global player_index, player_surf

    if player_rect.bottom < PLAYER_FLOOR_Y:
        player_surf = player_jump_surf
    else:
        player_index += 0.1
        if player_index >= len(player_walk):
            player_index = 0
        player_surf = player_walk[int(player_index)]


def animate_egg():
    """Cycle the egg enemy between its two animation frames."""
    global egg_frame_index, egg_surf

    egg_frame_index = 1 - egg_frame_index
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

    players_gravity_speed += 0.25
    player_rect.y += players_gravity_speed

    if player_rect.bottom >= PLAYER_FLOOR_Y:
        player_rect.bottom = PLAYER_FLOOR_Y
        players_gravity_speed = 0  # clear accumulated fall speed so next jump has no delay
        jump_count = 0


def update_tilt():
    """
    Map vertical velocity directly to a tilt target so the angle transitions
    continuously through the arc — no sudden flip at the peak.

    Velocity is normalised against TILT_VEL_SCALE (the speed at which the
    plane reaches full tilt) and clamped to [-1, 1], then scaled to TILT_MAX.
    This means:
      • Fast rising  → smoothly approaches +TILT_MAX  (nose up)
      • At apex (vy≈0) → naturally near 0°
      • Fast falling → smoothly approaches -TILT_MAX  (nose down)
      • Grounded     → snaps target to 0 so it levels on landing
    """
    global tilt_angle, tilt_target, tilt_lerp

    grounded = player_rect.bottom >= PLAYER_FLOOR_Y

    if grounded:
        tilt_target = 0.0
        tilt_lerp = TILT_LERP_BASE
    else:
        # Normalise velocity: full tilt is reached at ±TILT_VEL_SCALE px/frame.
        # Negate so nose-up (negative vy = rising) maps to positive angle.
        normalised = -players_gravity_speed / TILT_VEL_SCALE
        normalised = max(-1.0, min(1.0, normalised))
        tilt_target = normalised * TILT_MAX

    # Exponential lerp toward target — fast at first, settles gently.
    tilt_angle += (tilt_target - tilt_angle) * tilt_lerp


def get_player_rotated():
    """
    Rotate player_surf by tilt_angle degrees pivoting on the bottom-left corner.
    Returns (rotated_surf, blit_pos) so both drawing and mask collision can use
    the same rotated surface without rotating twice per frame.
    """
    import math

    if abs(tilt_angle) < 0.1:
        return player_surf, pygame.Vector2(player_rect.topleft)

    w, h = player_surf.get_size()
    pivot_local = pygame.Vector2(0, h)
    pivot_world = pygame.Vector2(player_rect.bottomleft)

    rotated_surf = pygame.transform.rotate(player_surf, tilt_angle)
    rw, rh = rotated_surf.get_size()

    rad = math.radians(tilt_angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    cx, cy = w / 2, h / 2
    px, py = pivot_local.x - cx, pivot_local.y - cy
    rotated_px = px * cos_a - py * sin_a
    rotated_py = px * sin_a + py * cos_a

    pivot_in_rot = pygame.Vector2(rw / 2 + rotated_px, rh / 2 + rotated_py)
    blit_pos = pivot_world - pivot_in_rot

    return rotated_surf, blit_pos


def draw_player_tilted():
    """Draw the player at the correct rotated position."""
    rotated_surf, blit_pos = get_player_rotated()
    screen.blit(rotated_surf, blit_pos)


def move_enemies(enemies):
    """
    Move all enemies left, draw them, and return the updated list.
    Each entry is a Rect (position/size); the mask is built fresh each frame
    from egg_surf in collisions() so it always matches the current anim frame.
    """
    if enemies:
        for enemy in enemies:
            enemy.x -= enemy_speed
            screen.blit(egg_surf, enemy)
        enemies = [enemy for enemy in enemies if enemy.right > 0]
    return enemies


def collisions(player_rect, enemies):
    """
    Pixel-perfect mask collision between the rotated player and each missile.

    On a hit:
      - The colliding missile is removed from the list.
      - player_lives is decremented and invincibility_timer is set.
      - Returns (False, enemies) only when lives reach 0 (game over).
      - While invincible, collisions are skipped entirely.

    Returns (still_alive: bool, updated_enemies: list).
    """
    global player_lives, invincibility_timer

    if invincibility_timer > 0:
        return True, enemies

    rotated_player_surf, player_blit_pos = get_player_rotated()
    player_mask = pygame.mask.from_surface(rotated_player_surf)
    egg_mask    = pygame.mask.from_surface(egg_surf)

    for enemy_rect in enemies:
        offset = (
            int(enemy_rect.x - player_blit_pos.x),
            int(enemy_rect.y - player_blit_pos.y),
        )
        if player_mask.overlap(egg_mask, offset):
            enemies.remove(enemy_rect)
            player_lives -= 1
            if player_lives <= 0:
                return False, enemies
            invincibility_timer = INVINCIBILITY_DURATION
            return True, enemies

    return True, enemies


def draw_menu():
    """Draw the start/game-over menu screen."""
    MENU_COLOR = "#314e71"

    screen.blit(SKY_SURF, (0, 0))
    screen.blit(GROUND_SURF, (0, GROUND_Y))

    title_surf = game_font.render("Fly to Survive", False, MENU_COLOR)
    title_rect = title_surf.get_rect(center=(400, 100))

    controls_surf = game_font.render("SPACE to start  |  Double jump", False, MENU_COLOR)
    controls_rect = controls_surf.get_rect(center=(400, 180))

    high_score_surf = game_font.render(f"High Score: {high_score}", False, MENU_COLOR)
    high_score_rect = high_score_surf.get_rect(center=(400, 260))

    screen.blit(title_surf, title_rect)
    screen.blit(controls_surf, controls_rect)
    screen.blit(high_score_surf, high_score_rect)

    if score > 0:
        game_over_surf = game_font.render(f"Final Score: {score}", False, MENU_COLOR)
        game_over_rect = game_over_surf.get_rect(center=(400, 320))
        screen.blit(game_over_surf, game_over_rect)


# ---------- MAIN GAME LOOP ----------

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if is_playing:
            player_input(event)

            if event.type == enemy_timer:
                enemy_list.append(
                    egg_surf.get_rect(
                        bottomleft=(random.randint(850, 1100), EGG_FLOOR_Y)
                    )
                )

            if event.type == animation_timer:
                animate_player()

            if event.type == egg_animation_timer:
                animate_egg()

        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                is_playing = True

                enemy_list.clear()
                player_rect.bottomleft = (80, PLAYER_FLOOR_Y)
                players_gravity_speed = 0
                jump_count = 0
                tilt_angle = 0.0
                tilt_target = 0.0
                tilt_lerp = TILT_LERP_BASE
                ground_scroll_x = 0
                player_lives = 3
                invincibility_timer = 0

                start_time = pygame.time.get_ticks() // 100

    if is_playing:
        screen.blit(SKY_SURF, (0, 0))

        score = display_score()

        enemy_speed = 5 + score // 50

        # Scroll ground slightly slower than missiles for a parallax feel.
        # Two tiles placed end-to-end; once the first scrolls fully off the
        # left edge it wraps around so the seam is invisible.
        ground_w = GROUND_SURF.get_width()
        ground_scroll_x -= enemy_speed * GROUND_SPEED_RATIO
        if ground_scroll_x <= -ground_w:
            ground_scroll_x += ground_w
        screen.blit(GROUND_SURF, (ground_scroll_x,            GROUND_Y))
        screen.blit(GROUND_SURF, (ground_scroll_x + ground_w, GROUND_Y))

        apply_gravity()
        update_tilt()

        # Flash the player every other 6-frame block while invincible
        if invincibility_timer > 0:
            invincibility_timer -= 1
            if (invincibility_timer // 6) % 2 == 0:
                draw_player_tilted()
        else:
            draw_player_tilted()

        draw_lives()

        enemy_list = move_enemies(enemy_list)

        is_playing, enemy_list = collisions(player_rect, enemy_list)

        if score > high_score:
            high_score = score

    else:
        draw_menu()

    pygame.display.update()
    clock.tick(60)

# Save high score to file when the game closes
with open("highscore.txt", "w") as file:
    file.write(str(high_score))

pygame.quit()