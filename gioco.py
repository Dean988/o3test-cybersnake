#!/usr/bin/env python3
'''
CyberSnake - Advanced Snake game with cybernetic neon graphics.
Autore: ChatGPT
Dipendenze: pygame (pip install pygame)
Esegui: python gioco.py
'''
import pygame
import random
import os
import math
from collections import deque


class Settings:
    GRID_SIZE = 20
    GRID_W = 30
    GRID_H = 30
    WIDTH = GRID_SIZE * GRID_W
    HEIGHT = GRID_SIZE * GRID_H + 60  # Space for HUD
    FPS_EASY = 6
    FPS_MEDIUM = 8
    FPS_HARD = 12
    MAX_FPS = 25
    COLORS = {
        'bg': (10, 10, 10),
        'grid': (30, 30, 30),
        'snake_head': (0, 255, 255),
        'snake_body': (0, 200, 200),
        'food': (0, 255, 128),
        'power': (255, 0, 255),
        'obst': (255, 64, 64),
        'portal': (128, 0, 255),
        'mine': (255, 215, 0),
        'shield': (64, 224, 208),
        'hud': (200, 200, 200),
        'menu_bg': (20, 20, 40),
        'menu_select': (0, 255, 255),
        'menu_text': (220, 220, 220),
    }
    FONT_NAME = 'freesansbold.ttf'
    HIGHSCORE_FILE = 'highscore.txt'
    DIFFICULTY_OBSTACLES = {
        'easy': 3,
        'medium': 8,
        'hard': 15
    }
    DIFFICULTY_MINE_CHANCE = {
        'easy': 0.0,
        'medium': 0.1,
        'hard': 0.2
    }
    DIFFICULTY_PORTAL_COUNT = {
        'easy': 0,
        'medium': 1,
        'hard': 2
    }


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.positions = deque([(Settings.GRID_W // 2, Settings.GRID_H // 2)])
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.grow_pending = 2
        self.shield_active = False
        self.shield_timer = 0

    def head(self):
        return self.positions[0]

    def turn(self, dir):
        # Prevent reverse movement
        if (dir[0] * -1, dir[1] * -1) == self.direction:
            return
        self.direction = dir

    def move(self):
        x, y = self.head()
        dx, dy = self.direction
        new_head = ((x + dx) % Settings.GRID_W, (y + dy) % Settings.GRID_H)
        if self.grow_pending:
            self.grow_pending -= 1
        else:
            self.positions.pop()
        self.positions.appendleft(new_head)

        # Update shield timer
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

    def grow(self, n=1):
        self.grow_pending += n

    def activate_shield(self, duration=150):
        self.shield_active = True
        self.shield_timer = duration

    def collides_self(self):
        return self.head() in list(self.positions)[1:]

    def draw(self, surf, glow_layer):
        for i, pos in enumerate(self.positions):
            px, py = pos
            rect = pygame.Rect(px * Settings.GRID_SIZE, py * Settings.GRID_SIZE,
                               Settings.GRID_SIZE, Settings.GRID_SIZE)
            color = Settings.COLORS['snake_head'] if i == 0 else Settings.COLORS['snake_body']
            pygame.draw.rect(surf, color, rect)
            
            # Add shield effect if active
            if i == 0 and self.shield_active:
                shield_rect = rect.inflate(8, 8)
                pygame.draw.rect(surf, Settings.COLORS['shield'], shield_rect, 2, border_radius=6)
                pygame.draw.rect(glow_layer, Settings.COLORS['shield'], shield_rect.inflate(4, 4), 3, border_radius=8)
            
            pygame.draw.rect(glow_layer, color, rect.inflate(6, 6), border_radius=8)


class Food:
    def __init__(self, power=False, shield=False):
        self.power = power
        self.shield = shield
        
        if shield:
            self.color = Settings.COLORS['shield']
        elif power:
            self.color = Settings.COLORS['power']
        else:
            self.color = Settings.COLORS['food']
            
        self.position = (0, 0)
        self.pulse = 0
        self.pulse_dir = 1

    def randomize(self, occupied):
        while True:
            p = (random.randint(0, Settings.GRID_W - 1), random.randint(0, Settings.GRID_H - 1))
            if p not in occupied:
                self.position = p
                break

    def update(self):
        # Pulsating effect
        self.pulse += 0.1 * self.pulse_dir
        if self.pulse >= 1.0:
            self.pulse_dir = -1
        elif self.pulse <= 0.0:
            self.pulse_dir = 1

    def draw(self, surf, glow_layer):
        px, py = self.position
        rect = pygame.Rect(px * Settings.GRID_SIZE, py * Settings.GRID_SIZE,
                           Settings.GRID_SIZE, Settings.GRID_SIZE)
        pygame.draw.rect(surf, self.color, rect)
        
        # Add pulsating glow effect
        pulse_size = 6 + int(4 * self.pulse)
        pygame.draw.rect(glow_layer, self.color, rect.inflate(pulse_size, pulse_size), border_radius=8)


class Mine:
    def __init__(self):
        self.position = (0, 0)
        self.timer = 0
        self.active = False
        self.explosion_radius = 1
        self.explosion_timer = 0

    def randomize(self, occupied):
        while True:
            p = (random.randint(0, Settings.GRID_W - 1), random.randint(0, Settings.GRID_H - 1))
            if p not in occupied:
                self.position = p
                self.timer = random.randint(100, 200)  # Random timer before activation
                self.active = False
                self.explosion_timer = 0
                break

    def update(self):
        if not self.active and self.timer > 0:
            self.timer -= 1
            if self.timer <= 0:
                self.active = True
        
        if self.explosion_timer > 0:
            self.explosion_timer -= 1

    def explode(self):
        self.explosion_timer = 20  # Duration of explosion animation
        return self.get_explosion_cells()
    
    def get_explosion_cells(self):
        cells = []
        x, y = self.position
        radius = self.explosion_radius
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius + radius:  # Circle-ish shape
                    nx, ny = (x + dx) % Settings.GRID_W, (y + dy) % Settings.GRID_H
                    cells.append((nx, ny))
        
        return cells

    def draw(self, surf, glow_layer):
        px, py = self.position
        rect = pygame.Rect(px * Settings.GRID_SIZE, py * Settings.GRID_SIZE,
                          Settings.GRID_SIZE, Settings.GRID_SIZE)
        
        if self.explosion_timer > 0:
            # Draw explosion
            explosion_cells = self.get_explosion_cells()
            for cell in explosion_cells:
                ex, ey = cell
                explosion_rect = pygame.Rect(ex * Settings.GRID_SIZE, ey * Settings.GRID_SIZE,
                                           Settings.GRID_SIZE, Settings.GRID_SIZE)
                intensity = min(255, 100 + 155 * (self.explosion_timer / 20))
                color = (intensity, intensity * 0.6, 0)
                pygame.draw.rect(surf, color, explosion_rect)
                pygame.draw.rect(glow_layer, (255, 200, 0), explosion_rect.inflate(10, 10), border_radius=8)
        else:
            # Draw mine
            color = Settings.COLORS['mine']
            if self.active:
                # Blinking effect when active
                if pygame.time.get_ticks() % 1000 < 500:
                    color = (255, 0, 0)
            
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(glow_layer, color, rect.inflate(6, 6), border_radius=8)
            
            # Draw X shape inside mine
            pygame.draw.line(surf, (20, 20, 20), 
                           (px * Settings.GRID_SIZE + 5, py * Settings.GRID_SIZE + 5),
                           (px * Settings.GRID_SIZE + Settings.GRID_SIZE - 5, 
                            py * Settings.GRID_SIZE + Settings.GRID_SIZE - 5), 2)
            pygame.draw.line(surf, (20, 20, 20), 
                           (px * Settings.GRID_SIZE + Settings.GRID_SIZE - 5, py * Settings.GRID_SIZE + 5),
                           (px * Settings.GRID_SIZE + 5, 
                            py * Settings.GRID_SIZE + Settings.GRID_SIZE - 5), 2)


class Portal:
    def __init__(self, id=0):
        self.id = id
        self.position = (0, 0)
        self.pair_position = (0, 0)
        self.color = Settings.COLORS['portal']
        self.angle = 0

    def randomize(self, occupied):
        while True:
            p1 = (random.randint(0, Settings.GRID_W - 1), random.randint(0, Settings.GRID_H - 1))
            if p1 not in occupied:
                self.position = p1
                occupied.add(p1)
                break
                
        while True:
            p2 = (random.randint(0, Settings.GRID_W - 1), random.randint(0, Settings.GRID_H - 1))
            if p2 not in occupied and p2 != self.position:
                self.pair_position = p2
                break

    def update(self):
        self.angle = (self.angle + 3) % 360

    def draw(self, surf, glow_layer):
        for pos in [self.position, self.pair_position]:
            px, py = pos
            rect = pygame.Rect(px * Settings.GRID_SIZE, py * Settings.GRID_SIZE,
                              Settings.GRID_SIZE, Settings.GRID_SIZE)
            
            # Draw portal
            center = rect.center
            radius = Settings.GRID_SIZE // 2
            pygame.draw.circle(surf, self.color, center, radius)
            
            # Draw rotating dots inside portal
            dot_count = 4
            for i in range(dot_count):
                angle = math.radians(self.angle + (360 / dot_count) * i)
                dot_x = center[0] + int(radius * 0.6 * math.cos(angle))
                dot_y = center[1] + int(radius * 0.6 * math.sin(angle))
                pygame.draw.circle(surf, (255, 255, 255), (dot_x, dot_y), 2)
            
            # Add glow effect
            pygame.draw.circle(glow_layer, self.color, center, radius + 4)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Settings.WIDTH, Settings.HEIGHT))
        pygame.display.set_caption('CyberSnake')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(Settings.FONT_NAME, 24)
        self.medium_font = pygame.font.Font(Settings.FONT_NAME, 32)
        self.big_font = pygame.font.Font(Settings.FONT_NAME, 48)

        self.grid_surface = pygame.Surface((Settings.WIDTH, Settings.HEIGHT - 60))
        self.grid_surface.set_alpha(80)
        self.create_grid()

        self.glow_layer = pygame.Surface((Settings.WIDTH, Settings.HEIGHT - 60), pygame.SRCALPHA)

        self.load_highscore()
        self.difficulty = 'medium'
        self.state = 'menu'
        self.menu_option = 0
        self.reset()

    def load_highscore(self):
        try:
            with open(Settings.HIGHSCORE_FILE, 'r') as f:
                self.highscore = int(f.read())
        except Exception:
            self.highscore = 0

    def save_highscore(self):
        with open(Settings.HIGHSCORE_FILE, 'w') as f:
            f.write(str(self.highscore))

    def create_grid(self):
        self.grid_surface.fill((0, 0, 0))
        for x in range(0, Settings.WIDTH, Settings.GRID_SIZE):
            pygame.draw.line(self.grid_surface, Settings.COLORS['grid'],
                             (x, 0), (x, Settings.HEIGHT - 60))
        for y in range(0, Settings.HEIGHT - 60, Settings.GRID_SIZE):
            pygame.draw.line(self.grid_surface, Settings.COLORS['grid'],
                             (0, y), (Settings.WIDTH, y))

    def reset(self):
        self.snake = Snake()
        self.obstacles = []
        self.mines = []
        self.portals = []
        self.explosion_cells = []
        self.score = 0
        
        # Set initial speed based on difficulty
        if self.difficulty == 'easy':
            self.speed = Settings.FPS_EASY
        elif self.difficulty == 'medium':
            self.speed = Settings.FPS_MEDIUM
        else:
            self.speed = Settings.FPS_HARD
            
        # Generate initial obstacles based on difficulty
        for _ in range(Settings.DIFFICULTY_OBSTACLES[self.difficulty]):
            self.spawn_obstacle()
            
        # Generate portals based on difficulty
        for i in range(Settings.DIFFICULTY_PORTAL_COUNT[self.difficulty]):
            self.spawn_portal(i)
            
        self.food = Food()
        self.food.randomize(self.get_occupied_positions())
        self.power_timer = 0
        self.shield_food_active = False
        self.state = 'running'
        self.combo_counter = 0
        self.combo_timer = 0
        self.last_direction_change = pygame.time.get_ticks()
        self.effects = []  # For visual effects

    def get_occupied_positions(self):
        occupied = set(self.snake.positions) | set(self.obstacles)
        for mine in self.mines:
            occupied.add(mine.position)
        for portal in self.portals:
            occupied.add(portal.position)
            occupied.add(portal.pair_position)
        if hasattr(self, 'food'):
            occupied.add(self.food.position)
        return occupied

    def spawn_obstacle(self):
        occupied = self.get_occupied_positions()
        while True:
            p = (random.randint(0, Settings.GRID_W - 1), random.randint(0, Settings.GRID_H - 1))
            if p not in occupied:
                self.obstacles.append(p)
                break

    def spawn_mine(self):
        mine = Mine()
        mine.randomize(self.get_occupied_positions())
        self.mines.append(mine)

    def spawn_portal(self, id=0):
        portal = Portal(id)
        portal.randomize(self.get_occupied_positions())
        self.portals.append(portal)

    def handle_menu(self):
        options = ['Easy', 'Medium', 'Hard', 'Start Game']
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.menu_option = (self.menu_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    self.menu_option = (self.menu_option + 1) % len(options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.menu_option < 3:  # Difficulty options
                        self.difficulty = options[self.menu_option].lower()
                    else:  # Start game
                        self.reset()
                        self.state = 'running'

    def draw_menu(self):
        options = ['Easy', 'Medium', 'Hard', 'Start Game']
        
        # Draw semi-transparent background
        menu_bg = pygame.Surface((Settings.WIDTH, Settings.HEIGHT))
        menu_bg.fill(Settings.COLORS['menu_bg'])
        menu_bg.set_alpha(220)
        self.screen.blit(menu_bg, (0, 0))
        
        # Draw title
        title = self.big_font.render('CYBERSNAKE', True, Settings.COLORS['menu_select'])
        title_rect = title.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 4))
        self.screen.blit(title, title_rect)
        
        # Draw subtitle
        subtitle = self.font.render('Select Difficulty', True, Settings.COLORS['menu_text'])
        subtitle_rect = subtitle.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 4 + 60))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Draw options
        for i, option in enumerate(options):
            color = Settings.COLORS['menu_select'] if i == self.menu_option else Settings.COLORS['menu_text']
            y_pos = Settings.HEIGHT // 2 + i * 50
            
            # Add indicator for selected option
            prefix = '> ' if i == self.menu_option else '  '
            
            text = self.medium_font.render(prefix + option, True, color)
            text_rect = text.get_rect(center=(Settings.WIDTH // 2, y_pos))
            self.screen.blit(text, text_rect)
            
            # Highlight current difficulty
            if i < 3 and option.lower() == self.difficulty:
                pygame.draw.rect(self.screen, color, text_rect.inflate(20, 10), 2, border_radius=5)

    def handle_events(self):
        if self.state == 'menu':
            self.handle_menu()
            return
            
        dir_map = {
            pygame.K_UP: (0, -1),
            pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_d: (1, 0),
        }
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.state = 'pause' if self.state == 'running' else 'running'
                elif event.key == pygame.K_ESCAPE:
                    self.state = 'menu' if self.state != 'menu' else 'running'
                if self.state != 'running':
                    continue
                if event.key in dir_map:
                    self.snake.turn(dir_map[event.key])
                    # Add combo system: fast direction changes score more
                    now = pygame.time.get_ticks()
                    if now - self.last_direction_change < 500:  # If changed direction within 0.5s
                        self.combo_counter += 1
                        self.combo_timer = 100  # Reset combo timer
                    else:
                        self.combo_counter = 1
                    self.last_direction_change = now
                elif event.key == pygame.K_r and self.state == 'gameover':
                    self.reset()

    def check_portal_collision(self):
        head = self.snake.head()
        for portal in self.portals:
            if head == portal.position:
                # Teleport to the paired portal
                exit_pos = portal.pair_position
                
                # Apply snake's direction to new position
                self.snake.positions[0] = exit_pos
                
                # Add teleport effect
                self.effects.append({
                    'type': 'teleport',
                    'pos': exit_pos,
                    'timer': 20
                })
                
                return True
            elif head == portal.pair_position:
                # Teleport to the entry portal
                exit_pos = portal.position
                
                # Apply snake's direction to new position
                self.snake.positions[0] = exit_pos
                
                # Add teleport effect
                self.effects.append({
                    'type': 'teleport',
                    'pos': exit_pos,
                    'timer': 20
                })
                
                return True
        return False

    def update(self):
        if self.state != 'running':
            return
            
        # Update effects
        self.effects = [effect for effect in self.effects if effect['timer'] > 0]
        for effect in self.effects:
            effect['timer'] -= 1
            
        # Update food animation
        self.food.update()
        
        # Update portals
        for portal in self.portals:
            portal.update()
            
        # Update mines
        for mine in self.mines:
            mine.update()
            
        # Update combo timer
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_counter = 0
            
        # Move snake
        self.snake.move()
        
        # Check portal teleportation
        teleported = self.check_portal_collision()
        
        # Check collisions
        if not teleported:
            # Check for collisions with mines
            for mine in self.mines:
                if self.snake.head() == mine.position and mine.explosion_timer == 0:
                    if self.snake.shield_active:
                        # Shield protects from mines
                        self.snake.shield_active = False
                        self.effects.append({
                            'type': 'shield_break',
                            'pos': self.snake.head(),
                            'timer': 20
                        })
                    else:
                        # Mine explosion
                        self.explosion_cells = mine.explode()
                        # Check if snake is in explosion radius
                        if self.snake.head() in self.explosion_cells:
                            self.state = 'gameover'
                            if self.score > self.highscore:
                                self.highscore = self.score
                                self.save_highscore()
                            return
            
            # Check for collision with explosion cells
            for cell in self.explosion_cells:
                if self.snake.head() == cell and not self.snake.shield_active:
                    self.state = 'gameover'
                    if self.score > self.highscore:
                        self.highscore = self.score
                        self.save_highscore()
                    return
            
            # Check for self collision or obstacle collision
            if (self.snake.collides_self() or 
                self.snake.head() in self.obstacles) and not self.snake.shield_active:
                self.state = 'gameover'
                if self.score > self.highscore:
                    self.highscore = self.score
                    self.save_highscore()
                return

        # Food collision
        if self.snake.head() == self.food.position:
            self.snake.grow()
            
            # Calculate score with combo multiplier
            combo_multiplier = min(5, max(1, self.combo_counter))
            base_points = 2 if self.food.power else 1
            if self.food.shield:
                base_points = 3
                self.snake.activate_shield()
                
            gained = base_points * combo_multiplier
            self.score += gained
            
            # Show score effect
            self.effects.append({
                'type': 'score',
                'pos': self.snake.head(),
                'value': gained,
                'timer': 40
            })
            
            # Spawn obstacles based on score
            if self.score % 5 == 0 and len(self.obstacles) < 30:
                self.spawn_obstacle()
                
            # Maybe spawn a mine based on difficulty
            if random.random() < Settings.DIFFICULTY_MINE_CHANCE[self.difficulty]:
                self.spawn_mine()
                
            # Adjust speed based on score and difficulty
            if self.difficulty == 'easy':
                self.speed = min(Settings.FPS_EASY + self.score // 8, Settings.MAX_FPS)
            elif self.difficulty == 'medium':
                self.speed = min(Settings.FPS_MEDIUM + self.score // 6, Settings.MAX_FPS)
            else:
                self.speed = min(Settings.FPS_HARD + self.score // 4, Settings.MAX_FPS)
                
            # Decide what kind of food to spawn next
            power = random.random() < 0.15
            shield = random.random() < 0.1
            
            if shield:
                self.food = Food(power=False, shield=True)
            else:
                self.food = Food(power=power, shield=False)
                
            self.food.randomize(self.get_occupied_positions())
            
            if power:
                self.power_timer = 120  # ~3-4 seconds
                self.speed = max(self.speed - 5, 5)

        # Power timer
        if self.power_timer:
            self.power_timer -= 1
            if self.power_timer == 0:
                if self.difficulty == 'easy':
                    self.speed = min(Settings.FPS_EASY + self.score // 8, Settings.MAX_FPS)
                elif self.difficulty == 'medium':
                    self.speed = min(Settings.FPS_MEDIUM + self.score // 6, Settings.MAX_FPS)
                else:
                    self.speed = min(Settings.FPS_HARD + self.score // 4, Settings.MAX_FPS)

    def draw_hud(self):
        hud_rect = pygame.Rect(0, Settings.HEIGHT - 60, Settings.WIDTH, 60)
        pygame.draw.rect(self.screen, Settings.COLORS['bg'], hud_rect)
        
        # Draw difficulty 
        diff_text = f'Difficulty: {self.difficulty.capitalize()}'
        diff_surf = self.font.render(diff_text, True, Settings.COLORS['hud'])
        diff_rect = diff_surf.get_rect(topleft=(20, Settings.HEIGHT - 55))
        self.screen.blit(diff_surf, diff_rect)
        
        # Draw score, highscore and speed
        text = f'Score: {self.score}   High Score: {self.highscore}   Speed: {self.speed}'
        surf = self.font.render(text, True, Settings.COLORS['hud'])
        self.screen.blit(surf, (20, Settings.HEIGHT - 30))
        
        # Draw combo counter if active
        if self.combo_counter > 1:
            combo_text = f'Combo: x{min(5, self.combo_counter)}'
            combo_color = (255, 255, 0)  # Yellow for combo
            combo_surf = self.font.render(combo_text, True, combo_color)
            self.screen.blit(combo_surf, (Settings.WIDTH - 150, Settings.HEIGHT - 30))
            
        # Draw shield indicator if active
        if self.snake.shield_active:
            shield_text = "SHIELD ACTIVE"
            shield_surf = self.font.render(shield_text, True, Settings.COLORS['shield'])
            self.screen.blit(shield_surf, (Settings.WIDTH - 200, Settings.HEIGHT - 55))

    def draw_obstacles(self):
        for p in self.obstacles:
            rect = pygame.Rect(p[0] * Settings.GRID_SIZE, p[1] * Settings.GRID_SIZE,
                               Settings.GRID_SIZE, Settings.GRID_SIZE)
            pygame.draw.rect(self.screen, Settings.COLORS['obst'], rect)
            pygame.draw.rect(self.glow_layer, Settings.COLORS['obst'], rect.inflate(6, 6), border_radius=8)

    def draw_effects(self):
        for effect in self.effects:
            if effect['type'] == 'teleport':
                x, y = effect['pos']
                rect = pygame.Rect(x * Settings.GRID_SIZE, y * Settings.GRID_SIZE,
                                 Settings.GRID_SIZE, Settings.GRID_SIZE)
                
                # Draw expanding circles
                max_radius = 30
                progress = 1 - (effect['timer'] / 20)
                radius = int(max_radius * progress)
                
                pygame.draw.circle(self.glow_layer, Settings.COLORS['portal'], 
                                  rect.center, radius, 2)
                pygame.draw.circle(self.glow_layer, Settings.COLORS['portal'], 
                                  rect.center, radius // 2, 2)
                                  
            elif effect['type'] == 'score':
                x, y = effect['pos']
                # Move effect upward as timer decreases
                y_offset = 20 * (1 - effect['timer'] / 40)
                pos = (x * Settings.GRID_SIZE + Settings.GRID_SIZE // 2, 
                     y * Settings.GRID_SIZE - y_offset)
                
                # Fade out text as timer decreases
                alpha = min(255, 255 * (effect['timer'] / 40))
                
                # Different colors based on score value
                if effect['value'] >= 10:
                    color = (255, 215, 0)  # Gold
                elif effect['value'] >= 5:
                    color = (255, 140, 0)  # Orange
                else:
                    color = (255, 255, 255)  # White
                
                # Draw score text with outline
                score_text = f"+{effect['value']}"
                score_surf = self.font.render(score_text, True, color)
                score_surf.set_alpha(alpha)
                
                # Position text centered at effect position
                score_rect = score_surf.get_rect(center=pos)
                self.screen.blit(score_surf, score_rect)
                
            elif effect['type'] == 'shield_break':
                x, y = effect['pos']
                rect = pygame.Rect(x * Settings.GRID_SIZE, y * Settings.GRID_SIZE,
                                 Settings.GRID_SIZE, Settings.GRID_SIZE)
                
                # Draw breaking shield effect
                max_radius = 25
                progress = 1 - (effect['timer'] / 20)
                radius = int(max_radius * progress)
                
                for i in range(8):
                    angle = math.radians(i * 45 + progress * 90)
                    end_x = rect.centerx + int(radius * math.cos(angle))
                    end_y = rect.centery + int(radius * math.sin(angle))
                    pygame.draw.line(self.glow_layer, Settings.COLORS['shield'],
                                   rect.center, (end_x, end_y), 2)

    def render(self):
        if self.state == 'menu':
            self.draw_menu()
            pygame.display.flip()
            return
            
        self.screen.fill(Settings.COLORS['bg'])
        self.screen.blit(self.grid_surface, (0, 0))
        self.glow_layer.fill((0, 0, 0, 0))

        self.draw_obstacles()
        
        # Draw mines
        for mine in self.mines:
            mine.draw(self.screen, self.glow_layer)
            
        # Draw portals
        for portal in self.portals:
            portal.draw(self.screen, self.glow_layer)
            
        self.food.draw(self.screen, self.glow_layer)
        self.snake.draw(self.screen, self.glow_layer)
        
        # Draw effects
        self.draw_effects()

        self.screen.blit(self.glow_layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.draw_hud()

        if self.state == 'pause':
            self.draw_center_text('PAUSA', self.big_font)
        elif self.state == 'gameover':
            self.draw_center_text('GAME OVER - premi R per ripartire', self.font)

        pygame.display.flip()

    def draw_center_text(self, text, font):
        surf = font.render(text, True, Settings.COLORS['hud'])
        rect = surf.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 2))
        self.screen.blit(surf, rect)

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.speed if self.state == 'running' else 30)


if __name__ == '__main__':
    Game().run()