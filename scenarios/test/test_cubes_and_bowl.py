"""Unit test for testing cubes and bowl scenario."""

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
from scenarios.cubes_and_bowl import get_environment
from scenarios import behaviors
import bt_learning.gp.genetic_programming as gp
from bt_learning.gp.gp_instance import GPInstance
from bt_learning.bo import bo
from planner import planner

CUBE_SIZE = 0.06
goals = []
goals.append(Goal(behaviors.AtPos, {"target_object": '"red cube"',
                                    "relative_object": '"yellow cube"',
                                    "offset": (0, 0, CUBE_SIZE + 0.0),
                                    "angle": 0.0}))

goals.append(Goal(behaviors.AtPos, {"target_object": '"blue cube"',
                                    "relative_object": '"red cube"',
                                    "offset": (0, 0, CUBE_SIZE + 0.0),
                                    "angle": 0.0}))
goals.append(Goal(behaviors.InContainer, {"target_object": '"green cube"',
                                          "relative_object": '"bowl"'}))

def test_manual_tree():
    """ Creates a whole manually constructed Behavior Tree to solve the cubes and bowl scenario in simulation"""
    environment = get_environment(planner_environment=False, n_agents=1)

    red_subtree = ['f(', '"red cube" at pos "yellow cube" (0.0, 0.0, 0.06) 0.0?',
                                   's(', 'f(', 'grasped "red cube"?',
                                               's(', 'f(', 'robot near "red cube"?', 'move to "red cube" (0.4, -0.6) 3.14!', ')', 
                                                     'grasp "red cube"!', ')', ')',
                                         'move to "yellow cube" (-0.4, 0.0) 0.0!',
                                         'place "red cube" at "yellow cube" (0.0, 0.0, 0.06) 0.0!', ')', ')']
    red_shortpath_subtree = ['f(', '"red cube" at pos "yellow cube" (0.0, 0.0, 0.06) 0.0?',
                                   's(', 'f(', 'grasped "red cube"?',
                                               's(', 'f(', 'robot near "red cube"?', 'move to "red cube" (0.7, -0.6) 3.14!', ')', 
                                                     'grasp "red cube"!', ')', ')',
                                         'move to "yellow cube" (-0.7, 0.0) 0.0!',
                                         'place "red cube" at "yellow cube" (0.0, 0.0, 0.06) 0.0!', ')', ')']
    green_subtree = ['f(', '"green cube" in "bowl"?',
                                   's(', 'f(', 'grasped "green cube"?',
                                               's(', 'move to "green cube" (-0.4, 0.0) 0.0!',
                                                     'grasp "green cube"!', ')', ')',
                                         'robot near "bowl"?', 'place "green cube" in "bowl"!', ')', ')']
    blue_subtree = ['f(', '"blue cube" at pos "red cube" (0.0, 0.0, 0.06) 0.0?',
                                   's(', 'f(', 'grasped "blue cube"?', 's(', 'robot near "blue cube"?', 'grasp "blue cube"!', ')', ')',
                                         'robot near "red cube"?', 'place "blue cube" at "red cube" (0.0, 0.0, 0.06) 0.0!', ')', ')', ')']

    rgb = ['s(']
    rgb.extend(red_subtree)
    rgb.extend(green_subtree)
    rgb.extend(blue_subtree)
    rgb.extend([')'])

    rgb_shortpath = ['s(']
    rgb_shortpath.extend(red_shortpath_subtree)
    rgb_shortpath.extend(green_subtree)
    rgb_shortpath.extend(blue_subtree)
    rgb_shortpath.extend([')'])

    grb = ['s(']
    grb.extend(green_subtree)
    grb.extend(red_subtree)
    grb.extend(blue_subtree)
    grb.extend([')'])

    gr = ['s(']
    gr.extend(green_subtree)
    gr.extend(red_subtree)
    gr.extend([')'])

    rg = ['s(']
    rg.extend(red_subtree)
    rg.extend(green_subtree)
    rg.extend([')'])

    # Test solving red but still failing
    r_and_fail = ['s(']
    r_and_fail.extend(red_subtree)
    r_and_fail.extend(['"green cube" in "bowl"?'])
    r_and_fail.extend([')'])

    # Test solving green but still failing
    g_and_fail = ['s(']
    g_and_fail.extend(green_subtree)
    g_and_fail.extend(['"red cube" in "bowl"?'])
    g_and_fail.extend([')'])

    # Test solving green and then idling
    g_and_idle = ['s(']
    g_and_idle.extend(green_subtree)
    g_and_idle.extend(['idle!'])
    g_and_idle.extend([')'])

    idle = ['grasp "red cube"!'] # Just do something that succeeds but does not interfere with goals

    environment.par.goals = goals
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(rgb)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(rgb_shortpath)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(grb)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(gr)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(rg)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(r_and_fail)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(g_and_fail)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(g_and_idle)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(idle)
    environment.start_simulation(channel=50051, headless=True, hide_window=False)


    rgb_fitness = environment.get_fitnesses([rgb], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    grb_fitness = environment.get_fitnesses([grb], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    gr_fitness = environment.get_fitnesses([gr], [0], [0], 1)[0][0]
    rg_fitness = environment.get_fitnesses([rg], [0], [0], 1)[0][0]
    rgb_shortpath_fitness = environment.get_fitnesses([rgb_shortpath], [0], [0], 1)[0][0]
    assert environment.pytree[0].success
    r_and_fail_fitness = environment.get_fitnesses([r_and_fail], [0], [0], 1)[0][0]
    assert not environment.pytree[0].success # Should fail because we are not doing the green task
    g_and_fail_fitness = environment.get_fitnesses([g_and_fail], [0], [0], 1)[0][0]
    assert not environment.pytree[0].success # Should fail
    g_and_idle_fitness = environment.get_fitnesses([g_and_idle], [0], [0], 1)[0][0]
    assert not environment.pytree[0].success
    idle_fitness = environment.get_fitnesses([idle], [0], [0], 1)[0][0]
    assert environment.pytree[0].success

    assert grb_fitness[0] < rgb_fitness[0] * 1.03 # Att least 3% difference in fitnesses from reordering
    assert round(rgb_fitness[0], 6) == round(rgb_fitness[2], 6)
    assert gr_fitness[0] < grb_fitness[0] # Not doing one of the tasks should be worse
    assert rg_fitness[0] < grb_fitness[0] # Not doing one of the tasks should be worse
    assert rgb_shortpath_fitness[0] > rgb_fitness[0]  # Shorter path should be better
    assert r_and_fail_fitness[0] > idle_fitness[0]  # Not doing one of the tasks should be worse than nothing
    assert g_and_fail_fitness[0] > idle_fitness[0]  # Not doing one of the tasks should be worse than nothing
    assert g_and_idle_fitness[0] > idle_fitness[0]  # Not doing one of the tasks should be worse than nothing
    print(rgb_fitness)


def test_planner():
    """creates a whole manually constructed Behavior Tree to solve the scenario"""
    environment = get_environment(planner_environment=True)
    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"red cube" at pos "yellow cube" (0.0, 0.0, 0.06) 0.0?',
                     '"green cube" in "bowl"?',
                     '"blue cube" at pos "red cube" (0.0, 0.0, 0.06) 0.0?']

    behavior_list.convert_from_string(planner_goals)
    for i, goal in enumerate(planner_goals):
        planner_goals[i], _ = behavior_list.get_node(goal, world_interface)
    string_bt, _ = planner.plan(world_interface, behavior_list, planner_goals, remove_redundant_conditions=True, save_figs=True)
    string_bt = string_bt.bt
    print(string_bt)

    verification_bt = ['s(', 'f(', '"red cube" at pos "yellow cube" (0.0, 0.0, 0.06) 0.0?',
                                   's(', 'f(', 'grasped "red cube"?',
                                               's(', 'robot near "red cube"?', 'grasp "red cube"!', ')', ')',
                                         'move to "yellow cube" (-0.4, 0.0) 0.0!',
                                         'place "red cube" at "yellow cube" (0.0, 0.0, 0.06) 0.0!', ')', ')', 
                             'f(', '"green cube" in "bowl"?',
                                   's(', 'f(', 'grasped "green cube"?',
                                               's(', 'robot near "green cube"?', 'grasp "green cube"!', ')', ')',
                                         'robot near "bowl"?', 'place "green cube" in "bowl"!', ')', ')',
                             'f(', '"blue cube" at pos "red cube" (0.0, 0.0, 0.06) 0.0?',
                                   's(', 'f(', 'grasped "blue cube"?', 's(', 'robot near "blue cube"?', 'grasp "blue cube"!', ')', ')',
                                         'robot near "red cube"?', 'place "blue cube" at "red cube" (0.0, 0.0, 0.06) 0.0!', ')', ')', ')']
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
    gp_par.n_generations = 5
    gp_par.verbose = True
    gp_par.fig_best = True
    gp_par.save_interval = 10

    gp_instance = GPInstance(name, environment, n_processes, gp_par)

    return gp_instance


def test_gp():
    """test run scenario in sim with genetic programming to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=False, n_agents=32, preplan_subtrees=True)
    environment.start_simulation(channel=50052, headless=True, timescale=10)

    environment.par.goals = goals
    n_sims = 1
    all_fitnesses = []
    for i in range(n_sims):
        environment.set_seeds(i)
        gp_instance = initialize_gp(environment, "test_gp_cubebowl/run_" + str(i))
        while gp_instance.is_runnable():
            gp_instance.step_gp()

        _, fitness, _, _ = gp_instance.get_final_info()
        assert fitness[0] >= -35000
        assert fitness[0] < -6000
        all_fitnesses.append(fitness[0])

    print(all_fitnesses)

def test_gp_and_planner():
    """test run scenario with genetic programming with planner to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=True)
    environment_sim = get_environment(planner_environment=False, n_agents=32, preplan_subtrees=True)

    environment.par.goals = goals
    environment_sim.par.goals = goals
    environment_sim.start_simulation(channel=50053, headless=True, timescale=10)

    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"green cube" in "bowl"?',
                     '"red cube" at pos "yellow cube" (0.0, 0.0, 0.06) 0.0?',
                     '"blue cube" at pos "red cube" (0.0, 0.0, 0.06) 0.0?']
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
        gp_instance = initialize_gp(environment_sim, "test_gp_and_planner_cubebowl/run_" + str(i))
        gp_instance.set_baseline(string_bt)
        while gp_instance.is_runnable():
            gp_instance.step_gp()
        _, fitness, _, _ = gp_instance.get_final_info()
        all_fitnesses.append(fitness[0])
    assert fitness[0] > -10000

    print(all_fitnesses)

