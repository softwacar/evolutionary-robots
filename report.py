import pygame
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io

from settings import (
    SCREEN_W, SCREEN_H, PANEL_BG, OBSTACLE_COLOR, OBSTACLE_BORDER,
    ROBOT_COLOR, TEXT_DIM, TEXT_COLOR, WHITE, GREEN, AMBER, RED,
)
from genetics import DNA, GeneticAlgorithm
from entities import spawn_obstacles, spawn_energies, spawn_robots



# FAST SIMULATION  (no rendering, for comparison mode)
def run_fast_sim(pop, elite, mut_rate, gen_ticks, num_gens, obs_count, energy_count):
    """Run a full simulation silently and return best/avg history."""
    ga       = GeneticAlgorithm(pop=pop, elite=elite, mut=mut_rate, ticks=gen_ticks)
    obs      = spawn_obstacles(count=obs_count)
    energies = spawn_energies(count=energy_count)
    robots   = spawn_robots(ga)

    for _ in range(num_gens):
        pygame.event.pump()          # keep window responsive during heavy calc
        for _t in range(gen_ticks):
            for r in robots:
                r.update(energies, obs)
        new_dna, _, _ = ga.evolve(robots)
        obs      = spawn_obstacles(count=obs_count)
        energies = spawn_energies(count=energy_count)
        robots   = spawn_robots(ga, new_dna)

    return ga.best_history, ga.avg_history



# PARAMETER PANEL
class ParameterPanel:
    """
    Overlay panel for editing simulation parameters.
    Keys: UP/DOWN to select row, LEFT/RIGHT to change value, ENTER to apply.
    """
    def __init__(self, cfg):
        self.cfg      = cfg
        self.selected = 0
        self.params   = [
            # (label, key, min, max, step, format)
            ("Population",     "population",    10,  100, 5,    "{}"),
            ("Mutation Rate",  "mutation_rate", 0.01, 0.50, 0.01, "{:.2f}"),
            ("Elite Count",    "elite_count",   2,   12,  1,    "{}"),
            ("Gen Ticks",      "gen_ticks",     100, 800, 50,   "{}"),
            ("Energy Count",   "energy_count",  5,   40,  5,    "{}"),
            ("Obstacle Count", "obs_count",     0,   20,  1,    "{}"),
        ]

    def handle_key(self, key):
        """Returns 'apply' if ENTER pressed, else None."""
        if key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self.params)
        elif key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.params)
        elif key in (pygame.K_LEFT, pygame.K_RIGHT):
            _, k, mn, mx, step, _ = self.params[self.selected]
            val  = self.cfg[k]
            val += step if key == pygame.K_RIGHT else -step
            self.cfg[k] = max(mn, min(mx, round(val, 4)))
        elif key == pygame.K_RETURN:
            return 'apply'
        return None

    def draw(self, screen, font_big, font_med, font_small):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        pw, ph = 480, 360
        px     = (SCREEN_W - pw) // 2
        py     = (SCREEN_H - ph) // 2
        pygame.draw.rect(screen, PANEL_BG,        pygame.Rect(px, py, pw, ph), border_radius=10)
        pygame.draw.rect(screen, OBSTACLE_BORDER, pygame.Rect(px, py, pw, ph), 1, border_radius=10)

        screen.blit(font_big.render("PARAMETER SETTINGS", True, ROBOT_COLOR),
                    (px + 20, py + 16))
        screen.blit(font_small.render("UP/DOWN: select   LEFT/RIGHT: change   ENTER: apply & restart",
                                      True, TEXT_DIM), (px + 20, py + 38))

        y = py + 65
        for i, (label, key, mn, mx, step, fmt) in enumerate(self.params):
            row_rect = pygame.Rect(px + 12, y - 4, pw - 24, 34)
            if i == self.selected:
                pygame.draw.rect(screen, OBSTACLE_COLOR, row_rect, border_radius=6)
                pygame.draw.rect(screen, ROBOT_COLOR,    row_rect, 1, border_radius=6)

            val      = self.cfg[key]
            val_str  = fmt.format(val)
            pct      = (val - mn) / (mx - mn)
            bar_x    = px + 220
            bar_w    = pw - 240

            screen.blit(font_med.render(label, True,
                        ROBOT_COLOR if i == self.selected else TEXT_COLOR),
                        (px + 20, y + 4))

            pygame.draw.rect(screen, (25, 33, 50),
                             pygame.Rect(bar_x, y + 10, bar_w, 8), border_radius=4)
            bar_color = AMBER if i == self.selected else OBSTACLE_BORDER
            pygame.draw.rect(screen, bar_color,
                             pygame.Rect(bar_x, y + 10, int(pct * bar_w), 8), border_radius=4)

            val_surf = font_med.render(val_str, True,
                                       AMBER if i == self.selected else WHITE)
            screen.blit(val_surf, (bar_x + bar_w + 8, y + 4))
            y += 42

        screen.blit(font_small.render("ESC: close without applying", True, TEXT_DIM),
                    (px + 20, py + ph - 24))



