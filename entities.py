import pygame
import random
import math
from settings import (
    SIM_W, SIM_H, OBS_COUNT, ENERGY_COUNT,
    OBSTACLE_COLOR, OBSTACLE_BORDER, ENERGY_COLOR, WHITE,
    ROBOT_COLOR, ELITE_COLOR, DEAD_COLOR, GREEN, AMBER, RED,
)
from genetics import DNA


# ---------------------------------------------------------------------------
# ROBOT
# ---------------------------------------------------------------------------
class Robot:
    TRAIL_LEN = 20
    RADIUS    = 7

    def __init__(self, dna=None, sim_w=SIM_W, sim_h=SIM_H):
        self.dna      = dna or DNA()
        self.x        = random.uniform(20, sim_w - 20)
        self.y        = random.uniform(20, sim_h - 20)
        self.angle    = random.uniform(0, math.pi * 2)
        self.energy   = 1.0
        self.fitness  = 0.0
        self.alive    = True
        self.trail    = []
        self.is_elite = False
        self.sim_w    = sim_w
        self.sim_h    = sim_h

    def sense_nearest_energy(self, energies):
        best, best_d = None, float('inf')
        for e in energies:
            if not e.alive: continue
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < self.dna.sensor_range and d < best_d:
                best, best_d = e, d
        return best

    def sense_nearest_obstacle(self, obstacles):
        best, best_d = None, float('inf')
        for obs in obstacles:
            d = math.hypot(obs.rect.centerx - self.x, obs.rect.centery - self.y)
            if d < self.dna.sensor_range and d < best_d:
                best, best_d = obs, d
        return best, best_d

    def update(self, energies, obstacles):
        if not self.alive:
            return
        delta  = (random.random() - 0.5) * self.dna.turn_rate * 2
        near_e = self.sense_nearest_energy(energies)
        if near_e:
            target = math.atan2(near_e.y - self.y, near_e.x - self.x)
            diff   = target - self.angle
            while diff >  math.pi: diff -= 2 * math.pi
            while diff < -math.pi: diff += 2 * math.pi
            delta += diff * 0.12 * self.dna.aggression

        near_o, do = self.sense_nearest_obstacle(obstacles)
        if near_o:
            away = math.atan2(self.y - near_o.rect.centery,
                              self.x - near_o.rect.centerx)
            diff = away - self.angle
            while diff >  math.pi: diff -= 2 * math.pi
            while diff < -math.pi: diff += 2 * math.pi
            delta += diff * max(0, 1 - do / 60) * 0.35

        self.angle += max(-self.dna.turn_rate, min(self.dna.turn_rate, delta))
        nx = self.x + math.cos(self.angle) * self.dna.speed
        ny = self.y + math.sin(self.angle) * self.dna.speed

        if nx < self.RADIUS or nx > self.sim_w - self.RADIUS:
            self.angle = math.pi - self.angle
            nx = max(self.RADIUS, min(self.sim_w - self.RADIUS, nx))
        if ny < self.RADIUS or ny > self.sim_h - self.RADIUS:
            self.angle = -self.angle
            ny = max(self.RADIUS, min(self.sim_h - self.RADIUS, ny))

        hit = any(obs.rect.inflate(self.RADIUS*2, self.RADIUS*2).collidepoint(nx, ny)
                  for obs in obstacles)
        if hit:
            self.fitness -= 2
            self.energy  -= 0.05
            self.angle   += math.pi + random.uniform(-0.4, 0.4)
        else:
            self.x, self.y = nx, ny

        for e in energies:
            if e.alive and math.hypot(e.x - self.x, e.y - self.y) < self.RADIUS + e.radius:
                e.alive       = False
                self.fitness += 10
                self.energy   = min(1.0, self.energy + 0.3)

        self.energy  -= 0.0018
        self.fitness += 0.01
        if self.energy <= 0:
            self.alive   = False
            self.fitness -= 5

        self.trail.append((self.x, self.y))
        if len(self.trail) > self.TRAIL_LEN:
            self.trail.pop(0)

    def draw(self, surface):
        if len(self.trail) > 1:
            ts = pygame.Surface((self.sim_w, self.sim_h), pygame.SRCALPHA)
            for i in range(1, len(self.trail)):
                alpha = int(50 * i / len(self.trail))
                col   = (*ELITE_COLOR, alpha) if self.is_elite else (*ROBOT_COLOR, alpha)
                pygame.draw.line(ts, col,
                                 (int(self.trail[i-1][0]), int(self.trail[i-1][1])),
                                 (int(self.trail[i][0]),   int(self.trail[i][1])), 1)
            surface.blit(ts, (0, 0))

        if not self.alive:
            pygame.draw.line(surface, DEAD_COLOR,
                             (int(self.x)-5, int(self.y)-5),
                             (int(self.x)+5, int(self.y)+5), 2)
            pygame.draw.line(surface, DEAD_COLOR,
                             (int(self.x)+5, int(self.y)-5),
                             (int(self.x)-5, int(self.y)+5), 2)
            return

        if self.is_elite:
            ss = pygame.Surface((self.sim_w, self.sim_h), pygame.SRCALPHA)
            pygame.draw.circle(ss, (*ELITE_COLOR, 14),
                               (int(self.x), int(self.y)),
                               int(self.dna.sensor_range))
            surface.blit(ss, (0, 0))

        col = ELITE_COLOR if self.is_elite else ROBOT_COLOR
        pts = [
            (self.x + math.cos(self.angle)           * 10,
             self.y + math.sin(self.angle)           * 10),
            (self.x + math.cos(self.angle + 2.4)     * 7,
             self.y + math.sin(self.angle + 2.4)     * 7),
            (self.x + math.cos(self.angle + math.pi) * 4,
             self.y + math.sin(self.angle + math.pi) * 4),
            (self.x + math.cos(self.angle - 2.4)     * 7,
             self.y + math.sin(self.angle - 2.4)     * 7),
        ]
        pygame.draw.polygon(surface, col, pts)

        bw = 14
        bx = int(self.x - bw / 2)
        by = int(self.y - 14)
        pygame.draw.rect(surface, (30, 30, 30), (bx, by, bw, 3))
        bc = GREEN if self.energy > 0.4 else AMBER if self.energy > 0.2 else RED
        pygame.draw.rect(surface, bc, (bx, by, int(self.energy * bw), 3))


