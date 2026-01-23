"""Defining trashpicking scenario."""

# Copyright (c) 2025, ABB
# All rights reserved.
#
# Redistribution and use in source and binary forms, with
# or without modification, are permitted provided that
# the following conditions are met:
#
#   * Redistributions of source code must retain thea
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
import os
from typing import Any
import platform
import numpy as np
import ikpy.chain
import scenarios.environment as env
from scenarios import fitness_function

from scenarios import behaviors, behavior_list_settings
from interfaces.base_world_interface import BaseWorldInterfaceParameters
from interfaces.py_trees_interface import PyTreeParameters
from interfaces.planner_world_interface import WorldInterface as PlannerWorldInterface

if platform.system() == "Windows":
    from interfaces.unity_world_interface import WorldInterface as SimWorldInterface
else:
    SimWorldInterface = None #pylint: disable=invalid-name

def true_fitness(
    world_interface: Any,
    coeff: fitness_function.Coefficients = None
) -> float:
    """Compute true fitness for the scenario."""
    fitness = 0.0

    coeff = fitness_function.Coefficients(pos_acc=0.1, angle_acc=0.2)
    fitness += behaviors.AtPos.compute_fitness({"target_object": '"fork"',
                                                "relative_object": '"plate"',
                                                "offset": [-0.2, 0, 0.0],
                                                "angle": 3.14}, world_interface, coeff)
    fitness += behaviors.AtPos.compute_fitness({"target_object": '"knife"',
                                                "relative_object": '"plate"',
                                                "offset": [0.2, 0, 0.0],
                                                "angle": 3.14}, world_interface, coeff)
    fitness += behaviors.AtPos.compute_fitness({"target_object": '"glass"',
                                                "relative_object": '"plate"',
                                                "offset": [0.0, 0.2, 0.0],
                                                "angle": 0.0}, world_interface, coeff)

    return fitness

def get_true_goals():
    """ Returns the true goals for the scenario """
    true_goals = []
    true_goals.append(env.Goal(behaviors.AtPos,
                               {"target_object": '"fork"',
                                "relative_object": '"plate"',
                                "offset": [-0.2, 0, 0.0],
                                "angle": 3.14,
                                "pos_acc": 0.1,
                                "angle_acc": 0.2}))
    true_goals.append(env.Goal(behaviors.AtPos,
                               {"target_object": '"knife"',
                                "relative_object": '"plate"',
                                "offset": [0.2, 0, 0.0],
                                "angle": 3.14,
                                "pos_acc": 0.1,
                                "angle_acc": 0.2}))
    true_goals.append(env.Goal(behaviors.AtPos,
                               {"target_object": '"glass"',
                                "relative_object": '"plate"',
                                "offset": [0.0, 0.2, 0.0],
                                "angle": 0.0,
                                "pos_acc": 0.1,
                                "angle_acc": 0.2}))
    return true_goals

def get_parameters(preplan_subtrees):
    """ Returns common parameters for scenario """
    movable_objects = ['"knife"', '"fork"', '"glass"']
    static_objects = ['"plate"']
    object_positions = {}
    object_positions['"plate"'] = np.array([-0.3, -0.2, 0.3])
    object_positions['"knife"'] = np.array([0.65, 0.25, 0.3])
    object_positions['"spoon"'] = np.array([0.0, 0.0, -10.0])
    object_positions['"fork"'] = np.array([0.2, 2.0, 0.0001])
    object_positions['"glass"'] = np.array([0.62, 0.25, 0.3])
    object_positions['"robot base"'] = np.array([-0.3, 2.0, 0.0001])
    object_yaws = {}

    behavior_lists = behavior_list_settings.get_behavior_list(movable_objects,
                                                              static_objects=static_objects, preplan_subtrees=preplan_subtrees,
                                                              default_object_positions=object_positions, mobile_base=True)
    parameters = env.EnvParameters()
    parameters.py_tree_parameters = PyTreeParameters()
    parameters.py_tree_parameters.behavior_lists = behavior_lists
    parameters.py_tree_parameters.max_ticks = 125

    parameters.sim_parameters = BaseWorldInterfaceParameters(movable_objects=movable_objects, object_positions=object_positions,
                                                             object_yaws=object_yaws)
    urdf_path = os.path.join(os.path.dirname(__file__), '../simulation/Assets/URDF/crb15000_5_95_gripper.urdf')
    parameters.sim_parameters.chain = ikpy.chain.Chain.from_urdf_file(urdf_path,
        active_links_mask=[False, True, True, True, True, True, True, False])  # Turn links on / off for IK

    parameters.true_fitness = true_fitness
    parameters.scenario = "tableware"
    return parameters

def get_environment(planner_environment=False, n_agents=1, preplan_subtrees=True):
    """ Returns the environment for running cubes and bowl scenario"""
    parameters = get_parameters(preplan_subtrees)
    if planner_environment:
        parameters.sim_class = PlannerWorldInterface
    else:
        parameters.sim_class = SimWorldInterface
        parameters.parallel_agents = True
        parameters.n_agents = n_agents
        parameters.physics_sim = True
    parameters.goals = []
    parameters.true_goals = get_true_goals()
    environment = env.Environment(parameters)

    environment.scene_description = "The table is on the floor. The chair is on the floor next to the table. " + \
                                    "The plate is on the table in front of the chair. The plate is around 35cm in diameter. " + \
                                    "The glass is on the table." + \
                                    "The knife is on the table. The knife's edge is pointing towards the chair at 0 radians rotation. " + \
                                    "The fork is on the floor. The fork's tines are pointing towards the chair at 0 radians rotation. " + \
                                    "The y-axis is pointing away from the chair. The x-axis is pointing to the right of the chair."
    return environment
