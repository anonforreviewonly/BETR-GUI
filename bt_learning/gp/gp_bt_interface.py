# pylint: disable=broad-exception-raised
"""Provide an interface between a GP algorithm and behavior tree functions."""

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
from typing import List, Tuple

from behaviors import behavior_tree
from behaviors.behavior_lists import BehaviorLists
from behaviors.common_behaviors import ParameterizedNode


def random_genome(
    min_length: int,
    p_leaf: float,
    behavior_lists: BehaviorLists,
    locked_tree=None,
    locked_mask=None
) -> List[ParameterizedNode]:
    """Return a random genome."""
    bt = behavior_tree.BT([], behavior_lists)
    return bt.random(min_length, p_leaf, locked_tree, locked_mask)


def mutate_gene(
    genome: List[ParameterizedNode],
    p_add: float,
    p_delete: float,
    p_parameter: float,
    p_replace: float,
    p_swap: float,
    p_leaf: float,
    behavior_lists: BehaviorLists,
    locked_tree=None,
    locked_mask=None,
    check_validity: bool = True
):
    """ Mutate only a single gene."""
    if p_add < 0 or p_delete < 0 or p_parameter < 0 or p_replace < 0 or p_swap < 0:
        raise Exception('Mutation parameters must not be negative.')

    if p_add + p_delete + p_parameter + p_replace + p_swap > 1:
        raise Exception('Sum of the mutation probabilities must be less than 1.')

    mutated_individual = behavior_tree.BT([], behavior_lists)
    mutated_individual.set(genome)
    max_attempts = 100
    attempts = 0
    # Make sure we try the same mutation a few times before giving up
    # otherwise we end up just doing the easiest mutations like adding and deleting
    max_attempts_per_mutation = 20
    attempts_for_mutation = 0
    mutation = 0.0
    valid_mutation_found = False
    while (not valid_mutation_found or \
           check_validity and not mutated_individual.is_valid(locked_tree, locked_mask) or \
           mutated_individual.bt == [] or \
           mutated_individual.bt == genome) and\
           attempts < max_attempts:
        if valid_mutation_found:
            mutated_individual.set(genome) # Reset to original
        index = random.randint(0, len(genome) - 1)
        if attempts_for_mutation >= max_attempts_per_mutation:
            attempts_for_mutation = 0
        if attempts_for_mutation == 0:
            mutation = random.random()

        if mutation < p_delete:
            valid_mutation_found = mutated_individual.delete_node(index)
        elif mutation < p_delete + p_add:
            nodes_added = mutated_individual.add_node(index, p_leaf)
            if nodes_added > 0:
                valid_mutation_found = True
            else:
                valid_mutation_found = False
        elif mutation < p_delete + p_add + p_parameter:
            valid_mutation_found = mutated_individual.change_parameters(index)
        elif mutation < p_delete + p_add + p_parameter + p_replace:
            valid_mutation_found = mutated_individual.replace_parent_with_subtree(index)
        elif mutation < p_delete + p_add + p_parameter + p_replace + p_swap:
            valid_mutation_found = mutated_individual.swap_siblings(index)
        else:
            valid_mutation_found = mutated_individual.change_node(index, p_leaf)

        # Close and trim bt accordingly to the change
        if valid_mutation_found:
            mutated_individual.close()
        attempts += 1
        attempts_for_mutation += 1

    if attempts >= max_attempts and\
       (not valid_mutation_found or \
        check_validity and not mutated_individual.is_valid(locked_tree, locked_mask) or mutated_individual.bt == genome):
        mutated_individual = behavior_tree.BT([], behavior_lists)
        valid_mutation_found = False

    return mutated_individual.bt, valid_mutation_found

def trim_genome(genome: List[ParameterizedNode], behavior_lists: BehaviorLists):
    """Trim the genome to remove unnecessary nodes. This can sometimes invalidate the genome. If so, an empty list is returned."""
    trimmed_genome = behavior_tree.BT([], behavior_lists)
    trimmed_genome.set(genome)
    trimmed_genome.trim()
    if not trimmed_genome.is_valid():
        return []
    return trimmed_genome.bt


def crossover_genome(
    genome1: List[ParameterizedNode],
    genome2: List[ParameterizedNode],
    behavior_lists: BehaviorLists,
    replace: bool = True,
    locked_tree=None,
    locked_mask=None
) -> Tuple[List[ParameterizedNode], List[ParameterizedNode]]:
    # pylint: disable=too-many-branches, too-many-locals
    """Do crossover between genomes at random points."""
    bt1 = behavior_tree.BT(genome1, behavior_lists)
    bt2 = behavior_tree.BT(genome2, behavior_lists)
    offspring1 = behavior_tree.BT([], behavior_lists)
    offspring2 = behavior_tree.BT([], behavior_lists)

    if bt1.is_valid(locked_tree, locked_mask) and bt2.is_valid(locked_tree, locked_mask):
        max_attempts = 100
        attempts = 0
        found = False
        while not found and attempts < max_attempts:
            offspring1.set(bt1.bt)
            offspring2.set(bt2.bt)
            cop1 = -1
            cop2 = -1
            if len(genome1) == 1:
                cop1 = 0  # Change whole tree
            else:
                while not offspring1.is_subtree(cop1):
                    cop1 = random.randint(1, len(genome1) - 1)
            if len(genome2) == 1:
                cop2 = 0  # Change whole tree
            else:
                while not offspring2.is_subtree(cop2):
                    cop2 = random.randint(1, len(genome2) - 1)

            if replace:
                offspring1.swap_subtrees(offspring2, cop1, cop2)
            else:
                subtree1 = offspring1.get_subtree(cop1)
                subtree2 = offspring2.get_subtree(cop2)
                if len(genome1) == 1:
                    index1 = random.randint(0, 1)
                else:
                    index1 = random.randint(1, len(genome1) - 1)
                if len(genome2) == 1:
                    index2 = random.randint(0, 1)
                else:
                    index2 = random.randint(1, len(genome2) - 1)
                offspring1.insert_subtree(subtree2, index1)
                offspring2.insert_subtree(subtree1, index2)

            attempts += 1
            if offspring1.is_valid(locked_tree, locked_mask) and offspring2.is_valid(locked_tree, locked_mask):
                found = True
        if not found:
            offspring1.set([])
            offspring2.set([])

    return offspring1.bt, offspring2.bt


def get_parameters(genome):
    """ Returns all float parameter values from the nodes and sets print_floats to False """
    parameters = {}
    for node in genome:
        if isinstance(node, ParameterizedNode):
            node.print_floats = False
            parameters = parameters | node.get_parameters()
    return parameters


def set_print_floats(genome, print_floats):
    """ Sets print_floats for every node in genome """
    for node in genome:
        if isinstance(node, ParameterizedNode):
            node.print_floats = print_floats
