# Evolutionary Optimization of Autonomous Robot Behaviors Using Genetic Algorithms

A 2D simulation where autonomous robots evolve over generations to efficiently collect energy while avoiding obstacles. Built with Python, Pygame, and Matplotlib.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green) ![Matplotlib](https://img.shields.io/badge/Matplotlib-3.10-orange)

---

## Overview

This project demonstrates how genetic algorithms can optimize autonomous agent behavior without any explicit programming of strategies. Robots start with random traits and evolve over successive generations — only the best performers survive and reproduce.

Each robot has a DNA encoding four genes:

| Gene | Description | Range |
|------|-------------|-------|
| Speed | Movement speed per tick | 0.5 – 3.0 |
| Turn Rate | Maximum turning angle per tick | 0.03 – 0.15 rad |
| Sensor Range | How far the robot can detect objects | 30 – 120 px |
| Aggression | How strongly it steers toward food | 0.0 – 1.0 |

---

![Demo](demo.gif)

## How It Works

### Simulation Loop
1. A population of robots (default: 40) is placed in a 2D environment
2. Each robot senses nearby energy sources and obstacles using its sensor range
3. Robots steer toward food and away from walls based on their DNA
4. After a fixed number of ticks (default: 400), the generation ends

### Fitness Function
Each robot accumulates a fitness score throughout its lifetime:

| Event | Score |
|-------|-------|
| Collecting an energy source | +10 |
| Surviving each tick | +0.01 |
| Colliding with an obstacle | −2 |
| Dying from energy depletion | −5 |

### Genetic Algorithm
At the end of each generation:
- Robots are ranked by fitness
- Top 6 elites are preserved unchanged (elitism)
- New population is created via **single-point crossover** between elite parents
- Offspring are subject to **random mutation** (default rate: 15%)

Over generations, robots develop increasingly efficient foraging behaviors.

---

## Project Structure

```
├── main.py        # Game loop, rendering, keyboard input
├── settings.py    # All constants, colors, and default parameters
├── genetics.py    # DNA class and GeneticAlgorithm class
├── entities.py    # Robot, Obstacle, Energy classes and spawn functions
└── report.py      # Matplotlib report, ParameterPanel, ComparisonMode
```

---

## Requirements

- Python 3.11
- Pygame 2.6.1
- Matplotlib 3.10
- NumPy 2.4

Install all dependencies:

```bash
pip install pygame matplotlib numpy
```

---

## Running the Simulation

```bash
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| `SPACE` | Pause / Resume |
| `→` | Skip to next generation |
| `↑` / `↓` | Increase / Decrease speed (1x – 10x) |
| `P` | Open parameter settings panel |
| `C` | Run mutation rate comparison (3 silent simulations) |
| `G` | Toggle fitness report (Matplotlib graphs) |
| `R` | Reset simulation |
| `ESC` | Quit |

---

## Features

### Real-Time Simulation
- Robots rendered as directional arrows with energy bars
- Elite robots highlighted in amber with visible sensor range
- Movement trails showing recent path
- Live fitness graph on the right panel

### Parameter Panel (`P`)
Adjust simulation parameters on the fly without editing code:
- Population size
- Mutation rate
- Elite count
- Generation duration
- Energy and obstacle count

### Mutation Rate Comparison (`C`)
Runs three silent simulations with mutation rates of **5%**, **15%**, and **40%** and records fitness history for each. Results appear in the report.

### Fitness Report (`G`)
A full Matplotlib report rendered inside the simulation window:

1. **Fitness over Generations** — best and average fitness curves
2. **Survival Rate** — percentage of robots alive at end of each generation
3. **Gene Evolution** — how the best robot's traits change over time
4. **All-Time Best DNA** — normalised gene values of the highest-scoring robot
5. **Mutation Rate Comparison** — side-by-side fitness curves (if `C` was run)
6. **Final Fitness Bar Chart** — comparing end results across mutation rates

---

## Example Results

After ~20 generations, robots typically show:
- Increased tendency to seek out energy sources
- Improved obstacle avoidance
- Convergence toward a balanced speed/sensor trade-off

High mutation rates (40%) introduce too much noise and slow convergence. Low mutation rates (5%) converge faster but may get stuck in local optima. The default 15% provides the best balance.

---

## Technical Details

- **Crossover:** Single-point crossover — genes before the cut point come from parent A, after from parent B
- **Mutation:** Each gene has an independent probability of being nudged by a small random value
- **Elitism:** Top N robots are copied unchanged to preserve best solutions
- **Sensor model:** Robots detect the nearest food/obstacle within their sensor range and steer accordingly

---

IUS AI PROJECT 1
