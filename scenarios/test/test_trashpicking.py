"""Unit test for testing trashpicking scenario."""

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

import bt_learning.gp.genetic_programming as gp
from bt_learning.gp.gp_instance import GPInstance
from bt_learning.bo import bo
from scenarios import behaviors
from scenarios.trashpicking import get_environment
from behaviors.common_behaviors import Goal
from planner import planner

goals = []
goals.append(Goal(behaviors.InContainer, {"target_object": '"paper"',
                                            "relative_object": '"green bin"'}))
goals.append(Goal(behaviors.InContainer, {"target_object": '"banana"',
                                        "relative_object": '"blue bin"'}))
goals.append(Goal(behaviors.InContainer, {"target_object": '"can"',
                                        "relative_object": '"yellow bin"'}))

def test_manual_tree():
    """ Creates a whole manually constructed Behavior Tree to solve the trashpicking scenario in simulation"""
    environment = get_environment(planner_environment=False, n_agents=1)

    green_bin_subtree = ['f(', '"paper" in  "green bin"?',
                              's(', 'f(', 'grasped "paper"?', 
                                          's(', 'move to "paper" (-0.3, 0.3) 0.0!',
                                                'grasp "paper"!', ')', ')', 
                                    'move to "green bin" (0.6, 0.0) 3.14!',
                                    'place "paper" in  "green bin"!', ')', ')']
    yellow_bin_subtree =  ['f(', '"can" in  "yellow bin"?',
                              's(', 'f(', 'grasped "can"?',
                                    's(', 'move to "can" (-0.2, 0.4) 1.57!',
                                                'grasp "can"!', ')', ')',
                                          'move to "yellow bin" (0.4, -0.4) -1.57!',
                                          'place "can" in  "yellow bin"!', ')', ')']
    blue_bin_subtree = ['f(', '"banana" in  "blue bin"?',
                              's(', 'f(', 'grasped "banana"?',
                                          's(', 'move to "banana" (-0.2, -0.4) -1.57!',
                                                'grasp "banana"!', ')', ')',
                                                'move to "blue bin" (0.4, 0.4) 1.57!',
                                                'place "banana" in  "blue bin"!', ')', ')']
    blue_bin_short_path_subtree = ['f(', '"banana" in  "blue bin"?',
                            's(', 'f(', 'grasped "banana"?',
                                        's(', 'move to "banana" (-0.2, -0.8) -1.57!',
                                            'grasp "banana"!', ')', ')',
                                            'move to "blue bin" (0.6, 0.6) 3.14!',
                                            'place "banana" in  "blue bin"!', ')', ')']

    ybg = ['s(']
    ybg.extend(yellow_bin_subtree)
    ybg.extend(blue_bin_subtree)
    ybg.extend(green_bin_subtree)
    ybg.extend([')'])

    ybg_short_path = ['s(']
    ybg_short_path.extend(yellow_bin_subtree)
    ybg_short_path.extend(blue_bin_short_path_subtree)
    ybg_short_path.extend(green_bin_subtree)
    ybg_short_path.extend([')'])

    ygb = ['s(']
    ygb.extend(yellow_bin_subtree)
    ygb.extend(green_bin_subtree)
    ygb.extend(blue_bin_subtree)
    ygb.extend([')'])

    byg = ['s(']
    byg.extend(blue_bin_subtree)
    byg.extend(yellow_bin_subtree)
    byg.extend(green_bin_subtree)
    byg.extend([')'])

    bgy = ['s(']
    bgy.extend(blue_bin_subtree)
    bgy.extend(green_bin_subtree)
    bgy.extend(yellow_bin_subtree)
    bgy.extend([')'])

    gyb = ['s(']
    gyb.extend(green_bin_subtree)
    gyb.extend(yellow_bin_subtree)
    gyb.extend(blue_bin_subtree)
    gyb.extend([')'])

    gby = ['s(']
    gby.extend(green_bin_subtree)
    gby.extend(blue_bin_subtree)
    gby.extend(yellow_bin_subtree)
    gby.extend([')'])

    gb = ['s(']
    gb.extend(green_bin_subtree)
    gb.extend(blue_bin_subtree)
    gb.extend([')'])

    # Test solving green but still failing
    g_and_fail = ['s(']
    g_and_fail.extend(green_bin_subtree)
    g_and_fail.extend(['"banana" in  "blue bin"?'])
    g_and_fail.extend([')'])

    idle = ['move to "can" (-0.2, 0.4) 1.57!'] # Just do something that succeeds but does not interfere with goals

    environment.par.goals = goals
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(ybg)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(ygb)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(byg)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(bgy)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(gyb)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(gby)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(ybg_short_path)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(gb)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(g_and_fail)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(idle)

    environment.start_simulation(channel=50031, headless=True, hide_window=False)

    ybg_fitness = environment.get_fitnesses([ybg], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    ygb_fitness = environment.get_fitnesses([ygb], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    byg_fitness = environment.get_fitnesses([byg], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    bgy_fitness = environment.get_fitnesses([bgy], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    gyb_fitness = environment.get_fitnesses([gyb], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    gby_fitness = environment.get_fitnesses([gby], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    ybg_short_path_fitness = environment.get_fitnesses([ybg_short_path], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    gb_fitness = environment.get_fitnesses([gb], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    g_and_fail_fitness = environment.get_fitnesses([g_and_fail], [0], [0], 1)[0][0]
    assert not environment.pytree[0].success
    idle_fitness = environment.get_fitnesses([idle], [0], [0], 1)[0][0]
    assert environment.pytree[0].success

    all_fitnesses = [ybg_fitness[0], ygb_fitness[0], byg_fitness[0], bgy_fitness[0], gyb_fitness[0], gby_fitness[0]]

    assert round(ybg_fitness[0], 6) == round(ybg_fitness[2], 6)
    assert max(all_fitnesses) * 1.03 > min(all_fitnesses) # Att least 3% difference in fitnesses from reordering
    assert gb_fitness[0] < min(all_fitnesses)  # Not doing one of the tasks should be worse
    assert ybg_short_path_fitness[0] > ybg_fitness[0]  # Shorter path should be better
    assert g_and_fail_fitness[0] > idle_fitness[0]  # Not doing one of the tasks should be worse than nothing

    print("YBG fitness:", ybg_fitness)
    print("YGB fitness:", ygb_fitness)
    print("BYG fitness:", byg_fitness)
    print("BGY fitness:", bgy_fitness)
    print("GYB fitness:", gyb_fitness)
    print("GBY fitness:", gby_fitness)

def test_planner():
    """creates a whole manually constructed Behavior Tree to solve the scenario"""
    environment = get_environment(planner_environment=True)
    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists

    planner_goals = ['"paper" in "green bin"', '"can" in "yellow bin"', '"banana" in "blue bin"']
    behavior_list.convert_from_string(planner_goals)
    for i, goal in enumerate(planner_goals):
        planner_goals[i], _ = behavior_list.get_node(goal, world_interface)
    string_bt, _ = planner.plan(world_interface, behavior_list, planner_goals, remove_redundant_conditions=True, verbose=True)
    string_bt = string_bt.bt
    print(string_bt)

    verification_bt = \
        ['s(', 'f(', '"paper" in "green bin"?',
                     's(', 'f(', 'grasped "paper"?',
                                 's(', 'move to "paper" (-0.3, 0.3) 0.0!',
                                       'grasp "paper"!', ')', ')', 
                           'move to "green bin" (0.6, 0.0) 3.14!',
                           'place "paper" in "green bin"!', ')', ')',
                'f(', '"can" in "yellow bin"?',
                      's(', 'f(', 'grasped "can"?',
                                  's(', 'move to "can" (-0.2, 0.4) 1.57!',
                                        'grasp "can"!', ')', ')', 
                            'move to "yellow bin" (0.4, -0.4) -1.57!',
                            'place "can" in "yellow bin"!', ')', ')',
                'f(', '"banana" in "blue bin"?',
                      's(', 'f(', 'grasped "banana"?',
                                  's(', 'move to "banana" (-0.2, -0.4) -1.57!',
                                        'grasp "banana"!', ')', ')',
                                  'move to "blue bin" (0.4, 0.4) 1.57!',
                                  'place "banana" in "blue bin"!', ')', ')', ')']
    print(verification_bt)
    assert string_bt == verification_bt


def initialize_gp(environment, name="test_gp_sim_1") -> GPInstance:
    """Initialize the genetic programming instance."""
    n_agents = 32
    n_processes = 1

    gp_par = gp.GpParameters()
    gp_par.log_name = ''
    gp_par.behavior_lists = environment.par.py_tree_parameters.behavior_lists
    gp_par.ind_start_length = 5
    gp_par.min_length = 5
    gp_par.n_population = n_agents
    gp_par.f_crossover = 0.0625
    gp_par.n_offspring_crossover = 2
    gp_par.f_mutation = 0.4375
    gp_par.n_offspring_mutation = 2
    gp_par.max_multi_mutation = 3
    gp_par.initialize_from_baseline = True
    gp_par.plot = True
    gp_par.n_generations = 3
    gp_par.verbose = True
    gp_par.fig_best = True
    gp_par.save_interval = 10

    gp_instance = GPInstance(name, environment, n_processes, gp_par)

    return gp_instance

def test_gp():
    """test run scenario in sim with genetic programming to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=False, n_agents=32, preplan_subtrees=True)
    environment.start_simulation(channel=50032, headless=True, timescale=10)

    environment.par.goals = goals
    n_sims = 1
    all_fitnesses = []
    for i in range(n_sims):
        environment.set_seeds(i)
        gp_instance = initialize_gp(environment, "test_gp_sim_" + str(i))
        while gp_instance.is_runnable():
            gp_instance.step_gp()

        _, fitness, _, _ = gp_instance.get_final_info()
        assert fitness[0] >= -45000
        assert fitness[0] < -9000
        all_fitnesses.append(fitness[0])

    print(all_fitnesses)

def test_gp_and_planner():
    """test run scenario with genetic programming with planner to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=True)
    environment_sim = get_environment(planner_environment=False, n_agents=32, preplan_subtrees=True)

    environment.par.goals = goals
    environment_sim.par.goals = goals
    environment_sim.start_simulation(channel=50033, headless=True, timescale=10)

    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"banana" in "blue bin"', '"paper" in "green bin"', '"can" in "yellow bin"']
    behavior_list.convert_from_string(planner_goals)
    for i, goal in enumerate(planner_goals):
        planner_goals[i], _ = behavior_list.get_node(goal, world_interface)
    string_bt, _ = planner.plan(world_interface, behavior_list, planner_goals, remove_redundant_conditions=True, verbose=True)
    string_bt = string_bt.bt
    print(string_bt)

    behavior_list.convert_from_string(string_bt)

    n_sims = 1
    all_fitnesses = []
    for i in range(0, n_sims):
        environment.set_seeds(i)
        gp_instance = initialize_gp(environment_sim, "test_gp_and_planner_trashpicking/run_" + str(i))
        gp_instance.set_baseline(string_bt)
        while gp_instance.is_runnable():
            gp_instance.step_gp()
        _, fitness, _, _ = gp_instance.get_final_info()
        all_fitnesses.append(fitness[0])

    print(all_fitnesses)

def test_bo():
    """test run scenario with bo to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=True)
    environment_sim = get_environment(planner_environment=False, n_agents=1, preplan_subtrees=True)

    environment.par.goals = goals
    environment_sim.par.goals = goals
    environment_sim.start_simulation(channel=50034, headless=True, timescale=10)

    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"banana" in "blue bin"', '"paper" in "green bin"', '"can" in "yellow bin"']
    behavior_list.convert_from_string(planner_goals)
    for i, goal in enumerate(planner_goals):
        planner_goals[i], _ = behavior_list.get_node(goal, world_interface)
    string_bt, _ = planner.plan(world_interface, behavior_list, planner_goals, remove_redundant_conditions=False, verbose=True)
    string_bt = string_bt.bt
    print(string_bt)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(string_bt)

    iterations = 5
    fix_goal_condition = True
    n_sims = 1

    for i in range(n_sims):
        bo_settings = bo.HandlerSettings(hotstart=False,
                                        cascaded=False,
                                        runs_per_bt=1,
                                        validation_runs=0,
                                        log_name="bo_test/run_" + str(i),
                                        random_forest=False,
                                        batch_size=1)

        bo_handler = bo.BoHandler(environment_sim, string_bt, bo_settings)
        if fix_goal_condition:
            bo_handler.fix_conditions()

        for _ in range(iterations):
            bo_handler.step_optimization()
        assert bo_handler.best_fitness > -12000