# ---------------------------------------------------------------------------
# OBSTACLE
# ---------------------------------------------------------------------------
class Obstacle:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        pygame.draw.rect(surface, OBSTACLE_COLOR, self.rect, border_radius=4)
        pygame.draw.rect(surface, OBSTACLE_BORDER, self.rect, 1, border_radius=4)


# ---------------------------------------------------------------------------
# ENERGY
# ---------------------------------------------------------------------------
class Energy:
    def __init__(self, sw=SIM_W, sh=SIM_H):
        self.x      = random.randint(15, sw - 15)
        self.y      = random.randint(15, sh - 15)
        self.alive  = True
        self.pulse  = random.uniform(0, math.pi * 2)
        self.radius = 6

    def update(self):
        self.pulse += 0.07

    def draw(self, surface):
        if not self.alive:
            return
        r    = self.radius + math.sin(self.pulse) * 2
        glow = pygame.Surface((int(r*4)+2, int(r*4)+2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*ENERGY_COLOR, 35),
                           (int(r*2), int(r*2)), int(r*2))
        surface.blit(glow, (int(self.x - r*2), int(self.y - r*2)))
        pygame.draw.circle(surface, ENERGY_COLOR, (int(self.x), int(self.y)), int(r))
        pygame.draw.circle(surface, WHITE,         (int(self.x), int(self.y)), max(2, int(r*0.35)))


# ---------------------------------------------------------------------------
# SPAWN HELPERS
# ---------------------------------------------------------------------------
def spawn_obstacles(sw=SIM_W, sh=SIM_H, count=None):
    count = count or OBS_COUNT
    obs = []
    for _ in range(count):
        w = random.randint(20, 80)
        h = random.randint(12, 40)
        x = random.randint(10, sw - w - 10)
        y = random.randint(10, sh - h - 10)
        obs.append(Obstacle(x, y, w, h))
    return obs


def spawn_energies(sw=SIM_W, sh=SIM_H, count=None):
    count = count or ENERGY_COUNT
    return [Energy(sw, sh) for _ in range(count)]


def spawn_robots(ga, dna_list=None):
    robots = []
    for i in range(ga.pop_size):
        dna = dna_list[i] if dna_list else DNA()
        r   = Robot(dna)
        r.is_elite = (i < ga.elite_count)
        robots.append(r)
    return robots