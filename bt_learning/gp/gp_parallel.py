"""Parallelize the Genetic Programming algorithm computation."""

# Copyright (c) 2025, ABB
# All rights reserved.
#
# Redistribution and use in source and binary forms, with
# or without modification, are permitted provided that
# the following conditions are met:
#
#   * Redistributions of source code must retain the
#     above copyright notice, this list of conditions
#     and the following disclaimer.
#   * Redistributions in binary form must reproduce the
#     above copyright notice, this list of conditions
#     and the following disclaimer in the documentation
#     and/or other materials provided with the
#     distribution.
#   * Neither the name of ABB nor the names of its
#     contributors may be used to endorse or promote
#     products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import functools
import random
from statistics import mean
from typing import Any, List, Tuple
from pathos.multiprocessing import ProcessingPool as Pool

import bt_learning.gp.genetic_programming as gp
from bt_learning.gp.hash_table import HashTable

def get_fitness_simple(
    individual: Any,
    environment: Any,
    min_episodes: int = 1
) -> List:
    """
    Return the fitness value.

    This version excludes rerun and hash table for easier parallelism.
    """
    values = []
    for i in range(min_episodes):
        values.append(environment.get_fitness(individual, i))
    return values


def get_fitness_min_population(
    min_population: list,
    population: list,
    environment: Any,
    min_episodes: int
) -> List[float]:
    """Get the fitness of a reduced population."""
    fitness = []
    for individual in min_population:
        fitness.append(get_fitness_simple(population[individual], environment, min_episodes))
    return fitness

def find_individuals_to_eval(
    population: Any,
    hash_table: HashTable,
    environment: Any,
    rerun_fitness: int
) -> Tuple[List[float], List[int]]:
    """Get the indexes of the individual to re-evaluate."""
    fitness_list = []
    individuals_to_eval = []
    # find the individuals to be evaluated
    for idx, individual in enumerate(population):
        values = hash_table.find(individual)
        if values is None:
            fitness_list.append(None)
            individuals_to_eval.append(idx)
        elif rerun_fitness == 2 or\
                (rerun_fitness == 1 and random.random() < gp.rerun_probability(len(values[0]))):
            fitness = environment.get_fitness(individual, len(values[0]))
            hash_table.insert(individual, fitness)
            fitness_list.append(mean(values[0]))
        else:
            fitness_list.append(mean(values[0]))
    return fitness_list, individuals_to_eval

def parallel_evaluate(
    pool: Any,
    n_processes: int,
    eval_func: Any,
    fitness_list: List[float],
    eval_list: list
) -> List[float]:
    """Spread the computation in parallel processes."""
    part_size = len(eval_list) // n_processes
    if len(eval_list) % n_processes != 0:
        part_size += 1
    mp_input = []
    # prepare input for each process
    for core_id in range(n_processes):
        mp_input.append(eval_list[core_id * part_size:(core_id + 1)*part_size])

    temp_list = pool.map(eval_func, mp_input)
    # retrieve fitness scores from the processes
    write_back_count = 0
    for core_id in range(n_processes):
        for p_idx in range(len(temp_list[core_id])):
            fitness_list[eval_list[write_back_count]] = temp_list[core_id][p_idx]
            write_back_count += 1
    assert write_back_count == len(eval_list)
    return fitness_list

def evaluate(
    population: list,
    hash_table: HashTable,
    environment: Any,
    pool: Any = None,
    n_processes: int = 1,
    rerun_fitness: int = 0,
    min_episodes: int = 1
) -> List[float]:
    """Evaluate the population using the environment."""
    fitness_list, individuals_to_eval = find_individuals_to_eval(
        population, hash_table, environment, rerun_fitness)

    if environment.use_parallel_agents():
        fitness_list = environment.get_fitnesses(population, fitness_list, individuals_to_eval, min_episodes)
    else:
        eval_func = functools.partial(
            get_fitness_min_population,
            population=population,
            environment=environment,
            min_episodes=min_episodes
        )
        if pool is not None:
            fitness_list = parallel_evaluate(pool, n_processes, eval_func, fitness_list, individuals_to_eval)
        elif n_processes > 1:
            with Pool(processes=n_processes) as pool:
                fitness_list = parallel_evaluate(pool, n_processes, eval_func, fitness_list, individuals_to_eval)
        else:
            for eval_idx in individuals_to_eval:
                fitness_list[eval_idx] = get_fitness_simple(population[eval_idx], environment, min_episodes)

    if not environment.get_paused():
        # Add to hash tables once all rollouts are done
        for eval_idx in individuals_to_eval:
            values = fitness_list[eval_idx]
            if isinstance(values, list):
                mean_value = 0
                for value in values:
                    hash_table.insert(population[eval_idx], value)
                    if isinstance(value, tuple):
                        mean_value += value[0]
                    else:
                        mean_value += value
                fitness_list[eval_idx] = mean_value / len(values)
            else:
                hash_table.insert(population[eval_idx], values)
                if isinstance(values, tuple):
                    fitness_list[eval_idx] = values[0]

    return fitness_list
