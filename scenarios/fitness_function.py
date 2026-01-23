"""Task dependent fitness function."""

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

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from interfaces.py_trees_interface import PyTree


@dataclass
class Coefficients:
    """Coefficients for tuning the fitness function."""
    position: float = -25.0
    angle: float = -10.0
    pos_acc: float = 0.02
    pos_acc_base: float = 0.1
    angle_acc: float = 0.2
    depth: float = -0.01
    length: float = -0.1
    ticks: float = 0.0
    failed: float = -20.0
    action_failure: float = -10.0
    lower_action_index: float = -50.0
    no_success: float = 0.0
    timeout: float = -30.0
    grasped: float = -1.0
    hand_not_empty: float = -1.0
    energy_consumed: float = -20.0
    targets: list = field(default_factory=list)


def compute_fitness(
    world_interface: Any,
    py_tree: PyTree,
    coeff: Any = None,
    verbose: bool = False
) -> tuple:
    """Retrieve values and compute fitness."""
    if coeff is None:
        coeff = Coefficients()

    depth = py_tree.get_depth()
    length = py_tree.get_length()
    fitness = 0.0

    if coeff.position != 0.0:
        for i, target in enumerate(coeff.targets):
            fitness += coeff.position * max(
                0, world_interface.distance(i, target) - coeff.pos_acc)
            if verbose:
                print('Fitness:', fitness)
                print(i, ': ', world_interface.get_object_position(i))

    if py_tree.failed:
        fitness += coeff.failed
        if verbose:
            print('Failed: ', fitness)
    if coeff.action_failure != 0.0:
        # Action failures are indicative of bad behavior tree design and should not be used to guide the tree traversal """
        n_failed_actions = world_interface.get_n_failed_actions()
        if n_failed_actions > 0:
            fitness += coeff.action_failure * n_failed_actions
            if verbose:
                print('Action failures: ', fitness, ' (', n_failed_actions, ')')
    if coeff.lower_action_index != 0.0:
        # Lower action index means the tree is executing from right to left, which is generally a sign of a bad tree design
        if world_interface.get_lower_action_index():
            fitness += coeff.lower_action_index
            if verbose:
                print('Lower action index: ', fitness)
    elif not py_tree.success:
        fitness += coeff.no_success
        if verbose:
            print('No success (probably timeout): ', fitness)
    if py_tree.timeout:
        fitness += coeff.timeout
        if verbose:
            print('Timed out: ', fitness)
    if coeff.hand_not_empty != 0.0 and world_interface.get_grasped_object() is not None:
        fitness += coeff.hand_not_empty
        if verbose:
            print('Hand not empty: ', fitness)

    if coeff.energy_consumed != 0.0:
        fitness += coeff.energy_consumed * world_interface.energy_consumed
        if verbose:
            print('Energy consumed: ', fitness)

    net_fitness = fitness # Length should not affect the net fitness, only for controlling the gp algorithm in this case
    fitness += coeff.length * length + coeff.depth * depth + coeff.ticks * py_tree.ticks
    if verbose:
        print('Fitness from length:', fitness - net_fitness)

    n_steps = 1
    # Rounding to ensure that binary approximation doesn't affect fitness ranking
    return (round(fitness, 10), net_fitness, n_steps)
