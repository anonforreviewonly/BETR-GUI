"""Unit test for gp_instance.py module."""

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

import random
import numpy as np
from behaviors import behavior_list_test_settings
from behaviors import behavior_lists
from behaviors.common_behaviors import ParameterizedNode, NodeParameter, ParameterTypes
from behaviors.behavior_tree import BT
import bt_learning.gp.genetic_programming as gp
from bt_learning.gp.gp_instance import GPInstance

from bt_learning.gp.test.test_gp_parallel import TestEnvironment


behavior_lists = behavior_lists.BehaviorLists(
    condition_nodes=behavior_list_test_settings.get_condition_nodes(),
    action_nodes=behavior_list_test_settings.get_action_nodes())

par1 = NodeParameter([], min=1, max=5, step=1, data_type=ParameterTypes.INTEGER, value=1)
par2 = NodeParameter([], min=1, max=5, step=1, data_type=ParameterTypes.INTEGER, value=2)

b = ParameterizedNode('b', None, [], True)
c = ParameterizedNode('c', None, [], True)
ab = ParameterizedNode('ab', None, {"value1": par1, "value2": par2, "require_execution": False}, False)
ac = ParameterizedNode('ac', None, {"value1": par1, "value2": par2, "require_execution": False}, False)
ad = ParameterizedNode('ad', None, {"value1": par1, "value2": par1, "require_execution": False}, False)
ae = ParameterizedNode('ae', None, {"value1": par1, "value2": par1, "require_execution": False}, False)
af = ParameterizedNode('af', None, {"require_execution": False}, False)

def test_run():
    """
    Test run function.

    The GPInstance.run function should produce identical result to the gp one.
    """
    gp_par = gp.GpParameters()
    gp_par.behavior_lists = behavior_lists
    gp_par.ind_start_length = 3
    gp_par.n_population = 32
    gp_par.f_crossover = 0.2
    gp_par.n_offspring_crossover = 4
    gp_par.f_mutation = 0.8
    gp_par.n_offspring_mutation = 4
    gp_par.f_elites = 0.1
    gp_par.f_parents = 0.1
    gp_par.plot = False
    gp_par.n_generations = 12
    gp_par.verbose = False
    gp_par.fig_best = False
    seed = 1337
    t_environment = TestEnvironment()
    gp.set_seeds(seed)
    population, fitness, _, _ = gp.run(t_environment, gp_par)
    assert (max(fitness)) == 3.4

    gp.set_seeds(seed)
    gp_instance = GPInstance('1', t_environment, 3, gp_par)
    while gp_instance.is_runnable():
        gp_instance.step_gp()
    population2, fitness2, _, _ = gp_instance.get_final_info()
    assert population2 == population
    assert fitness2 == fitness
    assert (max(fitness2)) == 3.4

def test_exchange():
    """
    Test exchanging migrants function.

    Try to swap two island completely.
    """
    gp_par = gp.GpParameters()
    gp_par.use_tracker = False
    gp_par.behavior_lists = behavior_lists
    gp_par.ind_start_length = 3
    gp_par.n_population = 32
    gp_par.f_crossover = 0.2
    gp_par.n_offspring_crossover = 4
    gp_par.f_mutation = 0.8
    gp_par.n_offspring_mutation = 4
    gp_par.f_elites = 0.1
    gp_par.f_parents = 0.1
    gp_par.plot = False
    gp_par.n_generations = 12
    gp_par.verbose = False
    gp_par.fig_best = False

    seed = 1337
    t_environment = TestEnvironment()
    random.seed(seed)
    np.random.seed(seed)
    gp_instance1 = GPInstance('1', t_environment, 3, gp_par)
    gp_instance1.step_gp()
    gp_instance2 = GPInstance('2', t_environment, 3, gp_par)
    gp_instance2.step_gp()
    population1, fitness1 = gp_instance1.get_current_population()
    population2, fitness2 = gp_instance2.get_current_population()

    migrants1, m_fitness1 = gp_instance1.get_migrants(gp_par.n_population)
    migrants2, m_fitness2 = gp_instance2.get_migrants(gp_par.n_population)

    gp_instance2.receive_migrants(migrants1, m_fitness1)
    gp_instance1.receive_migrants(migrants2, m_fitness2)

    gp_instance1.merge_migrants()
    gp_instance2.merge_migrants()

    population1_swapped, fitness1_swapped = gp_instance1.get_current_population()
    population2_swapped, fitness2_swapped = gp_instance2.get_current_population()

    def sorting_key(x):
        return x[1]

    p1 = list(zip(population1, fitness1))
    p2 = list(zip(population2, fitness2))

    p1_swapped = list(zip(population1_swapped, fitness1_swapped))
    p2_swapped = list(zip(population2_swapped, fitness2_swapped))
    p1.sort(key=sorting_key)
    p2.sort(key=sorting_key)
    p1_swapped.sort(key=sorting_key)
    p2_swapped.sort(key=sorting_key)
    assert p1 == p2_swapped
    assert p2 == p1_swapped