# COMPARISON MODE
class ComparisonMode:
    """
    Runs 3 fast simulations with different mutation rates and stores results.
    """
    RATES  = [0.05, 0.15, 0.40]
    COLORS = ['#27c99a', '#4a9eff', '#e05555']
    LABELS = ['5% mutation', '15% mutation', '40% mutation']

    def __init__(self):
        self.results  = []
        self.running  = False
        self.done     = False
        self.progress = 0
        self.num_gens = 20
        self.cfg      = None

    def start(self, cfg):
        self.cfg      = cfg
        self.results  = []
        self.done     = False
        self.running  = True
        self.progress = 0

    def run_step(self):
        """Call once per frame while running; returns True when done."""
        if not self.running or self.done:
            return self.done

        idx = len(self.results)
        if idx >= len(self.RATES):
            self.done    = True
            self.running = False
            return True

        rate      = self.RATES[idx]
        best, avg = run_fast_sim(
            pop          = self.cfg['population'],
            elite        = self.cfg['elite_count'],
            mut_rate     = rate,
            gen_ticks    = self.cfg['gen_ticks'],
            num_gens     = self.num_gens,
            obs_count    = self.cfg['obs_count'],
            energy_count = self.cfg['energy_count'],
        )
        self.results.append((best, avg))
        self.progress = int((idx + 1) / len(self.RATES) * 100)
        return False

    def draw_progress(self, screen, font_big, font_med, font_small):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        pw, ph = 420, 180
        px     = (SCREEN_W - pw) // 2
        py     = (SCREEN_H - ph) // 2
        pygame.draw.rect(screen, PANEL_BG,        pygame.Rect(px, py, pw, ph), border_radius=10)
        pygame.draw.rect(screen, OBSTACLE_BORDER, pygame.Rect(px, py, pw, ph), 1, border_radius=10)

        screen.blit(font_big.render("RUNNING COMPARISON...", True, ROBOT_COLOR),
                    (px + 20, py + 20))

        idx = len(self.results)
        for i, (label, col) in enumerate(zip(self.LABELS, [GREEN, ROBOT_COLOR, RED])):
            status = "Done" if i < idx else ("Running..." if i == idx else "Waiting")
            color  = GREEN if i < idx else (AMBER if i == idx else TEXT_DIM)
            screen.blit(font_med.render(f"  {label}: {status}", True, color),
                        (px + 20, py + 60 + i * 26))

        bar_y = py + ph - 36
        pygame.draw.rect(screen, OBSTACLE_COLOR, pygame.Rect(px+20, bar_y, pw-40, 12), border_radius=6)
        pygame.draw.rect(screen, ROBOT_COLOR,
                         pygame.Rect(px+20, bar_y, int((pw-40)*self.progress/100), 12), border_radius=6)
        screen.blit(font_small.render(f"{self.progress}%", True, TEXT_DIM),
                    (px + 20, bar_y + 16))



# MATPLOTLIB REPORT

