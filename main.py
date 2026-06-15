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

# Return to start state
monkey_returning = False

# Smooth acceleration variables
acceleration_timer = 0
target_speed = 5 + 999 // 50
current_scrolling_speed = 0

# level images
background_sprite = pygame.transform.scale(pygame.image.load("graphics/level/Background.png").convert(), (800, 400))
foreground_sprite = pygame.image.load("graphics/level/Foreground.png").convert_alpha()
foreground_y = 400 - foreground_sprite.get_height()
ground_sprite = pygame.image.load("graphics/level/ground.png").convert_alpha()
overlay_image = pygame.image.load("graphics/level/Overlay.png").convert_alpha()
game_font = pygame.font.SysFont("couriernew", 40, bold=True)

# monkey run frames
monkey_run_frames = [
    pygame.transform.scale(pygame.image.load(f"graphics/monkey/Monkey_Run/frame_{i}_delay-0.1s (1).gif").convert_alpha(), (100, 100))
    for i in range(7)
]

# monkey still frames
monkey_still_frames = [
    pygame.transform.scale(pygame.image.load(f"graphics/monkey/Monkey_Still/frame_{i}_delay-0.1s.gif").convert_alpha(), (90, 90))
    for i in range(7)
]

monkey_jump_image = pygame.image.load("graphics/monkey/Monkey_jump.png").convert_alpha()
monkey_jump_image = pygame.transform.scale(monkey_jump_image, (130, 130))
monkey_image = monkey_run_frames[0]
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
life_received_image = pygame.image.load("graphics/lives/life_recieved.png").convert_alpha()
life_received_image = pygame.transform.scale(life_received_image, (50, 50))
life_received_length = 60
life_received_timer = 0

indicator_height = 40
coconut_indicator_image = pygame.image.load("graphics/indicators/coconut_indicator.png").convert_alpha()
life_indicator_image = pygame.image.load("graphics/indicators/life_indicator.png").convert_alpha()

# Variables
jump_count = 0
jump_cancel = False
jump_cancel_speed = 25
bounce_speed = -20
player_lives = 3
immortality_length = 90
invincibility_timer = 0
player_visible = True
monkey_flashing = 0
player_gravspeed = 0

# Monkey flip
flipping_speed = 0.1
monkey_orient = 0
flipping = 0

# Ground scrolling
ground_w = ground_sprite.get_width()
ground_x1 = 0
ground_x2 = ground_w
ground_speed = 0.6

# Back ground layer parallaxing
back_ground_x1 = 0
back_ground_x2 = ground_w
back_ground_speed = 0.4

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

# score
score_offset = 0
score = 0
last_life_refill_score = 0

high_score = 0
start_time = 0
pause_time = 0
pause_start_time = 0

# timer related functions
enemy_timer = pygame.USEREVENT + 1
pygame.time.set_timer(enemy_timer, 1200)

# falling things
base_spawn_delay = 1200
indicator_timer = 800
falling_things_gravity = 1.5
coconut_bouncing = -25
life_spawn_rate = 0.05

# spawning difficulty increaser
spawn_wave = 0
spawn_delay_decreaser = 25
lowest_spawn_delay = 500

falling_objects = []
indicators = []
falling_stuff_time = pygame.USEREVENT + 2
pygame.time.set_timer(falling_stuff_time, base_spawn_delay)

try:
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())
except FileNotFoundError:
    high_score = 0


def scroll_pair(x1, x2, speed, sprite_w):
    x1 = (x1 - speed) % sprite_w
    return x1 - sprite_w, x1


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


