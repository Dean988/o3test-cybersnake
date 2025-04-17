#!/usr/bin/env python3
'''
CyberSnake - Advanced Snake game with cybernetic neon graphics.
Autore: ChatGPT
Dipendenze: pygame (pip install pygame)
Esegui: python cyber_snake.py
'''
import pygame
import random
import os
from collections import deque


class Settings:
    GRID_SIZE = 20
    GRID_W = 30
    GRID_H = 30
    WIDTH = GRID_SIZE * GRID_W
    HEIGHT = GRID_SIZE * GRID_H + 60  # Space for HUD
    FPS_BASE = 8
    MAX_FPS = 25
    COLORS = {
        'bg': (10, 10, 10),
        'grid': (30, 30, 30),
        'snake_head': (0, 255, 255),
        'snake_body': (0, 200, 200),
        'food': (0, 255, 128),
        'power': (255, 0, 255),
        'obst': (255, 64, 64),
        'hud': (200, 200, 200),
    }
    FONT_NAME = 'freesansbold.ttf'
    HIGHSCORE_FILE = 'highscore.txt'


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.positions = deque([(Settings.GRID_W // 2, Settings.GRID_H // 2)])
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.grow_pending = 2

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

    def grow(self, n=1):
        self.grow_pending += n

    def collides_self(self):
        return self.head() in list(self.positions)[1:]

    def draw(self, surf, glow_layer):
        for i, pos in enumerate(self.positions):
            px, py = pos
            rect = pygame.Rect(px * Settings.GRID_SIZE, py * Settings.GRID_SIZE,
                               Settings.GRID_SIZE, Settings.GRID_SIZE)
            color = Settings.COLORS['snake_head'] if i == 0 else Settings.COLORS['snake_body']
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(glow_layer, color, rect.inflate(6, 6), border_radius=8)


class Food:
    def __init__(self, power=False):
        self.power = power
        self.color = Settings.COLORS['power'] if power else Settings.COLORS['food']
        self.position = (0, 0)

    def randomize(self, occupied):
        while True:
            p = (random.randint(0, Settings.GRID_W - 1), random.randint(0, Settings.GRID_H - 1))
            if p not in occupied:
                self.position = p
                break

    def draw(self, surf, glow_layer):
        px, py = self.position
        rect = pygame.Rect(px * Settings.GRID_SIZE, py * Settings.GRID_SIZE,
                           Settings.GRID_SIZE, Settings.GRID_SIZE)
        pygame.draw.rect(surf, self.color, rect)
        pygame.draw.rect(glow_layer, self.color, rect.inflate(6, 6), border_radius=8)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Settings.WIDTH, Settings.HEIGHT))
        pygame.display.set_caption('CyberSnake')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(Settings.FONT_NAME, 24)
        self.big_font = pygame.font.Font(Settings.FONT_NAME, 48)

        self.grid_surface = pygame.Surface((Settings.WIDTH, Settings.HEIGHT - 60))
        self.grid_surface.set_alpha(80)
        self.create_grid()

        self.glow_layer = pygame.Surface((Settings.WIDTH, Settings.HEIGHT - 60), pygame.SRCALPHA)

        self.load_highscore()
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
        self.score = 0
        self.speed = Settings.FPS_BASE
        self.food = Food()
        self.food.randomize(set(self.snake.positions))
        self.power_timer = 0
        self.state = 'running'

    def spawn_obstacle(self):
        occupied = set(self.snake.positions) | {self.food.position}
        while True:
            p = (random.randint(0, Settings.GRID_W - 1), random.randint(0, Settings.GRID_H - 1))
            if p not in occupied and p not in self.obstacles:
                self.obstacles.append(p)
                break

    def handle_events(self):
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
                if self.state != 'running':
                    continue
                if event.key in dir_map:
                    self.snake.turn(dir_map[event.key])
                elif event.key == pygame.K_r and self.state == 'gameover':
                    self.reset()

    def update(self):
        if self.state != 'running':
            return
        self.snake.move()
        if self.snake.collides_self() or self.snake.head() in self.obstacles:
            self.state = 'gameover'
            if self.score > self.highscore:
                self.highscore = self.score
                self.save_highscore()
            return

        # Food collision
        if self.snake.head() == self.food.position:
            self.snake.grow()
            gained = 2 if self.food.power else 1
            self.score += gained
            if self.score % 5 == 0 and len(self.obstacles) < 20:
                self.spawn_obstacle()
            self.speed = min(Settings.FPS_BASE + self.score // 4, Settings.MAX_FPS)
            power = random.random() < 0.15
            self.food = Food(power)
            self.food.randomize(set(self.snake.positions) | set(self.obstacles))
            if power:
                self.power_timer = 120  # ~3-4 seconds
                self.speed = max(self.speed - 5, 5)

        # Power timer
        if self.power_timer:
            self.power_timer -= 1
            if self.power_timer == 0:
                self.speed = min(Settings.FPS_BASE + self.score // 4, Settings.MAX_FPS)

    def draw_hud(self):
        hud_rect = pygame.Rect(0, Settings.HEIGHT - 60, Settings.WIDTH, 60)
        pygame.draw.rect(self.screen, Settings.COLORS['bg'], hud_rect)
        text = f'Score: {self.score}   High Score: {self.highscore}   Speed: {self.speed}'
        surf = self.font.render(text, True, Settings.COLORS['hud'])
        self.screen.blit(surf, (20, Settings.HEIGHT - 45))

    def draw_obstacles(self):
        for p in self.obstacles:
            rect = pygame.Rect(p[0] * Settings.GRID_SIZE, p[1] * Settings.GRID_SIZE,
                               Settings.GRID_SIZE, Settings.GRID_SIZE)
            pygame.draw.rect(self.screen, Settings.COLORS['obst'], rect)
            pygame.draw.rect(self.glow_layer, Settings.COLORS['obst'], rect.inflate(6, 6), border_radius=8)

    def render(self):
        self.screen.fill(Settings.COLORS['bg'])
        self.screen.blit(self.grid_surface, (0, 0))
        self.glow_layer.fill((0, 0, 0, 0))

        self.draw_obstacles()
        self.food.draw(self.screen, self.glow_layer)
        self.snake.draw(self.screen, self.glow_layer)

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