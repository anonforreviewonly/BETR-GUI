# pylint: disable=broad-exception-raised
"""Class for handling string representations of behavior trees."""

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
from typing import List, Tuple, Any

from behaviors.behavior_lists import BehaviorLists
from behaviors.common_behaviors import ParameterizedNode, fast_copy


class BT:
    """Class for handling list representations of behavior trees."""

    def __init__(self, bt: List[str], behavior_lists: BehaviorLists):
        """Create a BT."""
        self.bt = bt[:]
        self.behaviors = behavior_lists

    def set(self, bt: List[ParameterizedNode]):
        """Set bt list."""
        self.bt = fast_copy(bt)
        return self

    def random(self, min_length: int, p_leaf: float, locked_tree: Any=None, locked_mask: Any=None) -> List[ParameterizedNode]:
        """
        Create a random bt of at least the given length.

        Tries to follow some of the rules for valid trees to speed up the process.

        Args:
        ----
            length: length of the BT.
            p_leaf: probability to generate a leaf node.

        """
        self.bt = []
        valid = False
        while not valid or self.length() < min_length:
            if min_length == 1:
                self.bt = [self.behaviors.get_random_behavior_node()]
                valid = self.is_valid(locked_tree, locked_mask)
            else:
                self.bt = [self.behaviors.get_random_root_node()]
                while self.length() < min_length:
                    self.add_node(self.length(), p_leaf)

                    if self.behaviors.is_behavior_node(self.bt[-1]):
                        self.bt += [self.behaviors.get_up_node()]

                self.close()
                valid = self.is_valid(locked_tree, locked_mask)
                if valid:
                    self.trim()

        return self.bt

    def is_valid(self, locked_tree=None, locked_mask=None, get_error_string=False, require_behavior=True) -> bool:
        """
        Check if bt is a valid behavior tree.

        Checks are somewhat in order of likelihood to fail.
        """
        # Empty list
        if len(self.bt) <= 0:
            return False if not get_error_string else (False, "Tree is empty")

        # The first element cannot be a leaf if after it there are other elements
        elif len(self.bt) != 1 and (not self.behaviors.is_control_node(self.bt[0]) and \
                                    not self.behaviors.is_root_node(self.bt[0])):
            return False if not get_error_string else (False, "Top node is not a valid root node")
        else:
            has_behavior = False
            for i in range(len(self.bt) - 1):
                # 'up' directly after a control node
                if self.behaviors.is_control_node(self.bt[i]) and\
                self.behaviors.is_up_node(self.bt[i+1]):
                    return False if not get_error_string else (False, "Control node without children")
                # Identical leaf nodes directly after one another - waste,
                elif self.behaviors.is_leaf_node(self.bt[i]):
                    if self.bt[i] == self.bt[i+1]:
                        return False if not get_error_string else \
                            (False, "Identical leaf nodes next to each other: " + self.bt[i].to_string())
                    else:
                        if self.behaviors.is_behavior_node(self.bt[i]):
                            has_behavior = True
                            # condition node after behavior node. Can in some rare cases be more optimal but
                            # is never necessary and makes tree much harder to read.
                            if self.behaviors.is_condition_node(self.bt[i+1]):
                                return False if not get_error_string else (False, "Condition nodes must be placed before action nodes")

                    # Check some rules for behaviors following each other
                    if isinstance(self.bt[i], ParameterizedNode):
                        if self.behaviors.is_behavior_node(self.bt[i]) and \
                            self.bt[i].parameters.get("require_execution", False) and not self.behaviors.is_up_node(self.bt[i+1]):
                            return False if not get_error_string else \
                                (False, self.bt[i].to_string() + " is an action node and must be last sibling")
                        if not self.bt[i].ok_after(self.bt[i+1]):
                            return False if not get_error_string else \
                                (False, self.bt[i+1].to_string() + " cannot be placed after " +  self.bt[i].to_string())
                # check for non-BT elements
                elif not self.behaviors.is_valid_node(self.bt[i]):
                    return False if not get_error_string else (False, "Invalid node: " + self.bt[i].to_string())

            if require_behavior and not has_behavior and not self.behaviors.is_behavior_node(self.bt[-1]):
                return False if not get_error_string else (False, "No leaf node in the tree")

            # Check on the bt depth: to be > 0
            depth = self.depth()
            if (depth < 0) or (depth == 0 and len(self.bt) > 1):
                return False if not get_error_string else (False, "Error in depth calculation")

            if self.behaviors.is_control_node(self.bt[0]):
                fallback_allowed = True
                sequence_allowed = True
                if self.behaviors.is_fallback_node(self.bt[0]):
                    fallback_allowed = False
                elif self.behaviors.is_sequence_node(self.bt[0]):
                    sequence_allowed = False
                if not self.is_subtree_valid(self.bt[1:], fallback_allowed, sequence_allowed):
                    return False if not get_error_string else (False, "Sequences and fallbacks must alternate in the tree")

            if locked_tree is not None and locked_mask is not None:
                if not self.is_locked_tree_part_of_tree(locked_tree, locked_mask):
                    return False if not get_error_string else (False, "Locked tree is not part of the behavior tree")

        return True if not get_error_string else True, ""

    def is_subtree_valid(
        self,
        subtree: List[ParameterizedNode],
        fallback_allowed: bool,
        sequence_allowed: bool
    ) -> bool:
        # pylint: disable=too-many-return-statements, too-many-branches
        """
        Check whether the subtree starting with subtree[0] is valid according to a couple rules.

        1. Fallbacks must not be children of fallbacks.
        2. Sequences must not be children of sequences.
        """
        while len(subtree) > 0:
            node = subtree.pop(0)

            if self.behaviors.is_up_node(node):
                return True
            if node in self.behaviors.atomic_fallback_nodes:
                if not fallback_allowed:
                    return False
            elif node in self.behaviors.atomic_sequence_nodes:
                if not sequence_allowed:
                    return False
            elif self.behaviors.is_control_node(node):
                if self.behaviors.is_fallback_node(node):
                    if fallback_allowed:
                        if not self.is_subtree_valid(subtree, False, True):
                            return False
                    else:
                        return False
                elif self.behaviors.is_sequence_node(node):
                    if sequence_allowed:
                        if not self.is_subtree_valid(subtree, True, False):
                            return False
                    else:
                        return False
                else:
                    if not self.is_subtree_valid(subtree, True, True):
                        return False

        return False

    def is_locked_tree_part_of_tree(self, locked_tree, locked_mask, tree=None, reordering_depth_allowed=0, starting_depth=0):
        """ 
        Check if the locked tree is a part of this tree 
        The locked list is a list of which nodes are locked and need to be checked
        If reordering depth is used, locked subtrees starting at that depth are allowed to be reordered
        Only tested for reordering_depth_allow = 1 or 0
        """
        if len(locked_tree) != len(locked_mask):
            return True #Something is wrong, but allowing the tree has the least consequences

        if tree is None:
            tree = self.bt
        bt_length = len(tree)
        bt_index = 0
        depth_bt = starting_depth
        depth_locked = starting_depth

        if reordering_depth_allowed > 0:
            #Find start of reordering
            for index, node in enumerate(tree):
                if depth_bt == reordering_depth_allowed:
                    bt_index = index
                    break
                if self.behaviors.is_control_node(node):
                    depth_bt += 1
                elif self.behaviors.is_up_node(node):
                    depth_bt -= 1

            locked_index = 0
            while locked_index < len(locked_tree):
                locked_node = locked_tree[locked_index]
                if depth_locked < reordering_depth_allowed:
                    if not self.is_locked_tree_part_of_tree([locked_node],
                                                            locked_mask[locked_index: locked_index + 1],
                                                            tree=tree,
                                                            reordering_depth_allowed=0,
                                                            starting_depth=depth_locked):
                        return False
                if depth_locked == reordering_depth_allowed:# Reordering allowed on this depth level
                    if self.behaviors.is_control_node(locked_node):
                        try:
                            end = self.find_up_node(locked_index, locked_tree) + 1
                        except Exception:
                            end = None # Make sure whole tree is used if missing up
                    else:
                        end = locked_index + 1
                    # Check if the locked subtree is part of the main tree
                    if not self.is_locked_tree_part_of_tree(locked_tree[locked_index:end],
                                                            locked_mask[locked_index:end],
                                                            tree=tree[bt_index:],
                                                            reordering_depth_allowed=0,
                                                            starting_depth=depth_locked):
                        return False
                    locked_index = end
                    if locked_index is None:
                        break # We were missing an up node, so we are done
                else: # Not complete subtree handled so depth changes
                    if self.behaviors.is_control_node(locked_node):
                        depth_locked += 1
                    elif self.behaviors.is_up_node(locked_node):
                        depth_locked -= 1
                    locked_index += 1
        else:
            for locked_index, locked_node in enumerate(locked_tree):
                if locked_mask[locked_index]:
                    while depth_bt != depth_locked or tree[bt_index] != locked_node:
                        if self.behaviors.is_control_node(tree[bt_index]):
                            depth_bt += 1
                        elif self.behaviors.is_up_node(tree[bt_index]):
                            depth_bt -= 1
                        bt_index += 1
                        if bt_index >= bt_length:
                            return False

                if self.behaviors.is_control_node(locked_node):
                    depth_locked += 1
                elif self.behaviors.is_up_node(locked_node):
                    depth_locked -= 1
        return True


    def close(self) -> None:
        """Add missing up nodes at the end, or removes from the end if too many."""
        open_subtrees = 0

        # Make sure tree always ends with up node if starts with control node
        if len(self.bt) > 0:
            if self.behaviors.is_control_node(self.bt[0]) and\
               not self.behaviors.is_up_node(self.bt[len(self.bt)-1]):
                self.bt += self.behaviors.get_up_node()

        for node in self.bt:
            if self.behaviors.is_control_node(node):
                open_subtrees += 1
            elif self.behaviors.is_up_node(node):
                open_subtrees -= 1

        if open_subtrees > 0:
            for _ in range(open_subtrees):
                self.bt += self.behaviors.get_up_node()
        elif open_subtrees < 0:
            for _ in range(-open_subtrees):
                # Do not remove the very last node, and only up nodes
                for j in range(len(self.bt) - 2, 0, -1):
                    # pragma: no branch, we will always find an up
                    if self.behaviors.is_up_node(self.bt[j]):
                        self.bt.pop(j)
                        break

    def trim(self) -> None:
        """
        Remove control nodes with only one child.
        If child is identical control node, remove child """
        for index in range(len(self.bt) - 1, -1, -1):
            if self.behaviors.is_control_node(self.bt[index]):
                children = self.find_children(index)
                if len(children) <= 1:
                    up_node_index = self.find_up_node(index)
                    self.bt.pop(up_node_index)
                    self.bt.pop(index)
                else:
                    for child_index in range(len(children) - 1, -1, -1):
                        if self.bt[index] == self.bt[children[child_index]]:
                            # Parent and child will be identical control nodes,
                            # child can be removed
                            up_node_index = self.find_up_node(children[child_index])
                            self.bt.pop(up_node_index)
                            self.bt.pop(children[child_index])

    def depth(self) -> int:
        """Return depth of the bt."""
        depth = 0
        max_depth = 0

        for i, node in enumerate(self.bt):
            if self.behaviors.is_control_node(node):
                depth += 1
                max_depth = max(depth, max_depth)
            elif self.behaviors.is_up_node(node):
                depth -= 1
                if (depth < 0) or (depth == 0 and i is not len(self.bt) - 1):
                    return -1

        if depth != 0:
            return -1

        return max_depth

    def length(self) -> int:
        """Count number of nodes in bt. Doesn't count up characters."""
        length = 0
        for node in self.bt:
            if not self.behaviors.is_up_node(node):
                length += 1
        return length

    def n_sequential_actions(self) -> int:
        """Count number of actions that follow directly after another action."""
        count = 0
        for i, node in enumerate(self.bt):
            if i > 0 and self.behaviors.is_action_node(node) and self.behaviors.is_action_node(self.bt[i - 1]):
                count += 1
        return count

    def random_node(self, p_leaf: float) -> ParameterizedNode:
        """Return a random node."""
        if random.random() > p_leaf:
            return self.behaviors.get_random_control_node()
        return self.behaviors.get_random_leaf_node()

    def change_node(
        self,
        index: int,
        p_leaf: float,
        new_node: str = None
    ) -> None:
        """Change node at index."""
        if self.behaviors.is_up_node(self.bt[index]):
            return False

        if new_node is None:
            new_node = self.random_node(p_leaf)

        if self.behaviors.is_control_node(self.bt[index]):
            # Change control node to leaf node, remove whole subtree
            if self.behaviors.is_leaf_node(new_node):
                self.delete_node(index)
                self.add_node(index, p_leaf, new_node)
            elif self.behaviors.root_nodes is None and \
                (self.behaviors.is_sequence_node(self.bt[index]) and self.behaviors.is_fallback_node(new_node) or
                 self.behaviors.is_fallback_node(self.bt[index]) and self.behaviors.is_sequence_node(new_node)):
                # If we want to switch one sequence to fallback or vice versa, we have to switch all for tree to be valid
                self.switch_sequences_fallbacks()
            else:
                self.bt[index] = new_node
        # Change leaf node to control node. Add up and extra condition/behavior node child
        elif self.behaviors.is_control_node(new_node) and\
                self.behaviors.is_leaf_node(self.bt[index]):
            old_node = self.bt[index]
            self.bt[index] = new_node
            if self.behaviors.is_behavior_node(old_node):
                self.add_node(index + 1, p_leaf=1.0)
                self.bt.insert(index + 2, old_node)
            else:  # condition node
                self.bt.insert(index + 1, old_node)
                self.add_node(index + 2, p_leaf=1.0, new_node=self.behaviors.get_random_behavior_node())
            self.bt.insert(index + 3, self.behaviors.get_up_node())
        else:
            self.bt[index] = new_node
        return True

    def add_node(
        self,
        index: int,
        p_leaf: float,
        new_node: ParameterizedNode = None
    ) -> None:
        """
        Add new node at index.
        If adding control node, also add two children
        If there are preplanned subtrees for leaf nodes, add those recursively
        Returns an int of number of nodes added
        """
        nodes_added = 0
        if new_node is None:
            new_node = self.random_node(p_leaf)
        if self.behaviors.is_control_node(new_node):
            if index == 0:
                # Adding new control node to encapsulate entire tree
                self.bt.insert(index, new_node)
                self.bt.append(self.behaviors.get_up_node())
                return 2
            else:
                self.bt.insert(index, new_node)
                nodes_added += 1
                nodes_added += self.add_node(index + nodes_added, p_leaf, self.behaviors.get_random_leaf_node())
                nodes_added += self.add_node(index + nodes_added, p_leaf, self.behaviors.get_random_behavior_node())
                self.bt.insert(index + nodes_added, self.behaviors.get_up_node())
                nodes_added += 1
                return nodes_added
        else:
            if hasattr(new_node, 'get_preplanned_subtree'):
                preplanned_subtree = new_node.get_preplanned_subtree()
                if preplanned_subtree:
                    for _, node in enumerate(preplanned_subtree):
                        if self.behaviors.is_leaf_node(node) and isinstance(node, ParameterizedNode):
                            if node.behavior == new_node.behavior:
                                # The node itself is usually part of it's preplanned subtree.
                                self.bt.insert(index + nodes_added, new_node)
                                nodes_added += 1
                            else:
                                node = fast_copy(node)

                                missing_parameters = []
                                if hasattr(node, "behavior") and hasattr(node.behavior, 'translate_parameters_from_dict'):
                                    translated_parameters = node.behavior.translate_parameters_from_dict(new_node.parameters)
                                    for param in node.parameters:
                                        if param in translated_parameters:
                                            node.parameters[param].value = translated_parameters[param]
                                        else:
                                            missing_parameters.append(param)
                                else:
                                    for param in node.parameters:
                                        if param in new_node.parameters:
                                            node.parameters[param].value = new_node.parameters[param].value
                                        else:
                                            missing_parameters.append(param)
                                for param in missing_parameters:
                                    node.set_default_parameter_value(param)
                                nodes_added += self.add_node(index + nodes_added, p_leaf, node)
                        else:
                            self.bt.insert(index + nodes_added, node)
                            nodes_added += 1
                    return nodes_added
            self.bt.insert(index, new_node)
            return 1

    def add_new_sequential_sibling(self, index, new_node):
        """ 
        Add new sibling to the node at index. If the node at the index does not currently have a sequence node as parent,
        add them both under a new sequence node. New node first.
        """
        parent = self.find_parent(index)
        if parent is not None and self.behaviors.is_sequence_node(self.bt[parent]):
            #Insert before as sibling
            self.bt.insert(index, new_node)
        else:
            #Replace with new sequence node
            old_node = self.bt[index]
            self.bt[index] = self.behaviors.sequence_nodes[0]
            self.bt.insert(index + 1, new_node)
            self.bt.insert(index + 2, old_node)
            self.bt.insert(index + 3, self.behaviors.get_up_node())

    def delete_node(self, index: int) -> None:
        """Delete node at index."""
        if self.behaviors.is_up_node(self.bt[index]):
            return False

        if self.behaviors.is_control_node(self.bt[index]):
            up_node_index = self.find_up_node(index)
            for i in range(up_node_index, index, -1):
                self.bt.pop(i)

        self.bt.pop(index)
        return True

    def find_parent(self, index: int) -> None:
        """Return index of the closest parent to the node at input index."""
        if index == 0:
            return None

        parent = index
        siblings_left = 0
        while parent > 0:
            parent -= 1
            if self.behaviors.is_control_node(self.bt[parent]):
                if siblings_left == 0:
                    return parent
                siblings_left -= 1
            elif self.behaviors.is_up_node(self.bt[parent]):
                siblings_left += 1

        return None

    def find_children(self, index: int) -> List[int]:
        """Find all children to the node at index."""
        children = []
        if self.behaviors.is_control_node(self.bt[index]):
            child = index + 1
            level = 0
            while level >= 0:
                if self.behaviors.is_up_node(self.bt[child]):
                    level -= 1
                elif level == 0:
                    children.append(child)

                if self.behaviors.is_control_node(self.bt[child]):
                    level += 1
                child += 1

        return children

    def find_up_node(self, index: int, tree=None) -> int:
        """Return index of the up node connected to the control node at input index."""
        if tree is None:
            tree = self.bt
        if not self.behaviors.is_control_node(tree[index]):
            raise Exception('Invalid call. Node at index not a control node')

        if index == 0:
            if self.behaviors.is_up_node(tree[len(tree)-1]):
                index = len(tree) - 1
            else:
                raise Exception('Changing invalid BT. Missing up.')
        else:
            level = 1
            while level > 0:
                index += 1
                if index == len(tree):
                    raise Exception('Changing invalid BT. Missing up.')
                if self.behaviors.is_control_node(tree[index]):
                    level += 1
                elif self.behaviors.is_up_node(tree[index]):
                    level -= 1

        return index

    def get_subtree(self, index: int) -> List[ParameterizedNode]:
        """Get subtree starting at index."""
        if self.behaviors.is_control_node(self.bt[index]):
            return self.bt[index: self.find_up_node(index) + 1]
        if self.behaviors.is_leaf_node(self.bt[index]):
            return [self.bt[index]]
        return []

    def get_nth_subtree(self, n: int) -> List[ParameterizedNode]:
        """
        Does a left to right depth first search and returns the nth possible
        executable subtree from a behavior tree.
        The behavior tree should be backward chained, assuming that conditions are not placed to the right of actions.
        Action nodes count as valid subtrees, conditions do not
        Action nodes without parameters are not counted as they don't add parameter complexity
        """
        subtrees = []
        n_subtrees = 0
        current_parent = 0
        last_in_subtree = -1
        current_subtree_has_action = False
        is_full_tree = True  # True if complete tree is returned
        for index, node in enumerate(self.bt):
            if self.behaviors.is_control_node(node):
                if current_subtree_has_action:
                    subtrees.append((current_parent, last_in_subtree))
                current_parent = index
                current_subtree_has_action = False
            elif self.behaviors.is_action_node(node) and node.parameters is not None:
                n_subtrees += 1

                if n_subtrees > n:
                    is_full_tree = False
                    if current_subtree_has_action:
                        subtrees.append((current_parent, last_in_subtree))
                    break
                else:
                    current_subtree_has_action = True
                    last_in_subtree = index
            elif self.behaviors.is_up_node(node):
                current_parent = self.find_parent(current_parent)
                last_in_subtree = index
        if is_full_tree:
            bt = BT(self.bt, self.behaviors)
        else:
            bt = []
            for subtree in subtrees:
                bt += self.bt[subtree[0]:subtree[1] + 1]
            bt = BT(bt, self.behaviors)
        bt.close()
        bt.trim()

        return bt.bt, is_full_tree

    def insert_subtree(self, subtree: List[ParameterizedNode], index: int) -> None:
        """Insert subtree at given index."""
        self.bt[index:index] = subtree

    def swap_subtrees(self, bt2: 'BT', index1: int, index2: int) -> None:
        """Swap two subtrees at given indices."""
        subtree1 = self.get_subtree(index1)
        subtree2 = bt2.get_subtree(index2)

        if subtree1 != [] and subtree2 != []:
            # Remove subtrees that will be replaced
            for _ in range(len(subtree1)):
                self.bt.pop(index1)
            for _ in range(len(subtree2)):
                bt2.bt.pop(index2)

            self.insert_subtree(subtree2, index1)
            bt2.insert_subtree(subtree1, index2)

    def is_subtree(self, index: int) -> bool:
        """Check if node at index is root of a subtree."""
        return bool(0 <= index < len(self.bt) and not self.behaviors.is_up_node(self.bt[index]))

    def same_structure(self, other_bt, categorical_value_diff_ok=False) -> bool:
        """ 
        Checks if the structure of the behavior tree is the same as the other behavior tree,
        only parameter values are allowed to be different 
        Categorical values may not differ if categorical_value_diff_ok is False
        """
        if len(self.bt) != len(other_bt):
            return False

        for i in range(len(self.bt)): #pylint: disable=consider-using-enumerate
            if self.bt[i] != other_bt[i]:
                if isinstance(self.bt[i], ParameterizedNode) and isinstance(other_bt[i], ParameterizedNode):
                    if self.bt[i].behavior != other_bt[i].behavior:
                        return False
                    for parameter_name, parameter in self.bt[i].parameters.items():
                        if hasattr(parameter, 'is_same') and parameter_name in other_bt[i].parameters and \
                            not parameter.is_same(other_bt[i].parameters[parameter_name],
                                                     value_diff_ok=True,
                                                     categorical_value_diff_ok=categorical_value_diff_ok):
                            return False
                else:
                    return False
        return True

    def get_siblings(self, index: int) -> List[int]:
        """Find the siblings of the node at index."""
        siblings = []
        if self.behaviors.is_up_node(self.bt[index]):
            return siblings

        if self.behaviors.is_leaf_node(self.bt[index]):
            right = index + 1
        else:   # control node
            right = self.find_up_node(index) + 1
        while right < len(self.bt) and not self.behaviors.is_up_node(self.bt[right]):
            if self.behaviors.is_leaf_node(self.bt[right]):
                siblings.append(right)
                right += 1
            else:  # control node
                siblings.append(right)
                right = self.find_up_node(right) + 1

        left = index - 1
        while left > 0 and self.behaviors.is_leaf_node(self.bt[left]):
            siblings.append(left)
            left -= 1

        return siblings

    def swap_siblings(self, index: int) -> bool:
        """Swap position with a sibling found by get_siblings()."""
        siblings = self.get_siblings(index)
        if len(siblings) == 0:
            return False
        swap_index = random.choice(siblings)
        subtree_swap = self.get_subtree(swap_index)
        subtree_selected = self.get_subtree(index)

        if swap_index > index:
            self.delete_node(swap_index)
            self.delete_node(index)
            self.insert_subtree(subtree_swap, index)
            self.insert_subtree(
                subtree_selected, swap_index + len(subtree_swap) - len(subtree_selected))
        else:
            self.delete_node(index)
            self.delete_node(swap_index)
            self.insert_subtree(subtree_selected, swap_index)
            self.insert_subtree(subtree_swap, index + len(subtree_selected) - len(subtree_swap))

        return True

    def replace_parent_with_subtree(self, index: int) -> bool:
        """
        Replace the parent subtree with the given subtree.

        This operation might simplify the structure.
        """
        if self.behaviors.is_up_node(self.bt[index]):
            return False
        parent_index = self.find_parent(index)
        if parent_index is not None:
            m_subtree = self.get_subtree(index)
            self.delete_node(parent_index)
            self.insert_subtree(m_subtree, parent_index)
            return True

        return False

    def switch_sequences_fallbacks(self):
        """ Switches all sequences into fallbacks and vice versa """
        for i in range(len(self.bt) - 2):
            if self.behaviors.is_fallback_node(self.bt[i]):
                self.bt[i] = self.behaviors.get_random_sequence_node()
            elif self.behaviors.is_sequence_node(self.bt[i]):
                self.bt[i] = self.behaviors.get_random_fallback_node()

    def change_parameters(self, index: int, attempt: int = 10) -> bool:
        """
        Changes the parameters of a given leaf node.

        The parameters are not allowed to be the same as before.

        Fails if the node at the index is not a leaf node or
        if the node parameters are not set to new values after <attempt> trials
        Return value indicates whether mutation was successful
        """
        node = self.bt[index]
        if self.behaviors.is_leaf_node(node):
            node_parameters = node.get_parameters()
            if not node_parameters: # Node has no parameters
                return False
            while attempt > 0:
                attempt -= 1
                self.bt[index].randomize_parameters(randomize_list_type=False)
                if self.bt[index].get_parameters() != node_parameters:
                    return True

        return False

    def get_edit_distance(
        self,
        second_bt: 'BT',
        first_root: int,
        second_root: int,
        k: float = 0.5
    ):
        """
        Return edit distance.

        Edit distance computed as proposed in: 'Diversity in Genetic Programming: An Analysis
        of Measures and Correlation With Fitness' by Edmund K.B. et.al

        when k=1, returns un-normalized type 1 edit distance
        when k=0.5, returns type 2 edit distance

        Two trees are padded to the same shape the edit distance is the sum of two parts:
        1. root distance: if root is not equal add 1 to the distance
        2. subtree distance: the sum of subtree edit distances weighted by k
        """
        if len(second_bt.bt) > 0:
            distance = 0 if self.bt[first_root] == second_bt.bt[second_root] else 1
        else:
            distance = 1

        first_children, second_children = [], []
        if self.behaviors.is_control_node(self.bt[first_root]):
            first_children.append(first_root + 1)
            first_children += self.get_siblings(first_root + 1)
        if len(second_bt.bt) > 0 and\
           second_bt.behaviors.is_control_node(second_bt.bt[second_root]):
            second_children.append(second_root + 1)
            second_children += second_bt.get_siblings(second_root + 1)

        for i in range(min(len(first_children), len(second_children))):
            distance += k * self.get_edit_distance(
                second_bt, first_root=first_children[i], second_root=second_children[i], k=k)
        empty_tree = BT([], None)
        if len(first_children) > len(second_children):
            for i in range(len(second_children), len(first_children)):
                distance += k * self.get_edit_distance(
                    empty_tree, first_root=first_children[i], second_root=-1, k=k)
        if len(first_children) < len(second_children):
            for i in range(len(first_children), len(second_children)):
                distance += k * second_bt.get_edit_distance(
                    empty_tree, first_root=-1, second_root=second_children[i], k=k)

        return distance

    def get_pseudo_isomorphs_tuple(self) -> Tuple[int, int, int]:
        """
        Return the pseudo isomorphs tuple for computing genotype diversity.

        Tuple definition: <terminals, non terminals, depth>
        """
        leaf_count = 0
        for n in self.bt:
            if self.behaviors.is_leaf_node(n):
                leaf_count += 1
        num_node = len(self.bt)
        num_control = (num_node - leaf_count) // 2
        return (leaf_count, num_control, self.depth())
