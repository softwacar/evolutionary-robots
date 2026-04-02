import pygame
import sys

from settings import (
    SCREEN_W, SCREEN_H, SIM_W, SIM_H, PANEL_X, FPS,
    POPULATION, ENERGY_COUNT, OBS_COUNT, GEN_TICKS, ELITE_COUNT, MUTATION_RATE,
    BG_COLOR, SIM_BG, PANEL_BG, OBSTACLE_COLOR, OBSTACLE_BORDER,
    ROBOT_COLOR, ELITE_COLOR, DEAD_COLOR, TEXT_COLOR, TEXT_DIM,
    WHITE, GREEN, AMBER, RED, GRID_COLOR,
)
from genetics import DNA, GeneticAlgorithm
from entities import spawn_obstacles, spawn_energies, spawn_robots
from report  import ParameterPanel, ComparisonMode, build_report_surface


# ---------------------------------------------------------------------------
# DRAW HELPERS
# ---------------------------------------------------------------------------
def draw_stat_card(screen, fs, fm, x, y, label, value, color=WHITE):
    pygame.draw.rect(screen, OBSTACLE_COLOR, pygame.Rect(x, y, 224, 38), border_radius=6)
    screen.blit(fs.render(label, True, TEXT_DIM), (x+6, y+4))
    screen.blit(fm.render(str(value), True, color), (x+6, y+20))


def draw_bar(screen, fs, x, y, label, value, mn, mx, color):
    pct = (value - mn) / (mx - mn)
    screen.blit(fs.render(label, True, TEXT_DIM), (x, y))
    pygame.draw.rect(screen, OBSTACLE_COLOR, pygame.Rect(x, y+14, 185, 5), border_radius=2)
    pygame.draw.rect(screen, color, pygame.Rect(x, y+14, int(pct*185), 5), border_radius=2)
    screen.blit(fs.render(f"{value:.2f}", True, color), (x+190, y+10))


