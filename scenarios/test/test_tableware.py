"""Unit test for testing tableware scenario."""

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

from behaviors.common_behaviors import Goal
import bt_learning.gp.genetic_programming as gp
from bt_learning.gp.gp_instance import GPInstance
from bt_learning.bo import bo
from scenarios.tableware import get_environment
from scenarios import behaviors

from planner import planner

goals = []
goals.append(Goal(behaviors.AtPos, {"not": False,
                                    "target_object": '"knife"',
                                    "relative_object": '"plate"',
                                    "offset": (0.2, 0.0, 0.0),
                                    "angle": 3.14}))
goals.append(Goal(behaviors.AtPos, {"not": False,
                                    "target_object": '"fork"',
                                    "relative_object": '"plate"',
                                    "offset": (-0.2, 0.0, 0.0),
                                    "angle": 3.14}))
goals.append(Goal(behaviors.AtPos, {"not": False,
                                    "target_object": '"glass"',
                                    "relative_object": '"plate"',
                                    "offset": (0, 0.2, 0.0),
                                    "angle": 0.0}))

def test_manual_tree():
    """ Creates a whole manually constructed Behavior Tree to solve the cubes and bowl scenario in simulation"""
    environment = get_environment(planner_environment=False, n_agents=1)



    fork_subtree = ['f(', '"fork" at pos "plate" (-0.2, 0.0, 0.0) 3.14?',
                          's(', 'f(', 'grasped "fork"?',
                                      's(', 'move to "fork" (-0.4, 0.0) 0.0!',
                                            'grasp "fork"!', ')', ')',
                                'move to "plate" (0.0, 0.7) 1.57!',
                                'place "fork" at "plate" (-0.2, 0.0, 0.0) 3.14!', ')', ')']
    far_fork_subtree = ['f(', '"fork" at pos "plate" (-0.2, 0.0, 0.0) 3.14?',
                              's(', 'f(', 'grasped "fork"?',
                                          's(', 'move to "fork" (-0.4, 0.0) 0.0!',
                                                'grasp "fork"!', ')', ')',
                            'move to "plate" (0.1, 0.8) 1.57!',
                            'place "fork" at "plate" (-0.2, 0.0, 0.0) 3.14!', ')', ')']
    glass_subtree = ['f(', '"glass" at pos "plate" (0.0, 0.2, 0.0) 0.0?',
                          's(', 'f(', 'grasped "glass"?', 
                                      's(', 'move to "glass" (-0.2, 0.4) 1.57!',
                                            'grasp "glass"!', ')', ')', 
                                'move to "plate" (0.0, 0.7) 1.57!',
                                'place "glass" at "plate" (0.0, 0.2, 0.0) 0.0!', ')', ')']
    knife_subtree = ['f(', '"knife" at pos "plate" (0.2, 0.0, 0.0) 3.14?',
                          's(', 'f(', 'grasped "knife"?',
                                      's(', 'move to "knife" (-0.2, 0.4) 1.57!',
                                            'grasp "knife"!', ')', ')',
                                'move to "plate" (0.0, 0.7) 1.57!',
                                'place "knife" at "plate" (0.2, 0.0, 0.0) 3.14!', ')', ')']

    full_tree = ['s(']
    full_tree.extend(fork_subtree)
    full_tree.extend(glass_subtree)
    full_tree.extend(knife_subtree)
    full_tree.extend([')'])

    bad_order = ['s(']
    bad_order.extend(glass_subtree)
    bad_order.extend(fork_subtree)
    bad_order.extend(knife_subtree)
    bad_order.extend([')'])

    fork_knife_glass = ['s(']
    fork_knife_glass.extend(fork_subtree)
    fork_knife_glass.extend(knife_subtree)
    fork_knife_glass.extend(glass_subtree)
    fork_knife_glass.extend([')'])

    fork_glass = ['s(']
    fork_glass.extend(fork_subtree)
    fork_glass.extend(glass_subtree)
    fork_glass.extend([')'])

    far_fork = ['s(']
    far_fork.extend(far_fork_subtree)
    far_fork.extend(glass_subtree)
    far_fork.extend(knife_subtree)
    far_fork.extend([')'])

    # Test solving fork but still failing
    fork_and_fail = ['s(']
    fork_and_fail.extend(fork_subtree)
    fork_and_fail.extend(['"knife" at pos "plate" (0.2, 0.0, 0.0) 3.14?'])
    fork_and_fail.extend([')'])

    idle = ['grasp "fork"!'] # Just do something that succeeds but does not interfere with goals

    collision = ['s(', 'f(', '"fork" at pos "plate" (-0.2, 0.0, 0.0) 3.14?',
                                  's(', 'f(', 'grasped "fork"?', 'grasp "fork"!', ')', 
                                        'f(', 'robot near "plate"?', 'move to "plate" (0.0, 0.6) 1.57!', ')', 
                                        'place "fork" at "plate" (-0.2, 0.0, 0.0) 3.14!', ')', ')',
                            'f(', '"glass" at pos "plate" (0.0, 0.2, 0.0) 0.0?',
                                  's(', 'f(', 'robot near "plate"?', 'move to "plate" (0.0, 0.6) 1.57!', ')', 
                                        'f(', 'grasped "glass"?', 
                                              's(', 'f(', 'robot near "glass"?', 'move to "glass" (-0.2, 0.4) 1.57!', ')',
                                        'grasp "glass"!', ')', 'grasp "knife"!', ')', 
                                        'place "glass" at "plate" (0.0, 0.2, 0.0) 0.0!', ')', 'robot at "glass" (-0.3, -0.6) 1.57?', ')',
                            'f(', '"knife" at pos "plate" (0.2, 0.0, 0.0) 3.14?',
                                  's(', 'f(', 'grasped "knife"?', 'robot at "knife" (0.1, -0.8) 3.14?', 'grasp "knife"!', ')',
                                        'f(', 'robot near "plate"?', 'move to "plate" (0.0, 0.6) 1.57!', ')',
                                        'place "knife" at "plate" (0.2, 0.0, 0.0) 3.14!', ')', ')', ')']


    environment.par.goals = goals
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(fork_subtree)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(glass_subtree)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(knife_subtree)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(full_tree)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(bad_order)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(fork_knife_glass)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(fork_glass)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(far_fork)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(fork_and_fail)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(idle)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(collision)

    environment.start_simulation(channel=50041, headless=True, hide_window=False)

    fork_fitness = environment.get_fitnesses([fork_subtree], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    glass_fitness = environment.get_fitnesses([glass_subtree], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    knife_fitness = environment.get_fitnesses([knife_subtree], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    full_fitness = environment.get_fitnesses([full_tree], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    bad_order_fitness = environment.get_fitnesses([bad_order], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    fork_glass_fitness = environment.get_fitnesses([fork_glass], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    fork_knife_glass_fitness = environment.get_fitnesses([fork_knife_glass], [0], [0], 1)[0][0]
    assert not environment.pytree[0].success
    far_fork_fitness = environment.get_fitnesses([far_fork], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    fork_and_fail_fitness = environment.get_fitnesses([fork_and_fail], [0], [0], 1)[0][0]
    assert not environment.pytree[0].success
    idle_fitness = environment.get_fitnesses([idle], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    collision_fitness = environment.get_fitnesses([collision], [0], [0], 1)[0][0]
    assert not environment.pytree[0].success

    assert bad_order_fitness[0] < full_fitness[0] * 1.1
    assert fork_knife_glass_fitness[0] < full_fitness[0] * 1.1
    assert far_fork_fitness[0] > full_fitness[0]
    assert full_fitness[0] > fork_glass_fitness[0]
    assert full_fitness[0] > fork_fitness[0]
    assert full_fitness[0] > glass_fitness[0]
    assert full_fitness[0] > knife_fitness[0]
    assert fork_and_fail_fitness[0] > idle_fitness[0]
    assert collision_fitness[0] < full_fitness[0]
    assert round(full_fitness[0], 6) == round(full_fitness[2], 6)
    print(full_fitness)

def test_planner():
    """creates a whole manually constructed Behavior Tree to solve the scenario"""
    environment = get_environment(planner_environment=True)
    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"fork" at pos "plate" (-0.2, 0.0, 0.0) 3.14?',
                     '"glass" at pos "plate" (0.0, 0.2, 0.0) 0.0?',
                     '"knife" at pos "plate" (0.2, 0.0, 0.0) 3.14?']
    behavior_list.convert_from_string(planner_goals)
    for i, goal in enumerate(planner_goals):
        planner_goals[i], _ = behavior_list.get_node(goal, world_interface)
    string_bt, _ = planner.plan(world_interface, behavior_list, planner_goals, remove_redundant_conditions=True, verbose=True)
    string_bt = string_bt.bt
    print(string_bt)

    verification_bt = ['s(', 'f(', '"fork" at pos "plate" (-0.2, 0.0, 0.0) 3.14?',
                                   's(', 'f(', 'grasped "fork"?', 
                                               's(', 'robot near "fork"?', 'grasp "fork"!', ')', ')', 
                                         'move to "plate" (0.0, 0.7) 1.57!', 
                                         'place "fork" at "plate" (-0.2, 0.0, 0.0) 3.14!', ')', ')', 
                             'f(', '"glass" at pos "plate" (0.0, 0.2, 0.0) 0.0?', 
                                   's(', 'f(', 'grasped "glass"?', 
                                               's(', 'move to "glass" (-0.2, 0.4) 1.57!',
                                                     'grasp "glass"!', ')', ')', 
                                          'move to "plate" (0.0, 0.7) 1.57!', 
                                          'place "glass" at "plate" (0.0, 0.2, 0.0) 0.0!', ')', ')', 
                             'f(', '"knife" at pos "plate" (0.2, 0.0, 0.0) 3.14?', 
                                   's(', 'f(', 'grasped "knife"?', 
                                               's(', 'move to "knife" (-0.2, 0.4) 1.57!',
                                                     'grasp "knife"!', ')', ')', 
                                         'move to "plate" (0.0, 0.7) 1.57!',
                                         'place "knife" at "plate" (0.2, 0.0, 0.0) 3.14!', ')', ')', ')']
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
    environment.start_simulation(channel=50042, headless=True, timescale=10)

    environment.par.goals = goals
    n_sims = 1
    all_fitnesses = []
    for i in range(n_sims):
        environment.set_seeds(i)
        gp_instance = initialize_gp(environment, "test_gp_tableware/run_" + str(i))
        while gp_instance.is_runnable():
            gp_instance.step_gp()

        _, fitness, _, _ = gp_instance.get_final_info()
        assert fitness[0] >= -30000
        assert fitness[0] < -6000
        all_fitnesses.append(fitness[0])

    print(all_fitnesses)


def test_gp_and_planner():
    """test run scenario with genetic programming with planner to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=True)
    environment_sim = get_environment(planner_environment=False, n_agents=32, preplan_subtrees=True)

    environment.par.goals = goals
    environment_sim.par.goals = goals
    environment_sim.start_simulation(channel=50043, headless=True, timescale=10)

    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"glass" at pos "plate" (0.0, 0.2, 0.0) 0.0?',
                     '"fork" at pos "plate" (-0.2, 0.0, 0.0) 3.14?',
                     '"knife" at pos "plate" (0.2, 0.0, 0.0) 3.14?']
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
        gp_instance = initialize_gp(environment_sim, "test_gp_and_planner_tableware/run_" + str(i))
        gp_instance.set_baseline(string_bt)
        while gp_instance.is_runnable():
            gp_instance.step_gp()
        _, fitness, _, _ = gp_instance.get_final_info()
        all_fitnesses.append(fitness[0])
        assert fitness[0] > -16000
        assert fitness[0] < -6000

    print(all_fitnesses)

def test_bo():
    """test run scenario with bo to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=True)
    environment_sim = get_environment(planner_environment=False, n_agents=1, preplan_subtrees=True)

    environment.par.goals = goals
    environment_sim.par.goals = goals
    environment_sim.start_simulation(channel=50047, headless=True, timescale=10)

    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"fork" at pos "plate" (-0.2, 0.0, 0.0) 3.14?',
                     '"glass" at pos "plate" (0.0, 0.2, 0.0) 0.0?',
                     '"knife" at pos "plate" (0.2, 0.0, 0.0) 3.14?']
    behavior_list.convert_from_string(planner_goals)
    for i, goal in enumerate(planner_goals):
        planner_goals[i], _ = behavior_list.get_node(goal, world_interface)
    string_bt, _ = planner.plan(world_interface, behavior_list, planner_goals, remove_redundant_conditions=False, verbose=True)
    string_bt = string_bt.bt
    print(string_bt)
    behavior_list.convert_from_string(string_bt)

    iterations = 3
    fix_goal_condition = True
    n_sims = 1

    for i in range(0, n_sims):
        environment.set_seeds(i)
        bo_settings = bo.HandlerSettings(hotstart=False,
                                        cascaded=False,
                                        runs_per_bt=1,
                                        validation_runs=0,
                                        log_name="bo_test_tableware/run_" + str(i),
                                        random_forest=False,
                                        batch_size=1)

        bo_handler = bo.BoHandler(environment_sim, string_bt, bo_settings)
        if fix_goal_condition:
            bo_handler.fix_conditions()

        for _ in range(iterations):
            bo_handler.step_optimization()
        assert bo_handler.best_fitness > -13000
        assert bo_handler.best_fitness < -6000