def test_bo():
    """test run scenario with bo to see if progress is made and no errors are encountered"""
    environment = get_environment(planner_environment=True)
    environment_sim = get_environment(planner_environment=False, n_agents=32, preplan_subtrees=True)

    environment.par.goals = goals
    environment_sim.par.goals = goals
    environment_sim.start_simulation(channel=50054, headless=True, timescale=10)

    world_interface = environment.sim_class(environment.par.sim_parameters)
    world_interface.extra_preconditions = True
    behavior_list = environment.par.py_tree_parameters.behavior_lists
    planner_goals = ['"red cube" at pos "yellow cube" (0.0, 0.0, 0.06) 0.0?',
                     '"green cube" in "bowl"?',
                     '"blue cube" at pos "red cube" (0.0, 0.0, 0.06) 0.0?']
    behavior_list.convert_from_string(planner_goals)
    for i, goal in enumerate(planner_goals):
        planner_goals[i], _ = behavior_list.get_node(goal, world_interface)
    string_bt, _ = planner.plan(world_interface, behavior_list, planner_goals, remove_redundant_conditions=False, verbose=True)
    string_bt = string_bt.bt
    print(string_bt)
    behavior_list.convert_from_string(string_bt)

    iterations = 2
    fix_goal_condition = True
    n_sims = 1

    for i in range(0, n_sims):
        environment.set_seeds(i)
        bo_settings = bo.HandlerSettings(hotstart=False,
                                        cascaded=False,
                                        runs_per_bt=1,
                                        validation_runs=0,
                                        log_name="bo_test_cubebowl/run_" + str(i),
                                        random_forest=False,
                                        batch_size=1)

        bo_handler = bo.BoHandler(environment_sim, string_bt, bo_settings)
        if fix_goal_condition:
            bo_handler.fix_conditions()

        for _ in range(iterations):
            bo_handler.step_optimization()
        assert bo_handler.best_fitness > -6000
