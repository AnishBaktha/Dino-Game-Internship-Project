"""
Dino Game in Python
The better Chrome Dino Game trust.
Original intern: @bassemfarid
Additional author: Anish Baktharaman
Commit hash: idk
"""

import pygame
import random
import math
import gif_pygame

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Dino Game")
clock = pygame.time.Clock()
running = True

# sounds
game_over = pygame.mixer.Sound("sfx/Dead.mp3")
hit = pygame.mixer.Sound("sfx/Player_Hit.mp3")
background = pygame.mixer.Sound("sfx/Background.mp3")
music = pygame.mixer.Sound("sfx/Music_2.mp3")
jump = pygame.mixer.Sound("sfx/Jump.mp3")
water = pygame.mixer.Sound("sfx/Water.mp3")
water.set_volume(2)
background.set_volume(0.3)
music.set_volume(1.2)
hit.set_volume(3.0)
jump.set_volume(0.5)
background.play(loops=-1)
music.play(loops=-1)
water.play(loops=-1)

# game state
is_playing = False
is_paused = False
ground_y = 300
jump_speed = -20

monkey_vertical = -15
player_ground = ground_y - monkey_vertical

# monkey release
monkey_release = False
monkey_release_move_speed = 6
monkey_release_centered = False

# level images
background_sprite = pygame.transform.scale(pygame.image.load("graphics/level/Background.png").convert(), (800, 400))
foreground_sprite = pygame.image.load("graphics/level/Foreground.png").convert_alpha()
foreground_y = 400 - foreground_sprite.get_height()
ground_sprite = pygame.image.load("graphics/level/ground.png").convert_alpha()
overlay_image = pygame.image.load("graphics/level/Overlay.png").convert_alpha()
game_font = pygame.font.SysFont("couriernew", 40, bold=True)

# monkey images
monkey_run = gif_pygame.load("graphics/monkey/Monkey_run.gif")
monkey_still = gif_pygame.load("graphics/monkey/Monkey_still.gif")
gif_pygame.transform.scale(monkey_still, (90, 90))
gif_pygame.transform.scale(monkey_run, (100, 100))
monkey_jump_image = pygame.image.load("graphics/monkey/Monkey_jump.png").convert_alpha()
monkey_jump_image = pygame.transform.scale(monkey_jump_image, (130, 130))
monkey_image = monkey_run.get_surfaces()[0]
monkey_hitbox = monkey_image.get_rect(bottomleft=(10, player_ground))

# rock obstacle images
rock_images = [
    pygame.image.load("graphics/obstacles/Rock_1.png").convert_alpha(),
    pygame.image.load("graphics/obstacles/Rock_2.png").convert_alpha(),
    pygame.image.load("graphics/obstacles/Rock_3.png").convert_alpha(),
]

# lives images
lives_surfs = [
    pygame.image.load("graphics/lives/3_lives.png").convert_alpha(),
    pygame.image.load("graphics/lives/2_lives.png").convert_alpha(),
    pygame.image.load("graphics/lives/1_life.png").convert_alpha(),
]

# falling object images
coconut_image = pygame.image.load("graphics/obstacles/coconut.png").convert_alpha()
coconut_image = pygame.transform.scale(coconut_image, (70, 70))
extra_life_image = pygame.image.load("graphics/lives/extra_life.png").convert_alpha()

# life received
life_recieved_image = pygame.image.load("graphics/lives/life_recieved.png").convert_alpha()
life_received_image = pygame.transform.scale(life_recieved_image, (50,50))
life_recieved_length= 60
life_received_timer = 0

indicator_height = 40
coconut_indicator_image = pygame.image.load("graphics/indicators/coconut_indicator.png").convert_alpha()
life_indicator_image    = pygame.image.load("graphics/indicators/life_indicator.png").convert_alpha()

# Variables
jump_count = 0
player_lives = 3
immortality_length = 90
invincibility_timer = 0
player_visible = True
monkey_flashing = 0
player_gravspeed = 0

# Monkey flip
flipping_speed = 0.1
monkey_orient = 0
flipping = 0.0

