"""Interfaces to py_trees from behavior tree strings."""

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
import time
from typing import Any, List

from behaviors.common_behaviors import get_node
from behaviors.behavior_tree import BT
import py_trees as pt

@dataclass
class PyTreeParameters:
    """Data class for parameters for the PyTree run."""

    behavior_lists: Any = None   # Lists of the types of behaviors
    max_ticks: int = 200         # Maximum number of ticks to run
    max_time: float = 10000.0    # Maximum time ins s to run
    max_fails: int = 1           # Maximum number of failure states before breaking
    min_time_tick: float = 0.0   # Minimum time per tick if not handled by the communication
    successes_required: int = 2  # Number of success states required before breaking
    show_world: bool = False     # Animate the run
    verbose: bool = False        # Extra prints


class PyTree(pt.trees.BehaviourTree):
    """A class containing a behavior tree. Inherits from the py tree BehaviorTree class."""

    def __init__(
        self,
        node_list: List,
        parameters: Any = None,
        world_interface: Any = None,
        root: Any = None
    ):
        if parameters is not None:
            self.par = parameters
        else:
            self.par = PyTreeParameters()

        self.behavior_lists = self.par.behavior_lists
        self.world_interface = world_interface
        self.ticks = 0
        self.straight_fails = 0
        self.successes = 0

        self.failed = False
        self.success = False
        self.timeout = False

        if root is not None:
            self.root = root
            self.bt = self.get_bt_from_root()
        else:
            self.bt = BT(node_list, self.par.behavior_lists)
            self.root, has_children = get_node(
                node_list[0], world_interface, verbose=self.par.verbose)
            node_list.pop(0)
            if has_children:
                PyTree.create_from_list(node_list, self.root, self.behavior_lists, self.world_interface, self.par.verbose)

        self.length = None
        self.depth = None

        super().__init__(root=self.root)


    def get_bt_from_root(self) -> BT:
        """
        Return bt string from py tree root by cleaning the ascii tree from py trees.

        Not complete or beautiful by any means but works for many trees.
        """
        string = pt.display.ascii_tree(self.root)
        string = string.replace('[o]', '')
        string = string.replace('[-]', '')
        string = string.replace('{o}', '')
        string = string.replace('{-}', '')
        string = string.replace('\t', '')
        string = string.replace('-->', '')
        string = string.replace('\x1b[0m', '')
        string = string.replace('\x1b[1m', '')
        string = string.replace('Fallback', 'f(')
        string = string.replace('Sequence', 's(')
        bt = string.split('\n')
        bt = bt[:-1]  # Remove empty element because of final newline

        prev_leading_spaces = 999999
        for i in range(len(bt) - 1, -1, -1):
            leading_spaces = len(bt[i]) - len(bt[i].lstrip(' '))
            bt[i] = bt[i].lstrip(' ')
            if leading_spaces > prev_leading_spaces:
                for _ in range(round((leading_spaces - prev_leading_spaces) / 4)):
                    bt.insert(i + 1, ')')
            prev_leading_spaces = leading_spaces

        for i, node in enumerate(bt):
            bt[i] = node.replace('  "', ' "') # Remove extra spaces in some nodes before objects
        bt_obj = BT(bt, self.par.behavior_lists)
        bt_obj.close()

        return bt_obj

    def get_length(self):
        """Get length of the behavior tree."""
        if self.length is None:
            self.length = self.bt.length()
        return self.length

    def get_depth(self):
        """Get depth of the behavior tree."""
        if self.depth is None:
            self.depth = self.bt.depth()
        return self.depth

    @staticmethod
    def create_from_list(
        node_list: List,
        node: Any,
        behavior_lists: Any,
        world_interface: Any,
        node_index: int = 0,
        verbose: bool = False
    ) -> pt.composites.Composite:
        """Recursive function to generate the tree from a list."""
        if node is None:
            node, _ = behavior_lists.get_node(
                node_list[0], world_interface, node_index, verbose)
            node_list.pop(0)

        while len(node_list) > 0:
            if node_list[0] == ')':
                node_list.pop(0)
                return (node, node_index)

            node_index += 1
            new_node, has_children = behavior_lists.get_node(
                node_list[0], world_interface, node_index, verbose)
            node_list.pop(0)
            if has_children:
                # Node is a control node or decorator with children.
                # Add subtree via string and then add to parent
                new_node, node_index = PyTree.create_from_list(node_list, new_node, behavior_lists, world_interface, node_index, verbose)
                node.add_child(new_node)
            else:
                # Node is a leaf/action node - add to parent, then keep looking for siblings
                node.add_child(new_node)

        # This return is only reached if there are too few up nodes
        return (node, node_index)

    def reset_counters(self):
        """ Resets tick counters etc."""
        self.ticks = 0
        self.straight_fails = 0
        self.successes = 0

    def run_bt(self):
        """Run the behavior tree."""
        self.reset_counters()
        status_ok = True

        start = time.time()
        last_feedback_time = 0
        while status_ok:
            if time.time() - last_feedback_time < self.par.min_time_tick:
                time.sleep(self.par.min_time_tick - (time.time() - last_feedback_time))
            status_ok = self.step_bt()
            last_feedback_time = time.time()

            if status_ok:
                if time.time() - start > self.par.max_time:
                    status_ok = False
                    print('Max time expired')

        if self.par.verbose:
            print('Total episode ticks: ', self.ticks)
            print('Total episode time: ', time.time() - start)

    def step_bt(self):
        """Step the BT one step."""
        status_ok = True

        if (self.root.status is not pt.common.Status.FAILURE or
                self.straight_fails < self.par.max_fails) and\
              (self.root.status is not pt.common.Status.SUCCESS or
                self.successes < self.par.successes_required) and\
                self.ticks < self.par.max_ticks:

            status_ok = self.world_interface.get_feedback()  # Wait for connection

            if status_ok:
                if self.par.verbose:
                    print('Tick', self.ticks)
                self.root.tick_once()
                self.world_interface.send_references()

                self.ticks += 1
                if self.root.status is pt.common.Status.SUCCESS:
                    self.successes += 1
                else:
                    self.successes = 0

                if self.root.status is pt.common.Status.FAILURE:
                    self.straight_fails += 1
                else:
                    self.straight_fails = 0
        else:
            status_ok = False

        if self.ticks >= self.par.max_ticks:
            self.timeout = True
            status_ok = False
        if self.straight_fails >= self.par.max_fails:
            self.failed = True
            status_ok = False
        if self.successes >= self.par.successes_required:
            self.success = True
            status_ok = False
        return status_ok

    def save_fig(
        self,
        path: str,
        name: str = 'Behavior tree',
        static: bool = True,
        blackboard: bool = False,
        save_png: bool = True,
        save_svg: bool = True
    ):
        """Save the tree as a figure."""
        pt.display.render_dot_tree(
            self.root,
            name=name,
            target_directory=path,
            with_blackboard_variables=blackboard,
            static=static,
            save_png=save_png,
            save_svg=save_svg
        )

