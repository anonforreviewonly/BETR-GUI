"""Defining demo scenario."""

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
from scenarios import behavior_list_settings
from interfaces.base_world_interface import BaseWorldInterfaceParameters
from interfaces.py_trees_interface import PyTreeParameters
from interfaces.planner_world_interface import WorldInterface as PlannerWorldInterface

if platform.system() == "Windows":
    from interfaces.unity_world_interface import WorldInterface as SimWorldInterface
else:
    SimWorldInterface = None #pylint: disable=invalid-name

def true_fitness(
    world_interface: Any, coeff: fitness_function.Coefficients = None) -> float: # pylint: disable=unused-argument
    """Compute true fitness for the scenario."""
    fitness = 0.0
    coeff = fitness_function.Coefficients()

    return fitness

def get_parameters(preplan_subtrees=True):
    """ Returns common parameters for scenario """
    movable_objects = ['"red ball"', '"green ball"', '"yellow ball"']
    static_objects = ['"goal area"']
    container_objects = static_objects[:]
    object_positions = {}
    object_positions['"red ball"'] = np.array([0.8, 0.0, 0.0001])
    object_positions['"green ball"'] = np.array([0.8, -1, 0.0001])
    object_positions['"yellow ball"'] = np.array([0.8, 1, 0.0001])
    object_positions['"goal area"'] = np.array([2.5, 0.0, 0.0])
    object_positions['"robot base"'] = np.array([0.0, 0.0, 0.0001])

    behavior_lists = behavior_list_settings.get_behavior_list(movable_objects, static_objects=static_objects,
                                                              container_objects=container_objects, mobile_base=True,
                                                              preplan_subtrees=preplan_subtrees, default_object_positions=object_positions)
    parameters = env.EnvParameters()
    parameters.py_tree_parameters = PyTreeParameters()
    parameters.py_tree_parameters.behavior_lists = behavior_lists
    parameters.py_tree_parameters.max_ticks = 200
    object_yaws = {}

    parameters.sim_parameters = BaseWorldInterfaceParameters(movable_objects=movable_objects,
                                                             object_positions=object_positions,
                                                             object_yaws=object_yaws)
    urdf_path = os.path.join(os.path.dirname(__file__), '../simulation/Assets/URDF/crb15000_5_95_gripper.urdf')
    parameters.sim_parameters.chain = ikpy.chain.Chain.from_urdf_file(urdf_path,
        active_links_mask=[False, True, True, True, True, True, True, False])  # Turn links on / off for IK

    parameters.true_fitness = true_fitness
    parameters.scenario = "spheres"
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
    environment = env.Environment(parameters)
    environment.scene_description = "The green ball is on the floor. The red ball is on the floor. " + \
                                    "The yellow ball is on the floor. The green ball is to the left. " + \
                                    "The red ball is in the middle. The yellow ball is to the right. " + \
                                    "The goal area is straight ahead. The robot is at the origin, facing the goal area."
    return environment