def test_get_genotype_diversity():
    """ Test get_genotype_diversity function """
    gp_par = gp.GpParameters()
    gp_par.use_tracker = False
    gp_par.behavior_lists = behavior_lists
    gp_par.n_population = 3

    t_environment = TestEnvironment()

    gp_instance = GPInstance('1', t_environment, 3, gp_par)

    bt1 = ['s(', ab, 'f(', ab, ab, ')', ab, ')']
    bt2 = ['s(', ab, 'f(', ab, ab, ')', 's(', ab, ab, ')', ')']
    bt3 = ['s(', ab, 'f(', ab, ab, ')', 's(', ab, ab, ')', ')']

    gp_instance.receive_migrants([bt1, bt2, bt3], [0, 0, 0])
    gp_instance.merge_migrants()

    ed1, ed2, num_isomorphs_tuple = gp_instance.get_genotype_diversity()

    assert ed1 == (0 + 3/8 + 3/8) / 3
    assert ed2 == (0 + 2 * 0.5 * (1 + 0.5 * 2)) / 3
    assert num_isomorphs_tuple == 2


def test_get_entropy_diversity():
    """ test get_entropy_diversity function"""
    gp_par = gp.GpParameters()
    gp_par.use_tracker = False
    gp_par.behavior_lists = behavior_lists
    gp_par.n_population = 10

    t_environment = TestEnvironment()

    gp_instance = GPInstance('1', t_environment, 3, gp_par)

    bt1 = ['s(', ab, ')']

    # zero entropy, all individuals have the same fitness score
    gp_instance.receive_migrants(
        [bt1] * gp_par.n_population, [0] * gp_par.n_population)
    gp_instance.merge_migrants()
    entropy1 = gp_instance.get_entropy_diversity()
    assert entropy1 == 0.0

    # p = 0.1 for all individuals
    gp_instance.receive_migrants(
        [bt1] * gp_par.n_population, list(range(gp_par.n_population)))
    gp_instance.merge_migrants()
    entropy1 = gp_instance.get_entropy_diversity()
    assert entropy1 == 10 * (- 0.1 * np.log(0.1))


def test_update_selection_pressure_ed2():
    """ Test update_selection_pressure with ed2 """
    gp_par = gp.GpParameters()
    gp_par.use_tracker = False
    gp_par.behavior_lists = behavior_lists
    gp_par.n_population = 3

    t_environment = TestEnvironment()

    gp_instance = GPInstance('1', t_environment, 3, gp_par)

    bt1 = ['s(', ab, 'f(', ab, ab, ')', ab, ')']
    bt2 = ['s(', ab, 'f(', ab, ab, ')', 's(', ab, ab, ')', ')']
    bt3 = ['s(', ab, 'f(', ab, ab, ')', 's(', ab, ab, ')', ')']

    gp_instance.receive_migrants([bt1, bt2, bt3], [0, 0, 0])
    gp_instance.merge_migrants()
    # the default value for selection pressure
    assert gp_instance.selection_pressure == 0.9

    ed2 = 0.2
    gp_instance.update_selection_pressure((0, ed2, 0))
    assert gp_instance.max_diversity == ed2
    assert gp_instance.min_diversity == ed2
    assert gp_instance.params.selection_pressure_diversity == 'ed2'
    assert gp_instance.selection_pressure == 0

    gp_instance.update_selection_pressure((0, 1, 0))
    assert gp_instance.max_diversity == 1
    assert gp_instance.min_diversity == ed2
    assert abs(gp_instance.selection_pressure - 1) < 0.001

    gp_instance.update_selection_pressure((0, (ed2 + 1)/2, 0))
    assert gp_instance.max_diversity == 1
    assert gp_instance.min_diversity == ed2
    assert abs(gp_instance.selection_pressure - 0.5) < 0.001