# Ground scrolling
ground_w = ground_sprite.get_width()
ground_x1 = 0
ground_x2 = ground_w
groundspeed = 0.6

# Back ground layer parallaxing
back_ground_x1 = 0
back_ground_x2 = ground_w
back_groundspeed = 0.4

# Parallax layer scrolling
background_w = 800
foreground_w = foreground_sprite.get_width()
background_scroll_speed = 0.2
foreground_scroll_speed = 0.35
background_x1 = 0
background_x2 = background_w
foreground_x1 = 0
foreground_x2 = foreground_w

# track rock position
enemy_rects = []
enemy_surfs = []
enemy_xpos = []

enemy_speed = 5

score_offset = 940   # for testing
score = 0

high_score = 0
start_time = 0
pause_time = 0
pause_start_time = 0

# timer related functions
enemy_timer = pygame.USEREVENT + 1
pygame.time.set_timer(enemy_timer, 1200)

# falling things
spawn_delay = 1500
spawn_delay_slow = 4000
indicator_timer = 800
fallingthings_gravity = 0.6
coconut_bouncing = -14
life_spawnrate = 0.15

# falling_objects entries are lists: [x, y, fall_speed, kind, has_bounced]
fall_X = 0
fall_Y = 1
fall_speed = 2
fall_type = 3
fall_BOUNCED = 4

# indicators lists
indicator_X = 0
indicator_type = 1
indicator_time_left = 2

falling_objects = []
indicators = []
fall_obj_timer = pygame.USEREVENT + 2
pygame.time.set_timer(fall_obj_timer, spawn_delay_slow)

max_objects = 3

try:
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())
except FileNotFoundError:
    high_score = 0


def fall_spawn_interval(current_score):
    t = min(1.0, (current_score - 1000) / 1000.0)
    return int(spawn_delay_slow + t * (spawn_delay - spawn_delay_slow))


def scroll_pair(x1, x2, speed, sprite_w):
    x1 -= speed
    x2 -= speed
    old_x1, old_x2 = x1, x2
    if old_x1 <= -sprite_w:
        x1 = old_x2 + sprite_w
    if old_x2 <= -sprite_w:
        x2 = old_x1 + sprite_w
    return x1, x2