def build_report_surface(ga, cmp=None):
    if ga.generation < 2:
        return None

    has_cmp = cmp is not None and cmp.done and len(cmp.results) == 3
    rows    = 3 if has_cmp else 2
    fig, axes = plt.subplots(rows, 2, figsize=(11, rows * 3))
    fig.patch.set_facecolor('#0a0e18')

    for ax in axes.flat:
        ax.set_facecolor('#0d1220')
        ax.tick_params(colors='#8899aa', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#223344')

    gens = list(range(ga.generation))

    # --- 1. Fitness over generations ---
    ax = axes[0, 0]
    ax.plot(gens, ga.best_history, color='#f59e0b', linewidth=2, label='Best')
    ax.plot(gens, ga.avg_history,  color='#4a9eff', linewidth=1.2,
            linestyle='--', label='Average')
    ax.fill_between(gens, ga.avg_history, ga.best_history,
                    alpha=0.12, color='#f59e0b')
    ax.set_title('Fitness over Generations', color='#ccd6e0', fontsize=10)
    ax.set_xlabel('Generation', color='#8899aa', fontsize=8)
    ax.set_ylabel('Fitness',    color='#8899aa', fontsize=8)
    ax.legend(fontsize=8, facecolor='#0d1220', labelcolor='#ccd6e0', framealpha=0.6)
    ax.grid(True, color='#1a2535', linewidth=0.5)

    # --- 2. Survival rate ---
    ax = axes[0, 1]
    ax.bar(gens, ga.alive_history, color='#27c99a', alpha=0.75, width=0.8)
    ax.axhline(y=50, color='#f59e0b', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_title('Survival Rate per Generation (%)', color='#ccd6e0', fontsize=10)
    ax.set_xlabel('Generation',       color='#8899aa', fontsize=8)
    ax.set_ylabel('Alive at end (%)', color='#8899aa', fontsize=8)
    ax.set_ylim(0, 105)
    ax.grid(True, color='#1a2535', linewidth=0.5, axis='y')

    # --- 3. Gene evolution ---
    ax = axes[1, 0]
    if ga.best_dna_history:
        speeds  = [d.speed             for d in ga.best_dna_history]
        turns   = [d.turn_rate * 10    for d in ga.best_dna_history]
        sensors = [d.sensor_range / 40  for d in ga.best_dna_history]
        aggs    = [d.aggression         for d in ga.best_dna_history]
        ax.plot(gens, speeds,  color='#4a9eff', linewidth=1.5, label='Speed')
        ax.plot(gens, turns,   color='#27c99a', linewidth=1.5, label='Turn×10')
        ax.plot(gens, sensors, color='#f59e0b', linewidth=1.5, label='Sensor÷40')
        ax.plot(gens, aggs,    color='#e05555', linewidth=1.5, label='Aggression')
    ax.set_title('Best Robot Gene Evolution', color='#ccd6e0', fontsize=10)
    ax.set_xlabel('Generation', color='#8899aa', fontsize=8)
    ax.legend(fontsize=7, facecolor='#0d1220', labelcolor='#ccd6e0',
              framealpha=0.6, ncol=2)
    ax.grid(True, color='#1a2535', linewidth=0.5)

    # --- 4. All-time best DNA bar chart ---
    ax = axes[1, 1]
    if ga.all_time_best_dna:
        d      = ga.all_time_best_dna
        labels = ['Speed', 'Turn\n×10', 'Sensor\n÷40', 'Aggression']
        values = [
            (d.speed        - DNA.SPEED_MIN)  / (DNA.SPEED_MAX  - DNA.SPEED_MIN),
            (d.turn_rate    - DNA.TURN_MIN)   / (DNA.TURN_MAX   - DNA.TURN_MIN),
            (d.sensor_range - DNA.SENSOR_MIN) / (DNA.SENSOR_MAX - DNA.SENSOR_MIN),
            (d.aggression   - DNA.AGG_MIN)    / (DNA.AGG_MAX    - DNA.AGG_MIN),
        ]
        bars = ax.bar(labels, values,
                      color=['#4a9eff', '#27c99a', '#f59e0b', '#e05555'], alpha=0.85)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{val:.2f}', ha='center', va='bottom',
                    color='#ccd6e0', fontsize=8)
        ax.set_ylim(0, 1.2)
        ax.set_title(
            f'All-Time Best DNA  (fitness={ga.all_time_best_fitness:.1f})',
            color='#ccd6e0', fontsize=10)
        ax.set_ylabel('Normalised value', color='#8899aa', fontsize=8)
        ax.grid(True, color='#1a2535', linewidth=0.5, axis='y')

    # --- 5 & 6. Comparison (only if data exists) ---
    if has_cmp:
        colors = ComparisonMode.COLORS
        labels = ComparisonMode.LABELS

        ax = axes[2, 0]
        for (best_h, _), col, lbl in zip(cmp.results, colors, labels):
            g = list(range(len(best_h)))
            ax.plot(g, best_h, color=col, linewidth=2, label=lbl)
        ax.set_title('Mutation Rate Comparison — Best Fitness', color='#ccd6e0', fontsize=10)
        ax.set_xlabel('Generation',   color='#8899aa', fontsize=8)
        ax.set_ylabel('Best Fitness', color='#8899aa', fontsize=8)
        ax.legend(fontsize=8, facecolor='#0d1220', labelcolor='#ccd6e0', framealpha=0.6)
        ax.grid(True, color='#1a2535', linewidth=0.5)

        ax = axes[2, 1]
        final_bests = [h[0][-1] if h[0] else 0 for h in cmp.results]
        bars = ax.bar(labels, final_bests, color=colors, alpha=0.85)
        for bar, val in zip(bars, final_bests):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}', ha='center', va='bottom',
                    color='#ccd6e0', fontsize=9)
        ax.set_title(f'Final Best Fitness after {cmp.num_gens} Generations',
                     color='#ccd6e0', fontsize=10)
        ax.set_ylabel('Best Fitness', color='#8899aa', fontsize=8)
        ax.grid(True, color='#1a2535', linewidth=0.5, axis='y')

    fig.suptitle(
        f'Evolutionary Robots — {ga.generation} Generations  |  '
        f'Pop={ga.pop_size}  Mut={ga.mut_rate:.2f}  Elite={ga.elite_count}',
        color='#ccd6e0', fontsize=11, fontweight='bold')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return pygame.image.load(buf, 'report.png')