def test_update_selection_pressure_ed1():
    """ Test update_selection_pressure with ed1 """
    gp_par = gp.GpParameters()
    gp_par.use_tracker = False
    gp_par.selection_pressure_diversity = 'ed1'
    gp_par.behavior_lists = behavior_lists
    gp_par.n_population = 3

    t_environment = TestEnvironment()

    gp_instance = GPInstance('1', t_environment, 3, gp_par)

    bt1 = ['s(', ab, 'f(', ab, ab, ')', ab, ')']
    bt2 = ['s(', ab, 'f(', ab, ab, ')', 's(', ab, ab, ')', ')']
    bt3 = ['s(', ab, 'f(', ab, ab, ')', 's(', ab, ab, ')', ')']

    gp_instance.receive_migrants([bt1, bt2, bt3], [0, 0, 0])
    gp_instance.merge_migrants()

    ed1 = 0.2
    gp_instance.update_selection_pressure((ed1, 0, 0))
    assert gp_instance.max_diversity == ed1
    assert gp_instance.min_diversity == ed1
    assert gp_instance.params.selection_pressure_diversity == 'ed1'
    assert gp_instance.selection_pressure == 0

    gp_instance.update_selection_pressure((1, 0, 0))
    assert gp_instance.max_diversity == 1
    assert gp_instance.min_diversity == ed1
    assert abs(gp_instance.selection_pressure - 1) < 0.001

    gp_instance.update_selection_pressure(((ed1 + 1)/2, 0, 0))
    assert gp_instance.max_diversity == 1
    assert gp_instance.min_diversity == ed1
    assert abs(gp_instance.selection_pressure - 0.5) < 0.001


def test_hotstart():
    """Test run function."""
    gp_par = gp.GpParameters()
    gp_par.behavior_lists = behavior_lists
    gp_par.ind_start_length = 3
    gp_par.n_population = 8
    gp_par.f_crossover = 0.2
    gp_par.n_offspring_crossover = 4
    gp_par.f_mutation = 0.8
    gp_par.n_offspring_mutation = 4
    gp_par.f_elites = 0.1
    gp_par.f_parents = 0.1
    gp_par.plot = False
    gp_par.n_generations = 5
    gp_par.verbose = False
    gp_par.fig_best = False


    seed = 1337
    t_environment = TestEnvironment()
    gp.set_seeds(seed)
    random.seed(seed)
    np.random.seed(seed)
    gp_instance = GPInstance('1', t_environment, 3, gp_par)
    while gp_instance.is_runnable():
        gp_instance.step_gp()
    _ = gp_instance.get_final_info()

    gp_instance2 = GPInstance('1', t_environment, 3, gp_par, hotstart=True)
    assert gp_instance.population == gp_instance2.population
    assert gp_instance.fitness == gp_instance2.fitness
    assert gp_instance.num_gen == gp_instance2.num_gen
    assert gp_instance.my_path == gp_instance2.my_path
    assert gp_instance.best_fitness == gp_instance2.best_fitness

def test_set_locked_mask():
    """Test set_baseline with locked mask function."""
    gp_par = gp.GpParameters()
    gp_par.behavior_lists = behavior_lists
    gp_par.ind_start_length = 3
    gp_par.n_population = 8
    gp_par.f_crossover = 0.2
    gp_par.n_offspring_crossover = 2
    gp_par.f_mutation = 0.8
    gp_par.n_offspring_mutation = 2
    gp_par.f_elites = 0.1
    gp_par.f_parents = 0.1
    gp_par.plot = False
    gp_par.n_generations = 5
    gp_par.verbose = False
    gp_par.fig_best = False

    t_environment = TestEnvironment()
    gp_instance = GPInstance('1', t_environment, 3, gp_par)
    gp_instance.step_gp()

    locked_genome = ['f(', b, ab, ')']
    locked_mask =  [True, True, True, False]
    gp_instance.set_baseline(locked_genome, locked_mask)
    gp_instance.step_gp()
    assert len(gp_instance.population) == gp_par.n_population
    assert len(gp_instance.fitness) == gp_par.n_population

