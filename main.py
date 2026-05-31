"""Dino Game in Python

The better Chrome Dino Game because jets, built using pygame-ce.
Original intern: @bassemfarid
Additional author: Anish Baktharaman
Commit hash: e6aa45d
"""

import pygame
import random

pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Dino Game")
clock = pygame.time.Clock()
running = True

# game state
is_playing = False
ground_y = 300
jump_speed = -10

player_hover = 45
player_mountains = ground_y - player_hover

missile_hover = 50
missile_mountains = ground_y - missile_hover

# level images
sky_sprite = pygame.image.load("graphics/level/sky.png").convert()
ground_sprite = pygame.image.load("graphics/level/ground.png").convert()

game_font = pygame.font.SysFont("couriernew", 40, bold=True)

# player images
player_walk_1 = pygame.image.load("graphics/player/player_walk_1.png").convert_alpha()
player_walk_2 = pygame.image.load("graphics/player/player_walk_2.png").convert_alpha()
player_jump = pygame.image.load("graphics/player/player_jump.png").convert_alpha()

player_walk = [player_walk_1, player_walk_2]
player_index = 0
player_surf = player_walk[player_index]
player_rect = player_surf.get_rect(bottomleft=(80, player_mountains))

# missile images
missile_frame_1 = pygame.image.load("graphics/missile/missile_1.png").convert_alpha()
missile_frame_2 = pygame.image.load("graphics/missile/missile_2.png").convert_alpha()
missile_frames = [missile_frame_1, missile_frame_2]
missile_frame_index = 0
missile_surf = missile_frames[missile_frame_index]

# lives images
lives_surfs = {
    3: pygame.image.load("graphics/lives/3_lives.png").convert_alpha(),
    2: pygame.image.load("graphics/lives/2_lives.png").convert_alpha(),
    1: pygame.image.load("graphics/lives/1_life.png").convert_alpha(),
}

# player variables
players_gravity_speed = 0
jump_count = 0
player_lives = 3

# invincibility after getting hit
immortality_length = 90
invincibility_timer = 0
player_visible = True
flash_counter = 0

# tilt variables
tilt_angle = 0
target_tilt = 0

# ground scrolling - two copies of the ground tile
ground_w = ground_sprite.get_width()
ground_x1 = 0
ground_x2 = ground_w
groundspeed = 0.6  # change this to make the ground scroll faster or slower

# enemy variables
enemy_list = []
enemy_speed = 5

# score variables
score = 0
high_score = 0
start_time = 0

# timer events
enemy_timer = pygame.USEREVENT + 1
pygame.time.set_timer(enemy_timer, 1200)

animation_timer = pygame.USEREVENT + 2
pygame.time.set_timer(animation_timer, 150)

missile_animation_timer = pygame.USEREVENT + 3
pygame.time.set_timer(missile_animation_timer, 300)

# load high score from file
try:
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())
except FileNotFoundError:
    high_score = 0


# functions

def display_score():
    current_time = pygame.time.get_ticks() // 100 - start_time
    score_surf = game_font.render(f"Score: {current_time}", False, "#b0a3ae")
    score_rect = score_surf.get_rect(center=(400, 50))
    screen.blit(score_surf, score_rect)
    return current_time


def draw_lives():
    if player_lives in lives_surfs:
        screen.blit(lives_surfs[player_lives], (20, 30))


def animate_player():
    global player_index, player_surf
    if player_rect.bottom < player_mountains:
        player_surf = player_jump
    else:
        player_index += 0.1
        if player_index >= len(player_walk):
            player_index = 0
        player_surf = player_walk[int(player_index)]


def animate_missile():
    global missile_frame_index, missile_surf
    missile_frame_index = 1 - missile_frame_index
    missile_surf = missile_frames[missile_frame_index]


def player_input(event):
    global players_gravity_speed, jump_count
    if (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_SPACE
        and jump_count < 2
    ):
        players_gravity_speed = jump_speed
        jump_count += 1


def apply_gravity():
    global players_gravity_speed, jump_count
    players_gravity_speed += 0.25
    player_rect.y += players_gravity_speed
    if player_rect.bottom >= player_mountains:
        player_rect.bottom = player_mountains
        players_gravity_speed = 0
        jump_count = 0


def update_tilt():
    global tilt_angle, target_tilt
    if player_rect.bottom >= player_mountains:
        target_tilt = 0
    elif players_gravity_speed < 0:
        target_tilt = 30   # going up, nose up
    else:
        target_tilt = -30  # falling, nose down

    # step toward the target angle a little each frame
    if tilt_angle < target_tilt:
        tilt_angle += 3
    elif tilt_angle > target_tilt:
        tilt_angle -= 3


