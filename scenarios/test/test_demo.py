"""Unit test for testing demo scenario."""

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

from scenarios import behaviors
from scenarios.demo import get_environment
from behaviors.common_behaviors import Goal

def test_manual_tree():
    """ Creates a whole manually constructed Behavior Tree to solve the trashpicking scenario in simulation"""
    environment = get_environment(planner_environment=False, n_agents=1)

    red_ball_subtree = ['f(', '"red ball" in "goal area"?',
                              's(', 'f(', 'grasped "red ball"?', 
                                          'grasp "red ball"!', ')', 
                                    'f(', 'robot near "goal area"?', 'move to "goal area" (-0.6, 0.0) 0.0!', ')', 
                                    'place "red ball" in "goal area"!', ')', ')']

    green_ball_subtree = ['f(', 'grasped "green ball"?',
                                's(', 'f(', 'robot near "green ball"?', 'move to "green ball" (-0.6, 0.0) 0.0!', ')', 
                                      'grasp "green ball"!', ')', ')']

    yellow_ball_subtree = ['f(', 'grasped "yellow ball"?',
                            's(', 'f(', 'robot near "yellow ball"?', 'move to "yellow ball" (-0.6, 0.0) 0.0!', ')', 
                                    'grasp "yellow ball"!', ')', ')']

    goals = []
    goals.append(Goal(behaviors.InContainer, {"target_object": '"red ball"',
                                              "relative_object": '"goal area"'}))

    environment.par.goals = goals
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(red_ball_subtree)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(green_ball_subtree)
    environment.par.py_tree_parameters.behavior_lists.convert_from_string(yellow_ball_subtree)

    environment.start_simulation(channel=50021, headless=True, hide_window=False)

    fitness = environment.get_fitnesses([red_ball_subtree], [0], [0], 1)[0][0]
    print("Fitness: " + str(fitness))
    assert environment.pytree[0].success

    fitness = environment.get_fitnesses([green_ball_subtree], [0], [0], 1)[0][0]
    print("Fitness: " + str(fitness))
    assert not environment.pytree[0].success

    fitness = environment.get_fitnesses([yellow_ball_subtree], [0], [0], 1)[0][0]
    print("Fitness: " + str(fitness))
    assert not environment.pytree[0].success


if __name__ == "__main__":
    # import cProfile
    # from pstats import Stats

    # pr = cProfile.Profile()
    # pr.enable()
    test_manual_tree()
    # pr.disable()
    # stats = Stats(pr)
    # stats.sort_stats('cumtime').print_stats(100)
    # stats.sort_stats('tottime').print_stats(100)