def reset_game():
    global is_playing, is_paused, monkey_returning, acceleration_timer, spawn_wave
    global life_received_timer, pause_time, score, start_time, monkey_release, monkey_release_centered
    global last_life_refill_score, player_lives, invincibility_timer, player_visible, monkey_flashing
    global player_gravspeed, jump_count, jump_cancel, monkey_orient, flipping
    global ground_x1, ground_x2, back_ground_x1, back_ground_x2, background_x1, background_x2, foreground_x1, foreground_x2

    is_playing = True
    is_paused = False
    monkey_returning = False
    acceleration_timer = 0
    spawn_wave = 0
    life_received_timer = 0
    pause_time = 0
    score = score_offset
    last_life_refill_score = (score_offset // 1000) * 1000
    start_time = pygame.time.get_ticks() // 100

    if ((score_offset // 500) % 2) == 1:
        monkey_release = True
        monkey_release_centered = True
        monkey_hitbox.centerx = 400
    else:
        monkey_release = False
        monkey_release_centered = False
        monkey_hitbox.bottomleft = (80, player_ground)

    # Clear game lists
    enemy_rects.clear()
    enemy_surfs.clear()
    enemy_xpos.clear()
    falling_objects.clear()
    indicators.clear()

    # Reset player variables
    player_lives = 3
    invincibility_timer = 0
    player_visible = True
    monkey_flashing = 0
    player_gravspeed = 0
    jump_count = 0
    jump_cancel = False
    monkey_orient = 0
    flipping = 0

    # Reset scroll positions
    ground_x1, ground_x2 = 0, ground_w
    back_ground_x1, back_ground_x2 = 0, ground_w
    background_x1, background_x2 = 0, background_w
    foreground_x1, foreground_x2 = 0, foreground_w

    pygame.time.set_timer(falling_stuff_time, base_spawn_delay)


def monkey_animate():
    global monkey_image
    keys = pygame.key.get_pressed()
    if monkey_hitbox.bottom < player_ground:
        monkey_image = monkey_jump_image
    elif monkey_returning:
        frame_index = (pygame.time.get_ticks() // 150) % len(monkey_run_frames)
        monkey_image = monkey_run_frames[frame_index]
    elif monkey_release and monkey_release_centered and (keys[pygame.K_a] or keys[pygame.K_d]):
        frame_index = (pygame.time.get_ticks() // 150) % len(monkey_run_frames)
        monkey_image = monkey_run_frames[frame_index]
    elif monkey_release and monkey_release_centered:
        frame_index = (pygame.time.get_ticks() // 150) % len(monkey_still_frames)
        monkey_image = monkey_still_frames[frame_index]
    else:
        frame_index = (pygame.time.get_ticks() // 150) % len(monkey_run_frames)
        monkey_image = monkey_run_frames[frame_index]


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
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_1:
            track = "sfx/Music_1.mp3"
        elif event.key == pygame.K_2:
            track = "sfx/Music_2.mp3"
        elif event.key == pygame.K_3:
            track = "sfx/Music.mp3"
        else:
            return
        music.stop()
        music = pygame.mixer.Sound(track)
        music.set_volume(1.2)
        music.play(loops=-1)


def player_input(event):
    global player_gravspeed, jump_count, monkey_orient, jump_cancel
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_d and monkey_release and not monkey_returning:
            monkey_orient = 0
        if event.key == pygame.K_a and monkey_release and not monkey_returning:
            monkey_orient = 1
        if event.key == pygame.K_w and jump_count < 2:
            player_gravspeed = jump_speed
            jump_count += 1
            jump.play()
        if event.key == pygame.K_s and monkey_hitbox.bottom < player_ground:
            player_gravspeed = jump_cancel_speed
            jump_cancel = True


def gravity():
    global player_gravspeed, jump_count, jump_cancel
    player_gravspeed += 1
    monkey_hitbox.y += player_gravspeed
    if monkey_hitbox.bottom >= player_ground:
        monkey_hitbox.bottom = player_ground
        if jump_cancel:
            player_gravspeed = bounce_speed
            jump_count = 1  
            jump_cancel = False
        else:
            player_gravspeed = 0
            jump_count = 0


def move_enemies(rects, surfs, xpos, speed_modifier, should_move):
    updated_rects = []
    updated_surfs = []
    updated_xpos = []

    for i in range(len(rects)):
        if should_move:
            xpos[i] -= speed_modifier * ground_speed
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


def falling_object_collisions():
    global falling_objects, is_playing, player_lives, invincibility_timer, player_visible, monkey_flashing, life_received_timer

    surviving_objects = []
    player_left, player_top = monkey_hitbox.x + 40, monkey_hitbox.y + 35
    player_width, player_height = monkey_hitbox.width - 80, monkey_hitbox.height - 70

    for obj in falling_objects:
        img = coconut_image if obj[3] == "coconut" else extra_life_image
        img_height = img.get_height()

        obj[2] += falling_things_gravity
        obj[1] += obj[2]

        if not obj[4] and obj[1] + img_height >= player_ground:
            obj[1] = player_ground - img_height
            obj[2] = coconut_bouncing
            obj[4] = True

        if obj[4] and obj[1] > 420:
            continue

        screen.blit(img, (int(obj[0]), int(obj[1])))
        
        obj_left, obj_top = int(obj[0]) + 10, int(obj[1]) + 10
        obj_w, obj_h = img.get_width() - 20, img.get_height() - 20

        if (player_left < obj_left + obj_w and player_left + player_width > obj_left 
                and player_top < obj_top + obj_h and player_top + player_height > obj_top):
            
            if obj[3] == "coconut":
                if invincibility_timer <= 0:
                    player_lives -= 1
                    hit.play()
                    if player_lives <= 0:
                        game_over.play()
                        is_playing = False
                        break
                    else:
                        invincibility_timer = immortality_length
                        player_visible = True
                        monkey_flashing = 0
            else:
                if player_lives < 3:
                    player_lives += 1
                life_received_timer = life_received_length
            continue
            
        surviving_objects.append(obj)

    if is_playing:
        falling_objects = surviving_objects


def update_indicators(dt_ms):
    surviving = []
    for ind in indicators:
        ind[2] -= dt_ms
        img = coconut_indicator_image if ind[1] == "coconut" else life_indicator_image
        img_width, img_height = img.get_size()
        draw_y = ground_y - indicator_height - img_height
        screen.blit(img, (ind[0] - img_width // 2, draw_y))

        if ind[2] <= 0:
            falling_objects.append([float(ind[0] - img_width // 2), -img_height, 0, ind[1], False])
        else:
            surviving.append(ind)
            
    indicators.clear()
    indicators.extend(surviving)


def spawn_falling_group(current_score):
    global spawn_wave
    if not monkey_release_centered:
        return
        
    score_earned_in_phase = current_score % 500
    dynamic_max_objects = min(4, 2 + (score_earned_in_phase // 100))
    player_center_x = monkey_hitbox.centerx
    
    indicators.append([player_center_x, "coconut", indicator_timer])
    
    active_count = len(falling_objects) + len(indicators)
    if active_count >= dynamic_max_objects:
        spawn_wave += 1 
        return

    slots = dynamic_max_objects - active_count
    count = random.randint(1, min(2, slots))

    for n in range(count):
        x = random.randint(60, 740)
        kind = "life" if random.random() < life_spawn_rate else "coconut"
        indicators.append([x, kind, indicator_timer])
        
    spawn_wave += 1


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


def draw_pause_screen():
    screen.blit(overlay_image, (0, 0))
    display_score()
    pause_text = game_font.render("GAME PAUSED", False, "#a6d8af")
    pause_position = pause_text.get_rect(center=(400, 160))
    resume_text = game_font.render("Press 'P' to Resume", False, "#a6d8af")
    resume_pos = resume_text.get_rect(center=(400, 220))
    screen.blit(pause_text, pause_position)
    screen.blit(resume_text, resume_pos)


# main game loop

while running:
    dt_ms = clock.get_time()

    for event in pygame.event.get():
        music_switch()
        if event.type == pygame.QUIT:
            running = False

        if is_playing:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                is_paused = not is_paused
                if is_paused:
                    pause_start_time = pygame.time.get_ticks() // 100
                else:
                    pause_time += (pygame.time.get_ticks() // 100) - pause_start_time

            if not is_paused:
                current_loop_mode = (score // 500) % 2
                if monkey_release and not monkey_returning:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_w and jump_count < 2:
                        player_gravspeed = jump_speed
                        jump_count += 1
                        jump.play()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_s and monkey_hitbox.bottom < player_ground:
                        player_gravspeed = jump_cancel_speed
                        jump_cancel = True
                else:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_d, pygame.K_a) and current_loop_mode == 0:
                        pass
                    else:
                        player_input(event)

                if event.type == enemy_timer and not monkey_release and not monkey_returning and (score < 500 or acceleration_timer >= 120):
                    rock_image = random.choice(rock_images)
                    spawn_x = random.randint(850, 1100)
                    rock_hitbox = rock_image.get_rect(bottomleft=(spawn_x, player_ground))
                    enemy_rects.append(rock_hitbox)
                    enemy_surfs.append(rock_image)
                    enemy_xpos.append(float(spawn_x))

                if event.type == falling_stuff_time and monkey_release and monkey_release_centered:
                    if current_loop_mode == 1:
                        spawn_falling_group(score) 
                        current_delay = base_spawn_delay - (spawn_wave * spawn_delay_decreaser)
                        new_interval = max(lowest_spawn_delay, current_delay)
                        pygame.time.set_timer(falling_stuff_time, new_interval)

        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_w:
                reset_game()

    if is_playing:
        music_switch()
        
        current_loop_mode = (score // 500) % 2

        # Manage phase changes and speed values
        if score < 500:
            enemy_speed = 5 + score // 50
            current_scrolling_speed = enemy_speed
        else:
            if current_loop_mode == 0:
                if monkey_returning:
                    enemy_speed = 0
                    current_scrolling_speed = 0
                else:
                    if acceleration_timer < 120:
                        if not is_paused:
                            acceleration_timer += 1
                        current_scrolling_speed = (acceleration_timer / 120.0) * target_speed
                    else:
                        current_scrolling_speed = target_speed
                    enemy_speed = current_scrolling_speed
            else:
                enemy_speed = target_speed
                current_scrolling_speed = target_speed

        if current_loop_mode == 1 and not monkey_release:
            monkey_release = True
            monkey_release_centered = False
            monkey_returning = False
            enemy_rects.clear()
            enemy_surfs.clear()
            enemy_xpos.clear()

        elif current_loop_mode == 0 and monkey_release:
            monkey_returning = True
            monkey_release = False
            monkey_release_centered = False
            acceleration_timer = 0
            falling_objects.clear()
            indicators.clear()

        if not is_paused:
            if current_loop_mode == 0:
                background_x1, background_x2 = scroll_pair(background_x1, background_x2, current_scrolling_speed * background_scroll_speed, background_w)
                foreground_x1, foreground_x2 = scroll_pair(foreground_x1, foreground_x2, current_scrolling_speed * foreground_scroll_speed, foreground_w)

        screen.fill((0, 0, 0))
        screen.blit(background_sprite, (background_x1, 0))
        screen.blit(background_sprite, (background_x2, 0))
        if current_loop_mode == 0:
            screen.blit(foreground_sprite, (foreground_x1, foreground_y))
            screen.blit(foreground_sprite, (foreground_x2, foreground_y))

        display_score()

        if score >= last_life_refill_score + 1000:
            player_lives = 3
            life_received_timer = life_received_length
            last_life_refill_score += 1000

        if not is_paused:
            if monkey_returning:
                monkey_orient = 1
                if monkey_hitbox.x > 80:
                    monkey_hitbox.x = max(monkey_hitbox.x - monkey_release_move_speed, 80)
                else:
                    monkey_returning = False
                    monkey_orient = 0

            if not monkey_release and not monkey_returning:
                back_ground_x1, back_ground_x2 = scroll_pair(back_ground_x1, back_ground_x2, current_scrolling_speed * back_ground_speed, ground_w)
                ground_x1, ground_x2 = scroll_pair(ground_x1, ground_x2, current_scrolling_speed * ground_speed, ground_w)

            if monkey_release:
                center_x = 400 - monkey_hitbox.width // 2
                if not monkey_release_centered:
                    if monkey_hitbox.x < center_x:
                        monkey_hitbox.x = min(monkey_hitbox.x - monkey_release_move_speed, center_x)
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

            if not monkey_release and not monkey_returning:
                monkey_orient = 0

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
            falling_object_collisions()

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

        if life_received_timer > 0 and not is_paused:
            life_received_timer -= 1
            lr_w = life_received_image.get_width()
            lr_h = life_received_image.get_height()
            lr_x = monkey_hitbox.centerx - lr_w // 2
            lr_y = monkey_hitbox.top - lr_h - 5
            screen.blit(life_received_image, (lr_x, lr_y))

        draw_lives()

        enemy_rects, enemy_surfs, enemy_xpos = move_enemies(enemy_rects, enemy_surfs, enemy_xpos, enemy_speed, not is_paused and not monkey_release)

        if not is_paused and not monkey_release and not monkey_returning:
            is_playing, enemy_rects, enemy_surfs, enemy_xpos = collisions(monkey_hitbox, enemy_rects, enemy_surfs, enemy_xpos)
            if score > high_score:
                high_score = score
        elif not is_paused and (monkey_release or monkey_returning):
            if score > high_score:
                high_score = score
        else:
            if is_paused:
                draw_pause_screen()

    else:
        draw_menu()

    pygame.display.update()
    clock.tick(60)

with open("highscore.txt", "w") as file:
    file.write(str(high_score))

pygame.quit()





"""
Changes history:
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
- after 500 score, monkey moved to center and is released so player can control with WASD controls
- jump key moved from space bar to w for future additions 
- monkey flips when moving left an right for better looking game (done by squishing until the image inverts)
- added monkey still animation for when the player doesnt move (only triggers after 500 points for free roam)
- changed monkey sprite image sizes so theyre more consistent
- added falling coconuts and extra lives, stops after 500 score for future additions
- extra life has a spawn rate (made it rarer)
- objects bounce off the ground giving player another chance to hit them then fall away and disappear
- extra life revcieved indicator above monkey
- added jump cancel where it bounces again after cancelling (strategy is to chain cancels)
- pressing 'r' resets ganme back to start
- replaced gif_pygame with manual PNG frame loading from Monkey_Run/ and Monkey_Still/ subfolders
- removed boss fight visuals and transition logic (game ends at 500 points)
- removed gif_pygame dependency entirely (no longer needed)
- added coconut spaning variables to increase difficulty by changing the spawn rates and max coconuts
- split def functions so they are under 30 lines according to the rubrivc
- cleaned up code to adhere to the rubric
- Let player double jump after jump cancel
- every 1000 points heath bar gets reset to max so players can enjoy the game for longer
"""
"""
future additions:
- add power up (add vine that drops from the sky for the monkey to hold onto, granting invincibility)
- add collectibles (banana) for monkey to collect
- add local high score leaderboard with the text file
- make a banana counter on bottom to count bananas collected
"""


""" notes of the extra added stuff:
pygame.mixer: sound
pygame.USEREVENT: custom events
"""


'''observations/bugs
- rock disappears after monkey hits it (keep this useful)
- monkey could jump forever flying away (fixed by adding tiny cooldown)
- rocks keep drifting away from the ground after a hit, or reaching the left wall (fixed by linking rocks to the ground speed)
- menus were hard to see (fixed by adding a semi transparent black image overlay between the texts and everything else)
- score is hard to read sometimes (too annoying to fix, good enough)
- music fixed, during testing wanted to try different musics but they switcher worked well (new feature keep music switcher, keys 1, 2, 3)
- coconut level is very competetive with people, its possible but the rarity of extra lives and the gradual increase difficulty makes it more enjoyable, and the refill health makes it a challenge to last the longest
'''


'''fixes
deleted boss fight and all boss fight related stuff
checked rubric and tweaked code to fit it'''