def get_rotated_player():
    rotated = pygame.transform.rotate(player_surf, tilt_angle)
    rotated_rect = rotated.get_rect(midbottom=player_rect.midbottom)
    return rotated, rotated_rect


def move_enemies(enemies):
    if enemies:
        for enemy in enemies:
            enemy.x -= enemy_speed
            screen.blit(missile_surf, enemy)
        enemies = [enemy for enemy in enemies if enemy.right > 0]
    return enemies


def collisions(rotated_rect, enemies):
    global player_lives, invincibility_timer, player_visible, flash_counter
    if invincibility_timer > 0:
        return True, enemies

    # shrink the box a bit so the corners of the rotated image don't count as hits
    hitbox = rotated_rect.inflate(-20, -20)

    for enemy_rect in enemies:
        if hitbox.colliderect(enemy_rect):
            enemies.remove(enemy_rect)
            player_lives -= 1
            if player_lives <= 0:
                return False, enemies
            invincibility_timer = immortality_length
            player_visible = True
            flash_counter = 0
            return True, enemies
    return True, enemies


def draw_menu():
    menu_colour = "#314e71"
    screen.blit(sky_sprite, (0, 0))
    screen.blit(ground_sprite, (0, ground_y))
    title_surf = game_font.render("Fly to Survive", False, menu_colour)
    title_rect = title_surf.get_rect(center=(400, 100))
    controls_surf = game_font.render("Spacebar to start  |  Double jump", False, menu_colour)
    controls_rect = controls_surf.get_rect(center=(400, 180))
    high_score_surf = game_font.render(f"High Score: {high_score}", False, menu_colour)
    high_score_rect = high_score_surf.get_rect(center=(400, 260))
    screen.blit(title_surf, title_rect)
    screen.blit(controls_surf, controls_rect)
    screen.blit(high_score_surf, high_score_rect)
    if score > 0:
        game_over_surf = game_font.render(f"Final Score: {score}", False, menu_colour)
        game_over_rect = game_over_surf.get_rect(center=(400, 320))
        screen.blit(game_over_surf, game_over_rect)


# main game loop

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if is_playing:
            player_input(event)

            if event.type == enemy_timer:
                enemy_list.append(
                    missile_surf.get_rect(
                        bottomleft=(random.randint(850, 1100), missile_mountains)
                    )
                )

            if event.type == animation_timer:
                animate_player()

            if event.type == missile_animation_timer:
                animate_missile()

        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                is_playing = True

                # reset everything for a new game
                enemy_list.clear()
                player_rect.bottomleft = (80, player_mountains)
                players_gravity_speed = 0
                jump_count = 0
                tilt_angle = 0
                target_tilt = 0
                ground_x1 = 0
                ground_x2 = ground_w
                player_lives = 3
                invincibility_timer = 0
                player_visible = True
                flash_counter = 0

                start_time = pygame.time.get_ticks() // 100

    if is_playing:
        screen.blit(sky_sprite, (0, 0))

        score = display_score()

        # speed increases gradually as score goes up
        enemy_speed = 5 + score // 50

        # move both ground pieces left, loop them back when off screen
        ground_x1 -= enemy_speed * groundspeed
        ground_x2 -= enemy_speed * groundspeed
        if ground_x1 <= -ground_w:
            ground_x1 = ground_w
        if ground_x2 <= -ground_w:
            ground_x2 = ground_w
        screen.blit(ground_sprite, (ground_x1, ground_y))
        screen.blit(ground_sprite, (ground_x2, ground_y))

        apply_gravity()
        update_tilt()

        rotated, rotated_rect = get_rotated_player()

        # flash the player while invincible
        if invincibility_timer > 0:
            invincibility_timer -= 1
            flash_counter += 1
            if flash_counter >= 6:
                player_visible = not player_visible
                flash_counter = 0
        else:
            player_visible = True

        if player_visible:
            screen.blit(rotated, rotated_rect)

        draw_lives()

        enemy_list = move_enemies(enemy_list)

        is_playing, enemy_list = collisions(rotated_rect, enemy_list)

        if score > high_score:
            high_score = score

    else:
        draw_menu()

    pygame.display.update()
    clock.tick(60)

# high score save on close
with open("highscore.txt", "w") as file:
    file.write(str(high_score))

pygame.quit()





# *** WORK ON POWERUPS ON MONDAY: Rocket Defense***