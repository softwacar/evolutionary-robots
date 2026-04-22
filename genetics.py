import random
from settings import (POPULATION, ELITE_COUNT, MUTATION_RATE, GEN_TICKS)



# DNA

class DNA:
    SPEED_MIN,  SPEED_MAX  = 0.5,  3.0
    TURN_MIN,   TURN_MAX   = 0.03, 0.15
    SENSOR_MIN, SENSOR_MAX = 30,   120
    AGG_MIN,    AGG_MAX    = 0.0,  1.0

    def __init__(self, speed=None, turn_rate=None,
                 sensor_range=None, aggression=None):
        self.speed        = speed        if speed        is not None else random.uniform(self.SPEED_MIN,  self.SPEED_MAX)
        self.turn_rate    = turn_rate    if turn_rate    is not None else random.uniform(self.TURN_MIN,   0.06)
        self.sensor_range = sensor_range if sensor_range is not None else random.uniform(self.SENSOR_MIN, 80)
        self.aggression   = aggression   if aggression   is not None else random.uniform(self.AGG_MIN,    0.5)

    @staticmethod
    def crossover(a, b):
        genes = ['speed', 'turn_rate', 'sensor_range', 'aggression']
        point = random.randint(1, len(genes) - 1)
        child = DNA.__new__(DNA)
        for i, g in enumerate(genes):
            setattr(child, g, getattr(a, g) if i < point else getattr(b, g))
        return child

    def mutate(self, rate=None):
        rate = rate if rate is not None else MUTATION_RATE
        if random.random() < rate:
            self.speed = max(self.SPEED_MIN, min(self.SPEED_MAX,
                             self.speed + random.uniform(-0.5, 0.5)))
        if random.random() < rate:
            self.turn_rate = max(self.TURN_MIN, min(self.TURN_MAX,
                                 self.turn_rate + random.uniform(-0.02, 0.02)))
        if random.random() < rate:
            self.sensor_range = max(self.SENSOR_MIN, min(self.SENSOR_MAX,
                                    self.sensor_range + random.uniform(-15, 15)))
        if random.random() < rate:
            self.aggression = max(self.AGG_MIN, min(self.AGG_MAX,
                                  self.aggression + random.uniform(-0.2, 0.2)))

    def clone(self):
        return DNA(self.speed, self.turn_rate, self.sensor_range, self.aggression)



# GENETIC ALGORITHM

class GeneticAlgorithm:
    def __init__(self, pop=None, elite=None, mut=None, ticks=None):
        self.pop_size     = pop   or POPULATION
        self.elite_count  = elite or ELITE_COUNT
        self.mut_rate     = mut   if mut is not None else MUTATION_RATE
        self.gen_ticks    = ticks or GEN_TICKS
        self.generation   = 0
        self.best_history = []
        self.avg_history  = []
        self.alive_history= []
        self.best_dna_history = []
        self.all_time_best_fitness = 0
        self.all_time_best_dna     = None

    def evolve(self, robots):
        robots.sort(key=lambda r: r.fitness, reverse=True)
        fits     = [r.fitness for r in robots]
        best_fit = fits[0]
        avg_fit  = sum(fits) / len(fits)
        alive_r  = sum(1 for r in robots if r.alive) / len(robots)

        self.best_history.append(round(best_fit, 2))
        self.avg_history.append(round(avg_fit,  2))
        self.alive_history.append(round(alive_r * 100, 1))
        self.best_dna_history.append(robots[0].dna.clone())

        if best_fit > self.all_time_best_fitness:
            self.all_time_best_fitness = best_fit
            self.all_time_best_dna     = robots[0].dna.clone()

        self.generation += 1

        elite_dna = [robots[i].dna.clone() for i in range(self.elite_count)]
        new_dna   = list(elite_dna)
        while len(new_dna) < self.pop_size:
            child = DNA.crossover(random.choice(elite_dna), random.choice(elite_dna))
            child.mutate(self.mut_rate)
            new_dna.append(child)
        return new_dna, best_fit, avg_fit