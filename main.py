import pygame
import random

pygame.init()

screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Dino Game Internship Project")

clock = pygame.time.Clock()
game_font = pygame.font.Font(pygame.font.get_default_font(), 40)

running = True
is_playing = False

GROUND_Y = 300
JUMP_SPEED = -20

player_walk_1 = pygame.image.load(
    "graphics/player/player_walk_1.png"
).convert_alpha()
player_walk_2 = pygame.image.load(
    "graphics/player/player_walk_2.png"
).convert_alpha()

player_walk = [player_walk_1, player_walk_2]
player_index = 0
player_surf = player_walk[player_index]
player_rect = player_surf.get_rect(bottomleft=(80, GROUND_Y))

egg_surf = pygame.image.load("graphics/egg/egg_1.png").convert_alpha()

SKY_SURF = pygame.image.load("graphics/level/sky.png").convert()
GROUND_SURF = pygame.image.load("graphics/level/ground.png").convert()

players_gravity_speed = 0
jump_count = 0

enemy_list = []

score = 0
high_score = 0
start_time = 0

enemy_speed = 5

enemy_timer = pygame.USEREVENT + 1
pygame.time.set_timer(enemy_timer, 1200)

animation_timer = pygame.USEREVENT + 2
pygame.time.set_timer(animation_timer, 150)

try:
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())
except:
    high_score = 0


def display_score():
    current_time = pygame.time.get_ticks() // 100 - start_time
    score_surf = game_font.render(f"Score: {current_time}", False, "Black")
    score_rect = score_surf.get_rect(center=(400, 50))

    pygame.draw.rect(screen, "#c0e8ec", score_rect.inflate(20, 20))
    pygame.draw.rect(screen, "#c0e8ec", score_rect.inflate(20, 20), 8)

    screen.blit(score_surf, score_rect)

    return current_time


def animate_player():
    global player_index
    global player_surf

    player_index += 0.1

    if player_index >= len(player_walk):
        player_index = 0

    player_surf = player_walk[int(player_index)]


def player_input(event):
    global players_gravity_speed
    global jump_count

    if (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_SPACE
        and jump_count < 2
    ):
        players_gravity_speed = JUMP_SPEED
        jump_count += 1


def apply_gravity():
    global players_gravity_speed
    global jump_count

    players_gravity_speed += 1
    player_rect.y += players_gravity_speed

    if player_rect.bottom >= GROUND_Y:
        player_rect.bottom = GROUND_Y
        jump_count = 0


def move_enemies(enemies):
    global enemy_speed

    if enemies:
        for enemy in enemies:
            enemy.x -= enemy_speed
            screen.blit(egg_surf, enemy)

        enemies = [enemy for enemy in enemies if enemy.right > 0]

    return enemies


def collisions(player, enemies):
    for enemy in enemies:
        if player.colliderect(enemy):
            return False

    return True


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if is_playing:
            player_input(event)

            if event.type == enemy_timer:
                enemy_list.append(
                    egg_surf.get_rect(
                        bottomleft=(random.randint(850, 1100), GROUND_Y)
                    )
                )

            if event.type == animation_timer:
                animate_player()

        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                is_playing = True

                enemy_list.clear()

                player_rect.bottom = GROUND_Y
                players_gravity_speed = 0
                jump_count = 0

                start_time = pygame.time.get_ticks() // 100

    if is_playing:
        screen.blit(SKY_SURF, (0, 0))
        screen.blit(GROUND_SURF, (0, GROUND_Y))

        score = display_score()

        enemy_speed = 5 + score // 50

        apply_gravity()

        screen.blit(player_surf, player_rect)

        enemy_list = move_enemies(enemy_list)

        is_playing = collisions(player_rect, enemy_list)

        if score > high_score:
            high_score = score

    else:
        screen.fill("black")

        title_surf = game_font.render("Dino Game", False, "White")
        title_rect = title_surf.get_rect(center=(400, 100))

        controls_surf = game_font.render(
            "Press SPACE to Start / Double Jump",
            False,
            "White",
        )
        controls_rect = controls_surf.get_rect(center=(400, 180))

        high_score_surf = game_font.render(
            f"High Score: {high_score}",
            False,
            "White",
        )
        high_score_rect = high_score_surf.get_rect(center=(400, 260))

        if score > 0:
            game_over_surf = game_font.render(
                f"Final Score: {score}",
                False,
                "White",
            )
            game_over_rect = game_over_surf.get_rect(center=(400, 320))

            screen.blit(game_over_surf, game_over_rect)

        screen.blit(title_surf, title_rect)
        screen.blit(controls_surf, controls_rect)
        screen.blit(high_score_surf, high_score_rect)

    pygame.display.update()
    clock.tick(60)

with open("highscore.txt", "w") as file:
    file.write(str(high_score))

pygame.quit()