def draw_mini_graph(screen, best_hist, avg_hist, x, y, w, h):
    pygame.draw.rect(screen, OBSTACLE_COLOR, pygame.Rect(x, y, w, h), border_radius=4)
    if len(best_hist) < 2:
        return
    max_v = max(best_hist) if max(best_hist) > 0 else 1
    min_v = min(avg_hist)
    rng   = max(max_v - min_v, 1)
    n     = len(best_hist)

    def pt(val, i):
        return (x + int(i/(n-1)*w),
                y + h - int((val - min_v)/rng*(h-4)) - 2)

    for i in range(1, n):
        pygame.draw.line(screen, ROBOT_COLOR, pt(avg_hist[i-1], i-1), pt(avg_hist[i], i), 1)
    for i in range(1, n):
        pygame.draw.line(screen, AMBER,       pt(best_hist[i-1],i-1), pt(best_hist[i],i), 2)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Evolutionary Robots — Final")
    clock  = pygame.time.Clock()

    font_big   = pygame.font.SysFont("consolas", 17, bold=True)
    font_med   = pygame.font.SysFont("consolas", 14)
    font_small = pygame.font.SysFont("consolas", 12)

    # Current config (editable via parameter panel)
    cfg = {
        'population':    POPULATION,
        'mutation_rate': MUTATION_RATE,
        'elite_count':   ELITE_COUNT,
        'gen_ticks':     GEN_TICKS,
        'energy_count':  ENERGY_COUNT,
        'obs_count':     OBS_COUNT,
    }

    def make_ga():
        return GeneticAlgorithm(
            pop   = cfg['population'],
            elite = cfg['elite_count'],
            mut   = cfg['mutation_rate'],
            ticks = cfg['gen_ticks'],
        )

    ga        = make_ga()
    obstacles = spawn_obstacles(count=cfg['obs_count'])
    energies  = spawn_energies(count=cfg['energy_count'])
    robots    = spawn_robots(ga)
    tick      = 0
    speed     = 1
    paused    = False

    param_panel   = ParameterPanel(cfg)
    cmp_mode      = ComparisonMode()
    show_params   = False
    show_report   = False
    report_surf   = None
    report_scaled = None
    report_gen    = -1

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                # --- Parameter panel open ---
                if show_params:
                    result = param_panel.handle_key(event.key)
                    if result == 'apply':
                        show_params = False
                        ga          = make_ga()
                        obstacles   = spawn_obstacles(count=cfg['obs_count'])
                        energies    = spawn_energies(count=cfg['energy_count'])
                        robots      = spawn_robots(ga)
                        tick        = 0
                        show_report = False
                    elif event.key == pygame.K_ESCAPE:
                        show_params = False
                    continue

                # --- Report open ---
                if show_report:
                    if event.key in (pygame.K_ESCAPE, pygame.K_g):
                        show_report = False
                    continue

                # --- Comparison running ---
                if cmp_mode.running:
                    continue

                # --- Normal keys ---
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    tick = cfg['gen_ticks']
                elif event.key == pygame.K_UP:
                    speed = min(speed + 1, 10)
                elif event.key == pygame.K_DOWN:
                    speed = max(speed - 1, 1)
                elif event.key == pygame.K_p:
                    show_params = True
                elif event.key == pygame.K_c:
                    cmp_mode.num_gens = 20
                    cmp_mode.start(dict(cfg))
                    paused = True
                elif event.key == pygame.K_g:
                    if show_report:
                        show_report = False
                    else:
                        if report_scaled is None or ga.generation != report_gen:
                            surf = build_report_surface(ga, cmp_mode)
                            if surf:
                                rw, rh = surf.get_size()
                                scale  = min(SCREEN_W/rw, SCREEN_H/rh, 1.0)
                                report_scaled = pygame.transform.smoothscale(
                                    surf, (int(rw*scale), int(rh*scale)))
                                report_gen = ga.generation
                        if report_scaled:
                            show_report = True
                elif event.key == pygame.K_r:
                    ga            = make_ga()
                    obstacles     = spawn_obstacles(count=cfg['obs_count'])
                    energies      = spawn_energies(count=cfg['energy_count'])
                    robots        = spawn_robots(ga)
                    tick          = 0
                    show_report   = False
                    cmp_mode      = ComparisonMode()
                    report_scaled = None
                    report_gen    = -1

        # --- Comparison mode step (one run per frame) ---
        if cmp_mode.running:
            done = cmp_mode.run_step()
            if done:
                paused = False

        # --- Simulation ---
        if not paused and not show_params and not cmp_mode.running:
            for _ in range(speed):
                for r in robots: r.update(energies, obstacles)
                for e in energies: e.update()
                tick += 1
                if tick >= cfg['gen_ticks']:
                    new_dna, _, _ = ga.evolve(robots)
                    obstacles = spawn_obstacles(count=cfg['obs_count'])
                    energies  = spawn_energies(count=cfg['energy_count'])
                    robots    = spawn_robots(ga, new_dna)
                    tick      = 0
                    break

        # ---- Draw simulation ----
        screen.fill(BG_COLOR)
        sim_surf = pygame.Surface((SIM_W, SIM_H))
        sim_surf.fill(SIM_BG)
        for gx in range(0, SIM_W, 32):
            pygame.draw.line(sim_surf, GRID_COLOR, (gx, 0), (gx, SIM_H))
        for gy in range(0, SIM_H, 32):
            pygame.draw.line(sim_surf, GRID_COLOR, (0, gy), (SIM_W, gy))
        for obs in obstacles: obs.draw(sim_surf)
        for e   in energies:  e.draw(sim_surf)
        for r   in robots:    r.draw(sim_surf)

        prog = tick / cfg['gen_ticks']
        pygame.draw.rect(sim_surf, (25, 33, 50), (0, SIM_H-6, SIM_W, 6))
        pygame.draw.rect(sim_surf, ROBOT_COLOR,  (0, SIM_H-6, int(SIM_W*prog), 6))
        screen.blit(sim_surf, (0, 0))
        pygame.draw.rect(screen, OBSTACLE_BORDER, (0, 0, SIM_W, SIM_H), 1)

        # ---- Right panel ----
        pygame.draw.rect(screen, PANEL_BG,
                         pygame.Rect(PANEL_X, 0, SCREEN_W-PANEL_X, SCREEN_H))
        pygame.draw.line(screen, OBSTACLE_BORDER,
                         (PANEL_X, 0), (PANEL_X, SCREEN_H), 1)

        px = PANEL_X + 8
        screen.blit(font_big.render("EVOLUTIONARY ROBOTS", True, ROBOT_COLOR), (px, 10))
        screen.blit(font_small.render(
            f"Gen:{ga.generation}  Tick:{tick}/{cfg['gen_ticks']}", True, TEXT_DIM), (px, 30))
        screen.blit(font_small.render(
            f"Pop:{cfg['population']}  Mut:{cfg['mutation_rate']:.2f}  Speed:{speed}x",
            True, TEXT_DIM), (px, 44))

        alive_count  = sum(1 for r in robots if r.alive)
        best_fitness = max(r.fitness for r in robots)
        avg_fitness  = sum(r.fitness for r in robots) / len(robots)
        energy_left  = sum(1 for e in energies if e.alive)

        y = 62
        draw_stat_card(screen, font_small, font_med, px, y,
                       "Best Fitness", f"{best_fitness:.1f}", AMBER)
        y += 44
        draw_stat_card(screen, font_small, font_med, px, y,
                       "Avg Fitness", f"{avg_fitness:.1f}")
        y += 44
        draw_stat_card(screen, font_small, font_med, px, y,
                       "Alive", f"{alive_count}/{cfg['population']}",
                       GREEN if alive_count > cfg['population']//2 else RED)
        y += 44
        draw_stat_card(screen, font_small, font_med, px, y,
                       "Energy Left", str(energy_left), GREEN)
        y += 50

        screen.blit(font_small.render("Fitness history:", True, TEXT_DIM), (px, y))
        y += 14
        draw_mini_graph(screen, ga.best_history, ga.avg_history, px, y, 224, 62)
        pygame.draw.line(screen, AMBER,       (px+4,  y+70), (px+18, y+70), 2)
        screen.blit(font_small.render("best", True, AMBER),       (px+22, y+66))
        pygame.draw.line(screen, ROBOT_COLOR, (px+58, y+70), (px+72, y+70), 1)
        screen.blit(font_small.render("avg",  True, ROBOT_COLOR), (px+76, y+66))
        y += 86

        best_robot = max(robots, key=lambda r: r.fitness)
        d = best_robot.dna
        screen.blit(font_small.render("--- Best Robot DNA ---", True, TEXT_DIM), (px, y))
        y += 16
        draw_bar(screen, font_small, px, y, "Speed",
                 d.speed, DNA.SPEED_MIN, DNA.SPEED_MAX, ROBOT_COLOR);    y += 26
        draw_bar(screen, font_small, px, y, "Turn Rate",
                 d.turn_rate, DNA.TURN_MIN, DNA.TURN_MAX, GREEN);         y += 26
        draw_bar(screen, font_small, px, y, "Sensor Range",
                 d.sensor_range, DNA.SENSOR_MIN, DNA.SENSOR_MAX, AMBER);  y += 26
        draw_bar(screen, font_small, px, y, "Aggression",
                 d.aggression, DNA.AGG_MIN, DNA.AGG_MAX, RED);             y += 30

        for line in ["P:params  C:compare  G:report",
                     "SPACE:pause  RIGHT:skip",
                     "UP/DOWN:speed  R:reset  ESC:quit"]:
            screen.blit(font_small.render(line, True, TEXT_DIM), (px, y))
            y += 14

        # Overlays
        if cmp_mode.running:
            cmp_mode.draw_progress(screen, font_big, font_med, font_small)

        if show_params:
            param_panel.draw(screen, font_big, font_med, font_small)

        if show_report and report_scaled:
            ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 210))
            screen.blit(ov, (0, 0))
            rx = (SCREEN_W - report_scaled.get_width())  // 2
            ry = (SCREEN_H - report_scaled.get_height()) // 2
            screen.blit(report_scaled, (rx, ry))
            msg = font_small.render("Press G or ESC to close", True, TEXT_DIM)
            screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H - 22))

        if paused and not show_params and not cmp_mode.running and not show_report:
            p = font_big.render("PAUSED", True, AMBER)
            screen.blit(p, (SIM_W//2 - p.get_width()//2, SIM_H//2 - 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()