def test_locked_reordering():
    """ Test that reordering of works as expected with locked genome """
    gp_par = gp.GpParameters()
    gp_par.behavior_lists = behavior_lists
    gp_par.ind_start_length = 3
    gp_par.n_population = 20
    gp_par.f_crossover = 0.1
    gp_par.n_offspring_crossover = 2
    gp_par.f_mutation = 0.4
    gp_par.n_offspring_mutation = 2
    gp_par.f_elites = 0.1
    gp_par.f_parents = 0.1
    gp_par.plot = False
    gp_par.n_generations = 5
    gp_par.verbose = False
    gp_par.fig_best = False

    t_environment = TestEnvironment()
    gp_instance = GPInstance('1', t_environment, 1, gp_par)
    gp_instance.step_gp()

    locked_genome = ['f(', ae, ad, c, b, ')']
    locked_mask =  [True, True, True, True, True, True]
    gp_instance.set_baseline(locked_genome, locked_mask)
    baseline_fitness = t_environment.get_fitness(locked_genome)
    for _ in range(5):
        gp_instance.step_gp()
    assert len(gp_instance.population) == gp_par.n_population
    assert len(gp_instance.fitness) == gp_par.n_population
    for individual in gp_instance.population:
        bt = BT(individual, behavior_lists)
        assert bt.is_locked_tree_part_of_tree(locked_genome, locked_mask)

    assert max(gp_instance.fitness) > baseline_fitness, "Some individual should be better than the locked genome fitness"

def test_set_fixed_structure():
    """ Test set_fixed_structure function """
    gp_par = gp.GpParameters()
    gp_par.behavior_lists = behavior_lists
    gp_par.ind_start_length = 3
    gp_par.n_population = 8
    gp_par.f_crossover = 0.2
    gp_par.n_offspring_crossover = 2
    gp_par.f_mutation = 0.8
    gp_par.n_offspring_mutation = 2
    gp_par.f_elites = 0.1
    gp_par.f_parents = 0.1
    gp_par.plot = False
    gp_par.n_generations = 5
    gp_par.verbose = False
    gp_par.fig_best = False

    t_environment = TestEnvironment()
    gp_instance = GPInstance('1', t_environment, 3, gp_par)
    gp_instance.step_gp()

    baseline = ['f(', b, c, 's(', ab, ac, ')', ad, ')']
    gp_instance.set_baseline(baseline)
    gp_instance.set_fixed_structure(True)
    for _ in range(5):
        gp_instance.step_gp()
    assert len(gp_instance.population) == gp_par.n_population
    assert len(gp_instance.fitness) == gp_par.n_population
    assert baseline in gp_instance.population
    bt = BT(baseline, behavior_lists)
    for ind in gp_instance.population:
        assert bt.same_structure(ind, categorical_value_diff_ok=True)

def test_set_baseline():
    """Test set_baseline function."""
    gp_par = gp.GpParameters()
    gp_par.behavior_lists = behavior_lists
    gp_par.ind_start_length = 3
    gp_par.n_population = 8
    gp_par.f_crossover = 0.2
    gp_par.n_offspring_crossover = 2
    gp_par.f_mutation = 0.8
    gp_par.n_offspring_mutation = 2
    gp_par.f_elites = 0.1
    gp_par.f_parents = 0.1
    gp_par.plot = False
    gp_par.n_generations = 5
    gp_par.verbose = False
    gp_par.fig_best = False

    t_environment = TestEnvironment()
    gp_instance = GPInstance('1', t_environment, 3, gp_par)
    gp_instance.step_gp()

    baseline = ['f(', b, c, ad, ')']
    gp_instance.set_baseline(baseline)
    gp_instance.step_gp()
    assert len(gp_instance.population) == gp_par.n_population
    assert len(gp_instance.fitness) == gp_par.n_population
    assert baseline in gp_instance.population



if __name__ == '__main__':
    # import cProfile
    # from pstats import Stats

    # pr = cProfile.Profile()
    # pr.enable()

    test_run()

    # pr.disable()
    # stats = Stats(pr)
    # stats.sort_stats('tottime').print_stats(25)