if __name__ == '__main__':
    from behaviors.behavior_lists import BehaviorLists
    parameters = PyTreeParameters()
    parameters.behavior_lists = BehaviorLists()
    #pytree = PyTree(['s(', 'f(', 'Condition 1?', 'Action 1!', ')', 'Action 2!', ')', ')'], parameters)
    #pytree = PyTree(['s(', 'Action 3!', 'f(', 'Condition 4?', 'Action 4!', ')', ')', ')'], parameters)
    #pytree = PyTree(['s(', 'f(', 'Condition 1?', 'Action 1!', ')', 'Action 3!', 'f(', 'Condition 4?', 'Action 4!', ')', ')', ')'], parameters)
    #pytree = PyTree(['s(', 'f(', 'Condition 1?', 'Action 1!', ')', 'f(', 'Condition 4?', 'Action 4!', ')', ')', ')'], parameters)
    pytree = PyTree(['s(', 'f(', '"green cube" in "bowl"?', 's(', 'f(', 'grasped "green cube"?', 's(', 'move to "green cube" (-0.4, -0.1) 0.0!', 'grasp "green cube"!', ')', ')',
                     'place "green cube" in "bowl"!', ')', ')', 'f(', '"red cube" at pos "yellow cube" (0.0, 0.0, 0.06) 0.0?', 's(', 'f(', 'grasped "red cube"?', 
                     's(', 'move to "red cube" (-0.2, -0.4) -1.57!', 'grasp "red cube"!', ')', ')', 'move to "yellow cube" (-0.4, 0.0) 0.0!', 
                     'place "red cube" at "yellow cube" (0.0, 0.0, 0.06) 0.0!', ')', ')', 'f(', '"blue cube" at pos "red cube" (0.0, 0.0, 0.06) 0.0?', 's(', 'f(', 'grasped "blue cube"?', 
                     'grasp "blue cube"!', ')', 'place "blue cube" at "red cube" (0.0, 0.0, 0.06) 0.0!', ')', ')', ')'], parameters)
    

    pytree.save_fig('./', 'crossover_after_no_replace')
