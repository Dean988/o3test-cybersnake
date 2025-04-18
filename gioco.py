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
import time
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
        'bg': (10, 10, 25),  # Darker blue background
        'grid': (20, 35, 45),  # More visible grid
        'snake_head': (0, 255, 255),
        'snake_body': (0, 200, 200),
        'food': (0, 255, 128),
        'power': (255, 0, 255),
        'obst': (255, 64, 64),
        'portal': (128, 0, 255),
        'mine': (255, 215, 0),
        'shield': (64, 224, 208),
        'hud': (200, 200, 200),
        'menu_bg': (15, 15, 35),
        'menu_select': (0, 255, 255),
        'menu_text': (220, 220, 220),
        'particle': (255, 255, 255, 150),  # Semi-transparent white for particles
        'bg_glow': (20, 40, 80, 50),  # Background glow effect
        'title_glow': (0, 180, 255),  # Glowing title effect
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
    
    # Sound settings
    SOUNDS = {
        'eat': 'eat.wav',
        'game_over': 'game_over.wav',
        'teleport': 'teleport.wav',
        'shield': 'shield.wav',
        'explosion': 'explosion.wav',
        'menu_select': 'menu_select.wav',
        'menu_confirm': 'menu_confirm.wav',
    }
    MUSIC = 'background_music.mp3'
    
    # Visual effects settings
    PARTICLE_COUNT = 50
    PARTICLE_SPEED = 1.5
    PARTICLE_LIFETIME = 200
    
    # Menu animations
    MENU_PULSE_SPEED = 0.02
    TITLE_GLOW_SPEED = 0.03
    
    # Background effects
    BG_STARS_COUNT = 100
    BG_NEBULA_COUNT = 3


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


class Particle:
    def __init__(self, x, y, color, size=2, lifetime=None, speed=None, direction=None):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime or random.randint(50, Settings.PARTICLE_LIFETIME)
        self.max_lifetime = self.lifetime
        self.speed = speed or random.uniform(0.5, Settings.PARTICLE_SPEED)
        
        # Random direction if none provided
        if direction is None:
            angle = random.uniform(0, math.pi * 2)
            self.dx = math.cos(angle) * self.speed
            self.dy = math.sin(angle) * self.speed
        else:
            self.dx = direction[0] * self.speed
            self.dy = direction[1] * self.speed
            
        # For some visual variations
        self.pulse_rate = random.uniform(0.03, 0.08)
        self.pulse = random.uniform(0, 1)
        self.pulse_dir = 1

    def update(self):
        self.lifetime -= 1
        self.x += self.dx
        self.y += self.dy
        
        # Slow down over time
        self.dx *= 0.98
        self.dy *= 0.98
        
        # Pulsate size
        self.pulse += self.pulse_rate * self.pulse_dir
        if self.pulse >= 1:
            self.pulse_dir = -1
        elif self.pulse <= 0:
            self.pulse_dir = 1
        
        return self.lifetime > 0

    def draw(self, surface):
        # Get alpha based on remaining lifetime
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        # Get size with pulse effect
        current_size = self.size * (0.8 + 0.4 * self.pulse) 
        
        # Create a surface for this particle with alpha
        if isinstance(self.color, tuple) and len(self.color) == 4:
            # If color already has alpha
            particle_color = (self.color[0], self.color[1], self.color[2], 
                             min(self.color[3], alpha))
        else:
            # Add alpha to the color
            particle_color = (*self.color[:3], alpha)
        
        # Draw on surface
        pygame.draw.circle(surface, particle_color, 
                         (int(self.x), int(self.y)), int(current_size))


class BackgroundStar:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.uniform(0.5, 2.5)
        self.brightness = random.uniform(0.3, 1.0)
        self.pulse_speed = random.uniform(0.01, 0.03)
        self.pulse = random.uniform(0, 1)
        self.direction = 1

    def update(self):
        # Pulsate brightness
        self.pulse += self.pulse_speed * self.direction
        if self.pulse > 1:
            self.direction = -1
        elif self.pulse < 0:
            self.direction = 1

    def draw(self, surface):
        # Calculate current brightness
        current_brightness = 0.3 + 0.7 * self.brightness * self.pulse
        color = (int(255 * current_brightness), 
                int(255 * current_brightness), 
                int(255 * current_brightness))
        
        # Draw star as a small circle
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))