def display_score():
    global score
    if is_paused:
        current_time = pause_start_time - start_time - pause_time
    else:
        current_time = (pygame.time.get_ticks() // 100) - start_time - pause_time

    score = current_time + score_offset

    score_surf = game_font.render(f"Score: {score}", False, "#ebc034")
    score_position = score_surf.get_rect(center=(400, 50))
    screen.blit(score_surf, score_position)
    return score


def draw_lives():
    if player_lives >= 1:
        screen.blit(lives_surfs[3 - player_lives], (20, 30))


def monkey_animate():
    global monkey_image
    keys = pygame.key.get_pressed()
    if monkey_hitbox.bottom < player_ground:
        monkey_image = monkey_jump_image
    elif monkey_release and monkey_release_centered and (keys[pygame.K_a] or keys[pygame.K_d]):
        frames = monkey_run.get_surfaces()
        frame_index = (pygame.time.get_ticks() // 150) % len(frames)
        monkey_image = frames[frame_index]
    elif monkey_release and monkey_release_centered:
        frames = monkey_still.get_surfaces()
        frame_index = (pygame.time.get_ticks() // 150) % len(frames)
        monkey_image = frames[frame_index]
    else:
        frames = monkey_run.get_surfaces()
        frame_index = (pygame.time.get_ticks() // 150) % len(frames)
        monkey_image = frames[frame_index]

def flip(surface):
    w, h = surface.get_size()
    if flipping <= 0.5:
        monkey_squish = 1.0 - (flipping / 0.5)
    else:
        monkey_squish = (flipping - 0.5) / 0.5
    new_orientation = max(1, int(w * monkey_squish))
    squishing = pygame.transform.scale(surface, (new_orientation, h))
    if flipping > 0.5:
        squishing = pygame.transform.flip(squishing, True, False)
    return squishing, new_orientation


def music_switch():
    global music
    if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
        music.stop()
        music = pygame.mixer.Sound("sfx/Music_1.mp3")
        music.set_volume(1.2)
        music.play(loops=-1)
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_2:
        music.stop()
        music = pygame.mixer.Sound("sfx/Music_2.mp3")
        music.set_volume(1.2)
        music.play(loops=-1)
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_3:
        music.stop()
        music = pygame.mixer.Sound("sfx/Music.mp3")
        music.set_volume(1.2)
        music.play(loops=-1)

def player_input(event):
    global player_gravspeed, jump_count, monkey_orient, jump_cancel_active
    if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
        monkey_orient = 0
    if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
        monkey_orient = 1
    if event.type == pygame.KEYDOWN and event.key == pygame.K_w and jump_count < 2:
        player_gravspeed = jump_speed
        jump_count += 1
        jump.play()
    if event.type == pygame.KEYDOWN and event.key == pygame.K_s and monkey_hitbox.bottom < player_ground:
        player_gravspeed = jump_cancel_speed
        jump_cancel_active = True


def gravity():
    global player_gravspeed, jump_count
    player_gravspeed += 1
    monkey_hitbox.y += player_gravspeed
    if monkey_hitbox.bottom >= player_ground:
        monkey_hitbox.bottom = player_ground
        player_gravspeed = 0
        jump_count = 0


def move_enemies(rects, surfs, xpos, speed_modifier, should_move):
    updated_rects = []
    updated_surfs = []
    updated_xpos = []

    for i in range(len(rects)):
        if should_move:
            xpos[i] -= speed_modifier * groundspeed
            rects[i].x = int(xpos[i])

        screen.blit(surfs[i], rects[i])

        if rects[i].right > 0:
            updated_rects.append(rects[i])
            updated_surfs.append(surfs[i])
            updated_xpos.append(xpos[i])

    return updated_rects, updated_surfs, updated_xpos


def collisions(monkey_hitbox, rects, surfs, xpos):
    global player_lives, invincibility_timer, player_visible, monkey_flashing
    if invincibility_timer > 0:
        return True, rects, surfs, xpos

    player_left = monkey_hitbox.x + 40
    player_top = monkey_hitbox.y + 35
    player_width = monkey_hitbox.width - 80
    player_height = monkey_hitbox.height - 70

    for i in range(len(rects)):
        rock_left = rects[i].x + 25
        rock_top = rects[i].y + 25
        rock_width = rects[i].width - 50
        rock_height = rects[i].height - 50

        if player_left < rock_left + rock_width and player_left + player_width > rock_left and player_top < rock_top + rock_height and player_top + player_height > rock_top:
            rects.pop(i)
            surfs.pop(i)
            xpos.pop(i)
            player_lives -= 1
            hit.play()

            if player_lives <= 0:
                game_over.play()
                return False, rects, surfs, xpos
            invincibility_timer = immortality_length
            player_visible = True
            monkey_flashing = 0
            return True, rects, surfs, xpos

    return True, rects, surfs, xpos


def update_falling_objects(dt_ms):
    global player_lives, invincibility_timer, player_visible, monkey_flashing
    global life_received_timer, is_playing, falling_objects

    player_left = monkey_hitbox.x + 40
    player_top = monkey_hitbox.y + 35
    player_width = monkey_hitbox.width - 80
    player_height = monkey_hitbox.height - 70

    surviving = []
    for obj in falling_objects:
        img = coconut_image if obj[fall_type] == "coconut" else extra_life_image
        img_width, img_height = img.get_size()

        obj[fall_speed] += fallingthings_gravity
        obj[fall_Y] += obj[fall_speed]

        if not obj[fall_BOUNCED] and obj[fall_Y] + img_height >= player_ground:
            obj[fall_Y] = player_ground - img_height
            obj[fall_speed] = coconut_bouncing
            obj[fall_BOUNCED] = True

        if obj[fall_BOUNCED] and obj[fall_Y] > 420:
            continue

        screen.blit(img, (int(obj[fall_X]), int(obj[fall_Y])))

        obj_left = int(obj[fall_X]) + 10
        obj_top = int(obj[fall_Y]) + 10
        obj_width = img_width - 20
        obj_height = img_height - 20

        hit_monkey = (player_left < obj_left + obj_width and player_left + player_width > obj_left
                      and player_top < obj_top + obj_height and player_top + player_height > obj_top)

        if hit_monkey:
            if obj[fall_type] == "coconut":
                if invincibility_timer <= 0:
                    player_lives -= 1
                    hit.play()
                    if player_lives <= 0:
                        game_over.play()
                        is_playing = False
                    else:
                        invincibility_timer = immortality_length
                        player_visible = True
                        monkey_flashing = 0
                continue
            else:
                if player_lives < 3:
                    player_lives += 1
                life_received_timer = life_recieved_length
                continue

        surviving.append(obj)

    falling_objects = surviving


def update_indicators(dt_ms):
    surviving = []
    for ind in indicators:
        ind[indicator_time_left] -= dt_ms
        img = coconut_indicator_image if ind[indicator_type] == "coconut" else life_indicator_image
        img_width, img_height = img.get_size()
        draw_y = ground_y - indicator_height - img_height
        screen.blit(img, (ind[indicator_X] - img_width // 2, draw_y))

        if ind[indicator_time_left] <= 0:
            falling_objects.append([float(ind[indicator_X] - img_width // 2), -img_height, 0.0, ind[indicator_type], False])
        else:
            surviving.append(ind)
    indicators.clear()
    indicators.extend(surviving)


def spawn_falling_group():
    if not monkey_release_centered:
        return
    if score >= 2000:
        return
    active_count = len(falling_objects) + len(indicators)
    if active_count >= max_objects:
        return

    slots = max_objects - active_count
    count = random.randint(1, min(3, slots))

    for _ in range(count):
        x = random.randint(60, 740)
        kind = "life" if random.random() < life_spawnrate else "coconut"
        indicators.append([x, kind, indicator_timer])


def draw_menu():
    menu_colour = "#a6d8af"
    screen.fill((0, 0, 0))
    screen.blit(background_sprite, (0, 0))
    screen.blit(foreground_sprite, (0, foreground_y))
    screen.blit(ground_sprite, (0, ground_y))
    screen.blit(overlay_image, (0, 0))
    title_text = game_font.render("Monkey Run", False, menu_colour)
    title_position = title_text.get_rect(center=(400, 100))
    controls_text = game_font.render("'W' to start", False, menu_colour)
    controls_position = controls_text.get_rect(center=(400, 180))
    highscore_text = game_font.render(f"High Score: {high_score}", False, menu_colour)
    high_score_position = highscore_text.get_rect(center=(400, 260))
    screen.blit(title_text, title_position)
    screen.blit(controls_text, controls_position)
    screen.blit(highscore_text, high_score_position)
    if score > 0:
        endgame_text = game_font.render(f"Final Score: {score}", False, menu_colour)
        final_score_position = endgame_text.get_rect(center=(400, 320))
        screen.blit(endgame_text, final_score_position)


# main game loop

while running:
    dt_ms = clock.get_time()

    for event in pygame.event.get():
        music_switch()
        if event.type == pygame.QUIT:
            running = False

        if is_playing:
            music_switch()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                is_paused = not is_paused
                if is_paused:
                    pause_start_time = pygame.time.get_ticks() // 100
                else:
                    pause_time += (pygame.time.get_ticks() // 100) - pause_start_time

            if not is_paused:
                if monkey_release:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_w and jump_count < 2:
                        player_gravspeed = jump_speed
                        jump_count += 1
                        jump.play()
                else:
                    player_input(event)

                if event.type == enemy_timer and not monkey_release:
                    rock_image = random.choice(rock_images)
                    spawn_x = random.randint(850, 1100)
                    rock_hitbox = rock_image.get_rect(bottomleft=(spawn_x, player_ground))
                    enemy_rects.append(rock_hitbox)
                    enemy_surfs.append(rock_image)
                    enemy_xpos.append(float(spawn_x))

                if event.type == fall_obj_timer and monkey_release and monkey_release_centered:
                    if 1000 <= score < 2000:
                        spawn_falling_group()
                        new_interval = fall_spawn_interval(score)
                        pygame.time.set_timer(fall_obj_timer, new_interval)

        else:
            music_switch()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_w:
                is_playing = True
                is_paused = False
                monkey_release = False
                monkey_release_centered = False

                enemy_rects.clear()
                enemy_surfs.clear()
                enemy_xpos.clear()
                falling_objects.clear()
                indicators.clear()
                life_received_timer = 0
                monkey_hitbox.bottomleft = (80, player_ground)
                player_gravspeed = 0
                jump_count = 0
                ground_x1 = 0
                ground_x2 = ground_w
                back_ground_x1 = 0
                back_ground_x2 = ground_w
                background_x1 = 0
                background_x2 = background_w
                foreground_x1 = 0
                foreground_x2 = foreground_w
                player_lives = 3
                invincibility_timer = 0
                player_visible = True
                monkey_flashing = 0
                pause_time = 0
                monkey_orient = 0
                flipping = 0.0

                pygame.time.set_timer(fall_obj_timer, spawn_delay_slow)

                start_time = pygame.time.get_ticks() // 100

    if is_playing:
        music_switch()
        enemy_speed = 5 + score // 50

        if score >= 1000 and not monkey_release:
            monkey_release = True
            monkey_release_centered = False
            enemy_rects.clear()
            enemy_surfs.clear()
            enemy_xpos.clear()

        if not is_paused:
            if not monkey_release:
                background_x1, background_x2 = scroll_pair(background_x1, background_x2, enemy_speed * background_scroll_speed, background_w)
                foreground_x1, foreground_x2 = scroll_pair(foreground_x1, foreground_x2, enemy_speed * foreground_scroll_speed, foreground_w)

        screen.fill((0, 0, 0))
        screen.blit(background_sprite, (background_x1, 0))
        screen.blit(background_sprite, (background_x2, 0))
        screen.blit(foreground_sprite, (foreground_x1, foreground_y))
        screen.blit(foreground_sprite, (foreground_x2, foreground_y))

        display_score()

        if not is_paused:
            if not monkey_release:
                back_ground_x1, back_ground_x2 = scroll_pair(back_ground_x1, back_ground_x2, enemy_speed * back_groundspeed, ground_w)
                ground_x1, ground_x2 = scroll_pair(ground_x1, ground_x2, enemy_speed * groundspeed, ground_w)

            if monkey_release:
                center_x = 400 - monkey_hitbox.width // 2
                if not monkey_release_centered:
                    if monkey_hitbox.x < center_x:
                        monkey_hitbox.x = min(monkey_hitbox.x + monkey_release_move_speed, center_x)
                    else:
                        monkey_release_centered = True
                else:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_d]:
                        monkey_hitbox.x = min(monkey_hitbox.x + monkey_release_move_speed, 800 - monkey_hitbox.width)
                        monkey_orient = 0
                    if keys[pygame.K_a]:
                        monkey_hitbox.x = max(monkey_hitbox.x - monkey_release_move_speed, 0)
                        monkey_orient = 1

            target = float(monkey_orient)
            if flipping < target:
                flipping = min(target, flipping + flipping_speed)
            elif flipping > target:
                flipping = max(target, flipping - flipping_speed)

            monkey_animate()
            gravity()

        screen.blit(ground_sprite, (back_ground_x1, ground_y))
        screen.blit(ground_sprite, (back_ground_x2, ground_y))
        screen.blit(ground_sprite, (ground_x1, ground_y))
        screen.blit(ground_sprite, (ground_x2, ground_y))

        if not is_paused:
            update_indicators(dt_ms)
            update_falling_objects(dt_ms)

        if not is_paused and invincibility_timer > 0:
            invincibility_timer -= 1
            monkey_flashing += 1
            if monkey_flashing >= 6:
                player_visible = not player_visible
                monkey_flashing = 0
        elif not is_paused:
            player_visible = True

        if player_visible:
            flipped_surf, flipped_w = flip(monkey_image)
            draw_x = monkey_hitbox.centerx - flipped_w // 2
            screen.blit(flipped_surf, (draw_x, monkey_hitbox.y))

        # Draw life received popup above monkey
        if life_received_timer > 0 and not is_paused:
            life_received_timer -= 1
            lr_w = life_received_image.get_width()
            lr_h = life_received_image.get_height()
            lr_x = monkey_hitbox.centerx - lr_w // 2
            lr_y = monkey_hitbox.top - lr_h - 5
            screen.blit(life_received_image, (lr_x, lr_y))

        draw_lives()

        enemy_rects, enemy_surfs, enemy_xpos = move_enemies(enemy_rects, enemy_surfs, enemy_xpos, enemy_speed, not is_paused and not monkey_release)

        if not is_paused and not monkey_release:
            is_playing, enemy_rects, enemy_surfs, enemy_xpos = collisions(monkey_hitbox, enemy_rects, enemy_surfs, enemy_xpos)
            if score > high_score:
                high_score = score
        elif not is_paused and monkey_release:
            if score > high_score:
                high_score = score
        else:
            screen.blit(overlay_image, (0, 0))
            display_score()
            pause_text = game_font.render("GAME PAUSED", False, "#a6d8af")
            pause_position = pause_text.get_rect(center=(400, 160))
            resume_text = game_font.render("Press 'P' to Resume", False, "#a6d8af")
            resume_pos = resume_text.get_rect(center=(400, 220))
            screen.blit(pause_text, pause_position)
            screen.blit(resume_text, resume_pos)

    else:
        draw_menu()

    pygame.display.update()
    clock.tick(60)

with open("highscore.txt", "w") as file:
    file.write(str(high_score))

pygame.quit()

"""
Changes:
- Theme changed from jets dodging bullets ot monkey dodging rocks
- textures changed
- parallaxing of ground (two ground sprites layered for 3d effect)
- background infinite scrolling
- foreground folliage parallaxing
- background extended for full frame
- hit box changing by changing the x and y ccalues of the hit box for rock
- linked rock height to monkey height
- googled gif support for pygame, using gif-pygame for monkey animation
- added darkening overlay in pause menu for readability
- fixed ground, foreground, background scrolling gaps: scroll_pair() funcition remembers the previous position
- rocks were out of sync from ground so linked them to the ground speed directly
- fixed music, added music switcher (keys 1, 2, 3)
- after 1000 score, monkey moved to center and is released so player can control with WASD controls
- jump key moved from space bar to w for future additions 
- monkey flips when moving left an right for better looking game (done by squishing until the image inverts)
- added monkey still animation for when the player doesnt move (only triggers after 1000 points for free roam)
- changed monkey sprite image sizes so theyre more consistent
- added falling coconuts and extra lives, stops after 2000 score for future additions
- extra life has a spawn rate (made it rarer)
- objects bounce off the ground giving player another chance to hit them then fall away and disappear
- extra life revcieved indicator above monkey
- 
********set core variable to 1000 to test free roam******

"""
"""
future additions:
- add a jump cancel where if the monkey presses a button, the monkey accelerates to the ground and immediately jumps back up (double jump should not work after jump cancel. double jump should only work if monkey presses space bar.)
- add power up (add vine that drops from the sky for the monkey to hold onto, granting invincibility)
- add cllectibles (banana) for monkey to collect
- add local high schore leaderboard with the text file
- make a banana counter on bottom to count bananas collected
"""


""" notes of the extra added stuff:
gif_pygame : xternal library
pygame.mixer: sound
pygame.USEREVENT: custom events
"""


'''observations/bugs
- rock disappears after monkey hits it (keep this usefuk)
- monkey coukd jump forever flying away (fixed by adding tiny cooldown)
- rocks keep drifting away from the ground after a hit, or reaching the left wall (fixed by linking rocks to the ground speed)
- menus were hard to see (fixed by adding a semi transparent black image overlay between the texts and everything else)
- scire is hard to read sometimes (too annoying to fix, good enough)
- music fixed, during testing wanted to try different musics but they switcher worked well (new feature keep music swithcer, keys 1, 2, 3)
'''