class SoundManager:
    def __init__(self):
        # Initialize mixer
        pygame.mixer.init()
        self.sounds = {}
        self.music_playing = False
        self.sound_enabled = True
        self.music_enabled = True
        
        # Try to load sounds
        try:
            for name, file in Settings.SOUNDS.items():
                try:
                    sound_path = os.path.join('sounds', file)
                    if os.path.exists(sound_path):
                        self.sounds[name] = pygame.mixer.Sound(sound_path)
                except:
                    print(f"Could not load sound: {file}")
            
            # Try to load music
            music_path = os.path.join('sounds', Settings.MUSIC)
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
        except:
            print("Error initializing sound system")
    
    def play(self, sound_name, volume=1.0):
        if not self.sound_enabled or sound_name not in self.sounds:
            return
        
        self.sounds[sound_name].set_volume(volume)
        self.sounds[sound_name].play()
    
    def play_music(self, volume=0.5, loop=-1):
        if not self.music_enabled:
            return
            
        try:
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loop)
            self.music_playing = True
        except:
            print("Could not play music")
    
    def stop_music(self):
        pygame.mixer.music.stop()
        self.music_playing = False
    
    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled
    
    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if self.music_enabled and not self.music_playing:
            self.play_music()
        elif not self.music_enabled:
            self.stop_music()
        return self.music_enabled


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Settings.WIDTH, Settings.HEIGHT))
        pygame.display.set_caption('CyberSnake')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(Settings.FONT_NAME, 24)
        self.medium_font = pygame.font.Font(Settings.FONT_NAME, 32)
        self.big_font = pygame.font.Font(Settings.FONT_NAME, 48)

        # Create directory for sounds if it doesn't exist
        os.makedirs('sounds', exist_ok=True)

        # Initialize sound system
        self.sound_manager = SoundManager()
        
        # Create surfaces
        self.grid_surface = pygame.Surface((Settings.WIDTH, Settings.HEIGHT - 60))
        self.grid_surface.set_alpha(80)
        self.create_grid()

        self.glow_layer = pygame.Surface((Settings.WIDTH, Settings.HEIGHT - 60), pygame.SRCALPHA)
        
        # Background layer for stars and nebulae
        self.bg_layer = pygame.Surface((Settings.WIDTH, Settings.HEIGHT), pygame.SRCALPHA)
        
        # Initialize particles list
        self.particles = []
        
        # Initialize background stars
        self.stars = [BackgroundStar(Settings.WIDTH, Settings.HEIGHT) 
                     for _ in range(Settings.BG_STARS_COUNT)]
        
        # Menu animation variables
        self.title_pulse = 0
        self.title_pulse_dir = 1
        self.menu_time = 0
        
        # Load highscore and initialize game
        self.load_highscore()
        self.difficulty = 'medium'
        self.state = 'menu'  # Always start with menu
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
                    self.sound_manager.play('menu_select', 0.3)
                    
                    # Add some particles around the new selected option
                    y_pos = Settings.HEIGHT // 2 + self.menu_option * 50
                    for _ in range(10):
                        x = Settings.WIDTH // 2 + random.randint(-100, 100)
                        self.particles.append(Particle(
                            x, y_pos, Settings.COLORS['menu_select'], 
                            random.uniform(1, 3), random.randint(20, 40)))
                        
                elif event.key == pygame.K_DOWN:
                    self.menu_option = (self.menu_option + 1) % len(options)
                    self.sound_manager.play('menu_select', 0.3)
                    
                    # Add some particles around the new selected option
                    y_pos = Settings.HEIGHT // 2 + self.menu_option * 50
                    for _ in range(10):
                        x = Settings.WIDTH // 2 + random.randint(-100, 100)
                        self.particles.append(Particle(
                            x, y_pos, Settings.COLORS['menu_select'], 
                            random.uniform(1, 3), random.randint(20, 40)))
                        
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.sound_manager.play('menu_confirm', 0.5)
                    
                    # Add explosion effect
                    y_pos = Settings.HEIGHT // 2 + self.menu_option * 50
                    for _ in range(30):
                        self.particles.append(Particle(
                            Settings.WIDTH // 2, y_pos, 
                            Settings.COLORS['menu_select'], 
                            random.uniform(2, 5), random.randint(30, 60)))
                    
                    if self.menu_option < 3:  # Difficulty options
                        self.difficulty = options[self.menu_option].lower()
                    else:  # Start game
                        # Start background music if enabled
                        if self.sound_manager.music_enabled and not self.sound_manager.music_playing:
                            self.sound_manager.play_music(0.3)
                            
                        self.reset()
                        self.state = 'running'
                
                # Toggle sound with S key
                elif event.key == pygame.K_s:
                    enabled = self.sound_manager.toggle_sound()
                    # Play test sound if enabled
                    if enabled:
                        self.sound_manager.play('menu_select', 0.3)
                
                # Toggle music with M key
                elif event.key == pygame.K_m:
                    self.sound_manager.toggle_music()

    def draw_menu(self):
        options = ['Easy', 'Medium', 'Hard', 'Start Game']
        current_time = pygame.time.get_ticks() / 1000  # Time in seconds
        self.menu_time += 0.016  # Approximately 60 fps
        
        # Update title pulse effect
        self.title_pulse += Settings.TITLE_GLOW_SPEED * self.title_pulse_dir
        if self.title_pulse >= 1.0:
            self.title_pulse_dir = -1
        elif self.title_pulse <= 0.0:
            self.title_pulse_dir = 1
        
        # Update background stars
        for star in self.stars:
            star.update()
        
        # Update particles in menu
        self.particles = [p for p in self.particles if p.update()]
        
        # Add new particles occasionally
        if random.random() < 0.05:
            for _ in range(3):
                x = random.randint(0, Settings.WIDTH)
                y = random.randint(0, Settings.HEIGHT - 100)
                size = random.uniform(1.5, 3.0)
                color = random.choice([
                    Settings.COLORS['snake_head'],
                    Settings.COLORS['portal'],
                    Settings.COLORS['food'],
                    Settings.COLORS['power']
                ])
                self.particles.append(Particle(x, y, color, size))
        
        # Clear screen with black
        self.screen.fill((0, 0, 0))
        
        # Draw animated background layer
        self.bg_layer.fill((0, 0, 0, 0))
        
        # Draw stars
        for star in self.stars:
            star.draw(self.bg_layer)
            
        # Draw nebula-like effects
        for i in range(Settings.BG_NEBULA_COUNT):
            center_x = Settings.WIDTH // 2 + int(math.sin(current_time * 0.3 + i * 2) * 100)
            center_y = Settings.HEIGHT // 2 + int(math.cos(current_time * 0.2 + i * 3) * 80)
            radius = 100 + int(math.sin(current_time * 0.5 + i) * 20)
            color = list(Settings.COLORS['bg_glow'])
            color[0] = (color[0] + i * 40) % 255
            color[1] = (color[1] + i * 30) % 255
            
            # Create radial gradient
            for r in range(radius, 0, -20):
                alpha = max(0, min(150, int(100 * (r / radius))))
                pygame.draw.circle(self.bg_layer, (*color[:3], alpha), 
                                 (center_x, center_y), r)
        
        # Blit background onto screen
        self.screen.blit(self.bg_layer, (0, 0))
        
        # Draw grid lines for cyber effect
        for x in range(0, Settings.WIDTH, 40):
            intensity = int(20 + 10 * math.sin(x / 50 + current_time))
            pygame.draw.line(self.screen, (intensity, intensity * 1.5, intensity * 2), 
                           (x, 0), (x, Settings.HEIGHT), 1)
        
        for y in range(0, Settings.HEIGHT, 40):
            intensity = int(20 + 10 * math.sin(y / 50 + current_time))
            pygame.draw.line(self.screen, (intensity, intensity * 1.5, intensity * 2), 
                           (0, y), (Settings.WIDTH, y), 1)
        
        # Draw semi-transparent background for menu
        menu_bg = pygame.Surface((Settings.WIDTH, Settings.HEIGHT))
        menu_bg.fill(Settings.COLORS['menu_bg'])
        menu_bg.set_alpha(200)
        self.screen.blit(menu_bg, (0, 0))
        
        # Draw title with glow effect
        glow_size = 10 + int(20 * self.title_pulse)
        title_color = Settings.COLORS['title_glow']
        
        # Draw multiple layers for glow effect
        for size_offset in range(glow_size, 0, -2):
            alpha = int(200 * (1 - size_offset / glow_size))
            glow_font = pygame.font.Font(Settings.FONT_NAME, 48 + size_offset)
            glow_title = glow_font.render('CYBERSNAKE', True, (*title_color[:3], alpha))
            glow_rect = glow_title.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 4))
            self.screen.blit(glow_title, glow_rect)
        
        # Draw actual title
        title = self.big_font.render('CYBERSNAKE', True, Settings.COLORS['menu_select'])
        title_rect = title.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 4))
        self.screen.blit(title, title_rect)
        
        # Draw subtitle with wave effect
        subtitle = "Select Difficulty"
        subtitle_surface = pygame.Surface((300, 50), pygame.SRCALPHA)
        subtitle_surface.fill((0, 0, 0, 0))
        
        # Draw each character with individual wave effect
        x_offset = 0
        for i, char in enumerate(subtitle):
            char_y = math.sin(current_time * 3 + i * 0.2) * 5
            char_surf = self.font.render(char, True, Settings.COLORS['menu_text'])
            subtitle_surface.blit(char_surf, (x_offset, char_y + 15))
            x_offset += char_surf.get_width()
        
        subtitle_rect = subtitle_surface.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 4 + 60))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw options with animation
        for i, option in enumerate(options):
            # Wave effect for selected option
            is_selected = i == self.menu_option
            color = Settings.COLORS['menu_select'] if is_selected else Settings.COLORS['menu_text']
            
            y_pos = Settings.HEIGHT // 2 + i * 50
            
            if is_selected:
                # Animated prefix for selected option
                prefix_chars = "> "
                x_offset = 0
                prefix_surface = pygame.Surface((60, 40), pygame.SRCALPHA)
                prefix_surface.fill((0, 0, 0, 0))
                
                for j, char in enumerate(prefix_chars):
                    pulse = 0.5 + 0.5 * math.sin(current_time * 5 + j)
                    char_size = 32 + int(4 * pulse)
                    char_font = pygame.font.Font(Settings.FONT_NAME, char_size)
                    char_surf = char_font.render(char, True, color)
                    prefix_surface.blit(char_surf, (x_offset, 0))
                    x_offset += char_surf.get_width()
                
                # Position prefix
                prefix_rect = prefix_surface.get_rect(midright=(Settings.WIDTH // 2 - 10, y_pos))
                self.screen.blit(prefix_surface, prefix_rect)
                
                # Draw text with wave effect
                option_surface = pygame.Surface((200, 40), pygame.SRCALPHA)
                option_surface.fill((0, 0, 0, 0))
                
                x_offset = 0
                for j, char in enumerate(option):
                    char_y = math.sin(current_time * 4 + j * 0.3) * 3
                    char_surf = self.medium_font.render(char, True, color)
                    option_surface.blit(char_surf, (x_offset, char_y))
                    x_offset += char_surf.get_width()
                
                option_rect = option_surface.get_rect(midleft=(Settings.WIDTH // 2, y_pos))
                self.screen.blit(option_surface, option_rect)
            else:
                # Draw normal text for non-selected options
                text = self.medium_font.render(option, True, color)
                text_rect = text.get_rect(center=(Settings.WIDTH // 2, y_pos))
                self.screen.blit(text, text_rect)
            
            # Highlight current difficulty
            if i < 3 and option.lower() == self.difficulty:
                # Pulsating rectangle
                pulse = 0.5 + 0.5 * math.sin(current_time * 3)
                rect_size = (140 + int(20 * pulse), 40 + int(10 * pulse))
                rect = pygame.Rect(0, 0, *rect_size)
                rect.center = (Settings.WIDTH // 2, y_pos)
                
                pygame.draw.rect(self.screen, color, rect, 2, border_radius=5)
        
        # Draw sound and music toggle buttons
        sound_text = "Sound: " + ("ON" if self.sound_manager.sound_enabled else "OFF")
        music_text = "Music: " + ("ON" if self.sound_manager.music_enabled else "OFF")
        
        sound_surf = self.font.render(sound_text, True, Settings.COLORS['menu_text'])
        music_surf = self.font.render(music_text, True, Settings.COLORS['menu_text'])
        
        self.screen.blit(sound_surf, (20, Settings.HEIGHT - 60))
        self.screen.blit(music_surf, (20, Settings.HEIGHT - 30))
        
        # Draw controls hint
        controls_text = "Arrow keys: Navigate | Enter/Space: Select | S: Toggle Sound | M: Toggle Music"
        controls_surf = self.font.render(controls_text, True, Settings.COLORS['menu_text'])
        controls_rect = controls_surf.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT - 30))
        self.screen.blit(controls_surf, controls_rect)

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
            
            # Add warning particles around active mines
            if mine.active and random.random() < 0.1:
                px, py = mine.position
                x = px * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                y = py * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                
                # Create warning particles
                for _ in range(3):
                    angle = random.uniform(0, math.pi * 2)
                    distance = random.uniform(5, 15)
                    dx = math.cos(angle) * distance
                    dy = math.sin(angle) * distance
                    
                    self.particles.append(Particle(
                        x + dx, y + dy, 
                        (255, 0, 0) if pygame.time.get_ticks() % 1000 < 500 else Settings.COLORS['mine'],
                        random.uniform(1, 2), random.randint(10, 30)))
            
        # Update combo timer
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_counter = 0
            
        # Move snake
        self.snake.move()
        
        # Create trail particles behind snake
        if random.random() < 0.1:
            for pos in list(self.snake.positions)[1:4]:  # Only a few positions for performance
                if random.random() < 0.3:  # Not every position
                    px, py = pos
                    x = px * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                    y = py * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                    
                    self.particles.append(Particle(
                        x, y, Settings.COLORS['snake_body'], 
                        random.uniform(1, 3), random.randint(15, 40)))
        
        # Check portal teleportation
        teleported = self.check_portal_collision()
        if teleported:
            # Play teleport sound
            self.sound_manager.play('teleport', 0.4)
        
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
                        self.sound_manager.play('shield', 0.5)
                    else:
                        # Mine explosion
                        self.explosion_cells = mine.explode()
                        self.sound_manager.play('explosion', 0.6)
                        
                        # Add explosion particles
                        px, py = mine.position
                        center_x = px * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                        center_y = py * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                        
                        for _ in range(50):
                            distance = random.uniform(0, 30)
                            angle = random.uniform(0, math.pi * 2)
                            speed = random.uniform(1, 4)
                            
                            dx = math.cos(angle) * distance
                            dy = math.sin(angle) * distance
                            
                            # Particles fly outward from explosion center
                            direction = (math.cos(angle), math.sin(angle))
                            
                            self.particles.append(Particle(
                                center_x + dx, center_y + dy,
                                (255, random.randint(100, 200), 0),
                                random.uniform(2, 4), random.randint(20, 60),
                                speed, direction))
                        
                        # Check if snake is in explosion radius
                        if self.snake.head() in self.explosion_cells:
                            self.state = 'gameover'
                            self.sound_manager.play('game_over', 0.7)
                            if self.score > self.highscore:
                                self.highscore = self.score
                                self.save_highscore()
                            return
            
            # Check for collision with explosion cells
            for cell in self.explosion_cells:
                if self.snake.head() == cell and not self.snake.shield_active:
                    self.state = 'gameover'
                    self.sound_manager.play('game_over', 0.7)
                    if self.score > self.highscore:
                        self.highscore = self.score
                        self.save_highscore()
                    return
            
            # Check for self collision or obstacle collision
            if (self.snake.collides_self() or 
                self.snake.head() in self.obstacles) and not self.snake.shield_active:
                self.state = 'gameover'
                self.sound_manager.play('game_over', 0.7)
                if self.score > self.highscore:
                    self.highscore = self.score
                    self.save_highscore()
                return

        # Food collision
        if self.snake.head() == self.food.position:
            # Play eating sound
            self.sound_manager.play('eat', 0.4)
            
            self.snake.grow()
            
            # Add particles for eating effect
            px, py = self.food.position
            x = px * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
            y = py * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
            
            for _ in range(20):
                self.particles.append(Particle(
                    x, y, self.food.color, 
                    random.uniform(1, 3), random.randint(20, 60)))
            
            # Calculate score with combo multiplier
            combo_multiplier = min(5, max(1, self.combo_counter))
            base_points = 2 if self.food.power else 1
            if self.food.shield:
                base_points = 3
                self.snake.activate_shield()
                self.sound_manager.play('shield', 0.5)
                
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
            
            # Add slow-motion particles occasionally
            if random.random() < 0.05:
                px, py = self.snake.head()
                x = px * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                y = py * Settings.GRID_SIZE + Settings.GRID_SIZE // 2
                
                for _ in range(2):
                    self.particles.append(Particle(
                        x + random.uniform(-20, 20), 
                        y + random.uniform(-20, 20), 
                        Settings.COLORS['power'], 
                        random.uniform(1, 2), random.randint(20, 40)))
                
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
        
        current_time = pygame.time.get_ticks() / 1000  # Time in seconds
            
        # Update background stars
        for star in self.stars:
            star.update()
        
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
            
        # Draw background
        self.screen.fill(Settings.COLORS['bg'])
        
        # Draw stars
        self.bg_layer.fill((0, 0, 0, 0))
        for star in self.stars:
            star.draw(self.bg_layer)
        
        # Draw some nebula effects in background
        for i in range(1):  # Just one subtle nebula in gameplay
            center_x = Settings.WIDTH // 2 + int(math.sin(current_time * 0.1 + i * 2) * 100)
            center_y = Settings.HEIGHT // 2 + int(math.cos(current_time * 0.08 + i * 3) * 80)
            radius = 150 + int(math.sin(current_time * 0.3 + i) * 30)
            color = list(Settings.COLORS['bg_glow'])
            color[0] = (color[0] + i * 40) % 255
            color[1] = (color[1] + i * 30) % 255
            
            # Create radial gradient with lower opacity for gameplay
            for r in range(radius, 0, -20):
                alpha = max(0, min(40, int(30 * (r / radius))))
                pygame.draw.circle(self.bg_layer, (*color[:3], alpha), 
                                 (center_x, center_y), r)
        
        self.screen.blit(self.bg_layer, (0, 0))
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
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)

        self.screen.blit(self.glow_layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.draw_hud()

        if self.state == 'pause':
            # Create a semi-transparent overlay
            overlay = pygame.Surface((Settings.WIDTH, Settings.HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            self.screen.blit(overlay, (0, 0))
            
            # Create pulsating effect for pause text
            pulse = 0.5 + 0.5 * math.sin(current_time * 2)
            size_offset = int(10 * pulse)
            
            # Draw multiple pause texts with glow effect
            for offset in range(20, 0, -4):
                alpha = 255 - offset * 10
                size = 48 + offset + size_offset
                pause_font = pygame.font.Font(Settings.FONT_NAME, size)
                pause_text = pause_font.render('PAUSA', True, (*Settings.COLORS['title_glow'], alpha))
                text_rect = pause_text.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 2))
                self.screen.blit(pause_text, text_rect)
                
            # Draw main pause text
            self.draw_center_text('PAUSA', self.big_font)
            
            # Draw additional instructions
            instructions = self.font.render('Premi ESC per tornare al menu', True, Settings.COLORS['hud'])
            instr_rect = instructions.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 2 + 60))
            self.screen.blit(instructions, instr_rect)
            
        elif self.state == 'gameover':
            # Create a semi-transparent overlay with red tint
            overlay = pygame.Surface((Settings.WIDTH, Settings.HEIGHT))
            overlay.fill((40, 0, 0))
            overlay.set_alpha(150)
            self.screen.blit(overlay, (0, 0))
            
            # Draw game over text with glow
            glow_color = (255, 50, 50)
            for offset in range(20, 0, -4):
                alpha = 255 - offset * 10
                size = 48 + offset
                font = pygame.font.Font(Settings.FONT_NAME, size)
                text = font.render('GAME OVER', True, (*glow_color, alpha))
                text_rect = text.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 2 - 30))
                self.screen.blit(text, text_rect)
            
            # Main game over text
            game_over = self.big_font.render('GAME OVER', True, (255, 50, 50))
            game_over_rect = game_over.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 2 - 30))
            self.screen.blit(game_over, game_over_rect)
            
            # Instructions with wave effect
            restart_text = "Premi R per ripartire"
            x_offset = 0
            text_surface = pygame.Surface((400, 40), pygame.SRCALPHA)
            text_surface.fill((0, 0, 0, 0))
            
            for i, char in enumerate(restart_text):
                char_y = math.sin(current_time * 4 + i * 0.3) * 3
                char_surf = self.font.render(char, True, Settings.COLORS['hud'])
                text_surface.blit(char_surf, (x_offset, char_y))
                x_offset += char_surf.get_width()
            
            text_rect = text_surface.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 2 + 30))
            self.screen.blit(text_surface, text_rect)
            
            # Menu option
            menu_text = self.font.render("Premi ESC per tornare al menu", True, Settings.COLORS['hud'])
            menu_rect = menu_text.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 2 + 70))
            self.screen.blit(menu_text, menu_rect)

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