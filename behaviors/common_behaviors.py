# pylint: disable=broad-exception-raised
"""Implementing various common py trees behaviors."""

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
import pickle
import random
from typing import Any, Tuple
from dataclasses import dataclass
from dataclasses import field
from enum import IntEnum
import string
import numpy as np

import py_trees as pt

class ParameterTypes(IntEnum):
    """Define the parameter types."""

    LIST = 0  # Choice from a list of values
    POSITION = 1  # A position consists of three values, x y and z
    XY_POSITION = 2 # An xy position consists of two values, x and y
    INTEGER = 3
    FLOAT = 4
    STRING = 5  # Used to describe object targets semantically
    TUPLE = 6  # Used for storing other parameters that don't fall in previous cases

def fast_copy(obj: Any) -> Any:
    """ Return a fast deep copy of a nested object, like a behavior """
    return pickle.loads(pickle.dumps(obj))

def random_range(min_value: int, max_value: int, step: int) -> int:
    """
    Return a value from random range with some checks for step.

    Also includes max in the range unlike randrange.
    """
    if step == 0:
        return min_value
    return random.randrange(min_value, max_value + step, step)


def random_range_float(min_value, max_value, step):
    """
    Gives a float in random range with discretized steps
    Adding 0 avoids representing 0 as -0.0
    """
    if step == 0:
        return min_value
    n = 1 / step
    return np.round(np.random.randint(min_value * n, (max_value + step) * n) * step, 3) + 0


@dataclass
class NodeParameter():
    """Define a parameter for a parameterized node and how to handle it."""

    list_of_values: list = field(default_factory=list)
    min: Any = None
    max: Any = None
    step: Any = None
    placement: int = -1  # Placement within string, just for readability
    data_type: Any = ParameterTypes.LIST
    value: Any = None  # Current value of this parameter
    random_step: bool = False  # Whether to randomize with random step instead of complete reinitialization
    standard_deviation: Any = 1  # Standard deviation of random step length
    use_prior: bool = False  # Current value and standard_deviation can be used as prior

    def is_same(self, other: 'NodeParameter', value_diff_ok=True, categorical_value_diff_ok=False,
                check_list_of_values=False, check_properties=False) -> bool:
        """
        Check if this parameter is the same as another parameter.
        Possible to allow value differences for some or all types
        """
        if self.data_type != other.data_type:
            return False
        if self.data_type == ParameterTypes.LIST:
            if not value_diff_ok or not categorical_value_diff_ok:
                if self.value != other.value:
                    return False
            if check_list_of_values and self.list_of_values != other.list_of_values:
                return False
        elif self.data_type == ParameterTypes.INTEGER or \
             self.data_type == ParameterTypes.FLOAT or \
             self.data_type == ParameterTypes.POSITION or \
             self.data_type == ParameterTypes.XY_POSITION:
            if not value_diff_ok and self.value != other.value:
                return False
            if check_properties:
                if self.min != other.min or self.max != other.max or self.step != other.step or \
                self.random_step != other.random_step or self.standard_deviation != other.standard_deviation or \
                self.use_prior != other.use_prior:
                    return False
        elif self.data_type == ParameterTypes.STRING or self.data_type == ParameterTypes.TUPLE:
            if not value_diff_ok and self.value != other.value:
                return False

        if self.placement != other.placement:
            return False

        return True

    def set_default_value(self):
        """ Set parameter to default value """
        if self.data_type == ParameterTypes.LIST:
            self.value = self.list_of_values[0]
        elif self.data_type == ParameterTypes.INTEGER or self.data_type == ParameterTypes.FLOAT:
            if self.min <= 0 and self.max >= 0:
                self.value = 0
            else:
                self.value = self.min
        elif self.data_type == ParameterTypes.POSITION:
            values = [0, 0, 0]
            for i in range(3):
                if self.min[i] <= 0 and self.max[i] >= 0:
                    values[i] = 0
                else:
                    values[i] = self.min[i]
            self.value = tuple(values)
        elif self.data_type == ParameterTypes.XY_POSITION:
            values = [0, 0]
            for i in range(2):
                if self.min[i] <= 0 and self.max[i] >= 0:
                    values[i] = 0
                else:
                    values[i] = self.min[i]
            self.value = tuple(values)

    def randomize_value(self):
        """Give the parameter a random value within the constraints."""
        if self.data_type == ParameterTypes.LIST:
            self.value = random.choice(self.list_of_values)
        elif self.data_type == ParameterTypes.INTEGER:
            self.value = random_range(self.min, self.max, self.step)
        elif self.data_type == ParameterTypes.POSITION or self.data_type == ParameterTypes.XY_POSITION:
            if isinstance(self.min[0], int):  # Integer values
                if self.data_type == ParameterTypes.POSITION:
                    self.value = (random_range(self.min[0], self.max[0], self.step[0]),
                                random_range(self.min[1], self.max[1], self.step[1]),
                                random_range(self.min[2], self.max[2], self.step[2]))
                else:
                    self.value = (random_range(self.min[0], self.max[0], self.step[0]),
                                random_range(self.min[1], self.max[1], self.step[1]))
            else:
                n_values = 3 if self.data_type == ParameterTypes.POSITION else 2
                if self.value is None:
                    self.value = [0.0] * n_values
                else:
                    self.value = list(self.value)
                for i in range(n_values):
                    if self.step[i] == 0 or self.step[i] is None:
                        self.value[i] = self.min[i]
                    elif self.random_step:
                        self.value[i] += np.random.normal(scale=self.standard_deviation)
                        self.value[i] = max(min(self.value[i], self.max[i]), self.min[i])
                        self.value[i] = np.round(np.round(self.value[i] / self.step[i], 0) *
                                                 self.step[i], 3) + 0  # Multiple of step
                    else:
                        self.value[i] = random_range_float(self.min[i], self.max[i], self.step[i])
                self.value = tuple(self.value)
        elif self.data_type == ParameterTypes.FLOAT:
            if self.step == 0 or self.step is None:
                self.value = self.min
            elif self.random_step:
                if not self.value:
                    self.value = 0.0

                self.value += np.random.normal(scale=self.standard_deviation)
                self.value = max(min(self.value, self.max), self.min)
                self.value = np.round(np.round(self.value / self.step, 0) * self.step, 3) + 0  # Multiple of step
            else:
                self.value = random_range_float(self.min, self.max, self.step)
        elif self.data_type == ParameterTypes.STRING:
            self.value = ''.join(random.choices(
                string.ascii_lowercase + string.digits, k=5))
        else:
            raise Exception('Unknown data_type: ', self.data_type)


class ParameterizedNode():
    """ A parameterized node is a node with parameters and how to handle those parameters """

    def __init__(
        self,
        name: str,
        behavior: Any = None,
        parameters: dict = None,
        condition: bool = True,
        default_object_positions: Any = None
    ):
        # pylint: disable=too-many-arguments
        self.name = name
        self.behavior = behavior
        self.parameters = fast_copy(parameters) if parameters else {}
        self.condition = condition
        self.default_object_positions = default_object_positions if default_object_positions else {}
        self.preplanned_subtree = None
        self.print_floats = True

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ParameterizedNode):
            return self.name == other.name and \
                self.parameters == other.parameters and \
                self.condition == other.condition
        elif isinstance(other, Goal):
            if self.condition and self.behavior == other.behavior:
                for parameter in self.parameters.items():
                    if parameter[1].value != other.parameters[parameter[0]]:
                        return False
                return True

        # don't attempt to compare against unrelated types
        return False

    def is_same(self, other: Any) -> bool:
        """ Check if this node is the same as another node of same type, but is more allowing than __eq__ """
        if isinstance(other, ParameterizedNode) and \
            self.name == other.name and \
            self.condition == other.condition:
            for name, parameter in self.parameters.items():
                if name not in other.parameters:
                    return False
                if not parameter.is_same(other.parameters[name], value_diff_ok=False,
                                        categorical_value_diff_ok=False,
                                        check_list_of_values=False, check_properties=False):
                    return False
            return True
        return False

    def __repr__(self) -> str:
        """Return the string version of the node."""
        return self.to_string()

    def check_string_match(self, node_string):
        """ Check if the string description of the node matches this node """
        try:
            return self.behavior.check_string_match(node_string)
        except AttributeError:
            return self.name in node_string

    def get_tooltip(self):
        """ Returns tooltip of the behavior """
        if hasattr(self.behavior, "get_tooltip"):
            return self.behavior.get_tooltip()
        return ""

    def get_parameters(self):
        """Return parameter values."""
        parameters = {}
        if self.parameters:
            for name, parameter in self.parameters.items():
                if hasattr(parameter, "value"):
                    parameters[name] = parameter.value
                else:
                    parameters[name] = parameter
        return parameters

    def set_parameters_from_string(self, node_descriptor):
        """ Set parameter values of the node by parsing a string """
        parsed_parameters = self.behavior.parse_parameters(node_descriptor)
        for name, parameter in parsed_parameters.items():
            self.parameters[name].value = parameter

    def set_default_parameter_values(self):
        """ Set default parameter values for all parameters """
        for name, _ in self.parameters.items():
            self.set_default_parameter_value(name, no_get_from_behavior=True)

    def set_default_parameter_value(self, name: str, no_get_from_behavior=False):
        """ Set default parameter value for a specific parameter """
        if name in self.parameters:
            if not no_get_from_behavior and hasattr(self.behavior, "get_default_parameter_value") and \
                self.default_object_positions:

                self.parameters[name].value = self.behavior.get_default_parameter_value(name,
                                                                                        self.parameters,
                                                                                        self.default_object_positions)
                if self.parameters[name].value is None:
                    self.parameters[name].set_default_value()
            else:
                self.parameters[name].set_default_value()
        else:
            print("Error: Parameter not found")

    def randomize_parameters(self, randomize_list_type=True):
        """ Randomize node parameters."""
        if self.parameters:
            for name, parameter in self.parameters.items():  # pylint: disable=not-an-iterable
                parameter_valid = False
                while not parameter_valid:
                    parameter_valid = True
                    if isinstance(parameter, NodeParameter):
                        if randomize_list_type or parameter.data_type != ParameterTypes.LIST:
                            parameter.randomize_value()
                        if hasattr(self.behavior, "is_parameter_valid"):
                            parameter_valid = self.behavior.is_parameter_valid(self.parameters, name)

    def to_string(self) -> str:
        """Return string representation of node for printing/logging/hashing."""
        if hasattr(self.behavior, "to_string"):
            return self.behavior.to_string_static(self.get_parameters())
        else:
            string_node = self.name
            if self.parameters:
                for _, parameter in self.parameters.items():  # pylint: disable=not-an-iterable
                    if isinstance(parameter, NodeParameter):
                        parameter_string = ''
                        placement = parameter.placement

                        if self.print_floats:
                            parameter_string += str(parameter.value)

                            if placement == 0:
                                string_node = ''.join((parameter_string, ' ', string_node))
                            elif placement == -1:
                                string_node = ''.join((string_node, ' ', parameter_string))
                            else:
                                string_node = string_node[:placement] +\
                                    ' ' + parameter_string + ' ' + \
                                    string_node[placement:]
                        else:
                            string_node += parameter_string
            if self.condition:
                string_node += '?'
            else:
                string_node += '!'
            return string_node.strip()

    def set_behavior(self, behavior: Any):
        """Set the associated behavior."""
        self.behavior = behavior

    def ok_after(self, other):
        """ Check if the other behavior is ok after this behavior """
        if isinstance(other, ParameterizedNode) and hasattr(self.behavior, "ok_after"):
            return self.behavior.ok_after(self.parameters, other.behavior, other.parameters)
        return True

    def get_preplanned_subtree(self):
        """
        Get the preplanned subtree for this node. 
        """
        negated = self.parameters.get("not", None)
        if negated is None or not negated.value:
            return self.preplanned_subtree
        return []

    def preplan_subtree(self, behavior_lists):
        """
        Preplan the subtree for this node.
        A preplanned subtree is a subtree that uses task planning logic to replace the node. 
        An action nodes is replaced with a sequence node with the preconditions of the action node
        as the first children, and the action node itself last.
        A condition node is replaced with a fallback node with itself as the first child 
        and then one or more action nodes with the condition node as a postcondition as the subsequent children
        Currently cannot handle multiple possible action nodes with different costs
        """
        self.preplanned_subtree = []
        if self.behavior is not None:
            if self.condition:
                for action_node in behavior_lists.action_nodes:
                    if hasattr(action_node, "behavior"):
                        postconditions = action_node.behavior.get_postcondition_behaviors()
                        if self.behavior in postconditions:
                            self.preplanned_subtree.append(action_node)
                            break
                if self.preplanned_subtree:
                    self.preplanned_subtree.insert(0, self)
                    self.preplanned_subtree.insert(0, behavior_lists.fallback_nodes[0])
            else: # action node
                preconditions = self.behavior.get_precondition_behaviors()
                for precondition in preconditions:
                    for condition_node in behavior_lists.condition_nodes:
                        if hasattr(condition_node, "behavior"):
                            if condition_node.behavior == precondition:
                                self.preplanned_subtree.append(condition_node)
                if self.preplanned_subtree:
                    self.preplanned_subtree.insert(0, behavior_lists.sequence_nodes[0])
                    self.preplanned_subtree.append(self)
        if self.preplanned_subtree:
            self.preplanned_subtree.append(behavior_lists.up_node[0])

class Goal():
    """ A goal is a node with behavior type and parameters"""

    def __init__(
        self,
        behavior: Any = None,
        parameters: dict = None
    ):
        self.behavior = behavior
        self.parameters = fast_copy(parameters) if parameters else {}

def get_node(
    node_descriptor: Any = None,
    world_interface: Any = None,
    index: int = 0,
    verbose: bool = False
) -> Tuple[Any, bool]:
    """Return a py_trees behavior or composite given the descriptor."""
    has_children = False

    if isinstance(node_descriptor, ParameterizedNode):
        node = node_descriptor.behavior(
            '', node_descriptor.get_parameters(), world_interface, index, verbose)
    else:
        if node_descriptor == 'f(':
            node = pt.composites.Selector('Fallback', memory=False)
            has_children = True
        elif node_descriptor == 'fm(':
            node = pt.composites.Selector('Fallback', memory=True)
            has_children = True
        elif node_descriptor == 'fr(':
            node = RandomSelector('RandomSelector')
            has_children = True
        elif node_descriptor == 's(':
            node = pt.composites.Sequence('Sequence', memory=False)
            has_children = True
        elif node_descriptor == 'sm(':
            node = pt.composites.Sequence('Sequence', memory=True)
            has_children = True
        elif node_descriptor == 'p(':
            node = pt.composites.Parallel(
                name='Parallel',
                policy=pt.common.ParallelPolicy.SuccessOnAll(synchronise=False))
            has_children = True
        else:
            print("Warning: Unrecognized node. Adding generic node instead of: " + str(node_descriptor))
            node = ActionBehavior(node_descriptor, {}, world_interface)

    return node, has_children

class Behavior(pt.behaviour.Behaviour):
    """ The general behavior implementation. """
    def __init__(self, name: str, parameters, world_interface: Any, verbose: bool = False):
        self.world_interface = world_interface
        self.verbose = verbose
        self.negated = parameters.get("not", False)
        self.parameters = parameters.copy()
        super().__init__(name)

    def __eq__(self, other) -> bool:
        if self.name != other.name:
            return False
        for parameter in self.parameters:
            if isinstance(self.parameters[parameter], np.ndarray):
                if not np.array_equal(self.parameters[parameter], other.parameters[parameter]):
                    return False
            else:
                if self.parameters[parameter] != other.parameters[parameter]:
                    return False
        return True

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Standard parameter parsing only looking for target_object and not """
        parameters = {}
        n_marks = 2
        marks = [0] * n_marks
        marks[0] = node_descriptor.find('"')
        for i in range(1, n_marks):
            if marks[i - 1] >= 0:
                marks[i] = node_descriptor.find('"', marks[i - 1] + 1)
            else:
                raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        #parameters["not"] = node_descriptor[0] == "~"

        return parameters

    def get_parameters(self):
        """ Returns parameters of the condition """
        return self.parameters

    @staticmethod
    def common_string_rules(node_string, parameters):
        """ Changes string using common string rules """
        if parameters.get("not", False):
            node_string = ''.join(("~", node_string))

        return node_string

    def check_negated(self, success):
        """ Handle whether the condition should be negated or not """
        return Behavior.check_negated_static(success, self.negated)

    @staticmethod
    def check_negated_static(success, negated):
        """ Handle whether the condition should be negated or not """
        if negated and not success or \
            not negated and success:
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE

    @staticmethod
    def ok_after(parameters, other, other_parameters): # pylint: disable=unused-argument
        """ Check if the other behavior is ok after this behavior """
        return True


class ActionBehavior(Behavior):
    """
    Class template for action behaviors
    """
    def __init__(self, name, parameters, world_interface, max_ticks=50, index=0, verbose=False):
        self.state = None
        self.counter = 0
        self.index = index
        self.max_ticks = max_ticks
        self.require_execution = parameters.get("require_execution", False) #
        self.preconditions = []
        extra_preconditions = False
        if world_interface is not None:
            extra_preconditions = world_interface.extra_preconditions
        for precondition_behavior in self.get_precondition_behaviors(extra_preconditions):
            self.preconditions.append(precondition_behavior('', parameters, world_interface))
        self.postconditions = []
        for postcondition_behavior in self.get_postcondition_behaviors():
            self.postconditions.append(postcondition_behavior('', parameters, world_interface))
        super().__init__(name, parameters, world_interface, verbose)

    def initialise(self) -> None:
        self.counter = 0
        self.state = pt.common.Status.RUNNING

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Standard parameter parsing only looking for target_object and not """
        parameters = {}
        n_marks = 2
        marks = [0] * n_marks
        marks[0] = node_descriptor.find('"')
        for i in range(1, n_marks):
            if marks[i - 1] >= 0:
                marks[i] = node_descriptor.find('"', marks[i - 1] + 1)
            else:
                raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        return parameters

    def update(self) -> None:
        """ Common update function checking counter, and setting last action variable """
        if self.state == pt.common.Status.RUNNING:
            self.counter += 1
            if self.counter > self.max_ticks:
                self.failure("Could not complete action in time")
            else:
                self.world_interface.set_last_action(self.index)
            if self.verbose:
                print(self.name, ':', self.state)

    def success(self) -> None:
        """Set state success."""
        self.state = pt.common.Status.SUCCESS
        if self.verbose:
            print(self.name, ': SUCCESS')

    def failure(self, error_message = '') -> None:
        """Set state failure."""
        self.state = pt.common.Status.FAILURE
        self.world_interface.set_failed_action(self.name)
        self.world_interface.set_error_message(error_message)
        if self.verbose:
            print(self.name, ': FAILURE')
        return self.state

    def cost(self) -> int:
        """Define the cost of the action."""
        return 1

    def get_preconditions(self):
        """ Returns list of preconditions """
        return self.preconditions

    def get_postconditions(self):
        """ Returns list of postconditions """
        return self.postconditions

    @staticmethod
    def get_precondition_behaviors(extra_preconditions=False): #pylint: disable=unused-argument
        """ Returns a list of precondition behaviors """
        return []

    @staticmethod
    def get_postcondition_behaviors():
        """ Returns a list of postcondition behaviors """
        return []

    def has_postcondition_check(self):
        """
        Most behaviors check postconditions first and
        only execute if they are not already fulfilled
        """
        return True

    def terminate(self, _status):
        """ Cleanup after stop """
        self.world_interface.set_manipulation_target(None)

class ComparisonCondition(pt.behaviour.Behaviour):
    """Class template for conditions comparing against constants."""

    def __init__(
        self, name: str,
        parameters: list,
        world_interface: Any,
        _verbose: bool = False
    ):
        self.world_interface = world_interface
        self.larger_than = parameters["larger_than"]
        self.value = float(parameters["value"])
        super().__init__(name)

    def compare(self, variable: Any) -> pt.common.Status:
        """Compare input variable to stored value."""
        if (self.larger_than and variable > self.value) or \
           (not self.larger_than and variable < self.value):
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE


class RandomSelector(pt.composites.Selector):
    """
    Random selector node for py_trees
    """
    def __init__(self, name='RandomSelector', children=None):
        super().__init__(name=name, memory=False, children=children)

    def tick(self):
        """
        Run the tick behaviour for this selector.

        Note that the status of the tick is always determined by its children,
        not by the user customized update function.

        Yields
        ------
            class:`~py_trees.behaviour.Behaviour`: a reference to itself or one of its children.

        """
        self.logger.debug('%s.tick()' % self.__class__.__name__)  # pylint: disable=consider-using-f-string
        # initialise
        if self.status == pt.common.Status.FAILURE or self.status == pt.common.Status.INVALID:
            # selector specific initialization - leave initialise() free for users to
            # re-implement without having to make calls to super()
            self.logger.debug(
                '%s.tick() [!RUNNING->reset current_child]' % self.__class__.__name__)  # pylint: disable=consider-using-f-string
            if len(self.children) > 1:
                # Select one child at random except the child we last tried executing.
                # If self.current_child is None we will choose a child entirely at random.
                self.current_child = random.choice(
                    [child for child in self.children if child is not self.current_child])
            elif len(self.children) == 1:
                # If there is only one child we should always execute it
                self.current_child = self.children[0]
            else:
                self.current_child = None

            # reset the children - don't need to worry since they will be handled
            # a) prior to a remembered starting point, or
            # b) invalidated by a higher level priority

            # user specific initialization
            self.initialise()

        for child in self.children:
            if child is not self.current_child:
                child.stop(new_status=pt.common.Status.SUCCESS)

        # customized work
        self.update()

        # nothing to do
        if not self.children:
            self.current_child = None
            self.stop(pt.common.Status.FAILURE)
            yield self
            return

        # actual work
        previous_children = []
        while len(previous_children) < len(self.children):
            for node in self.current_child.tick():
                yield node
                if node is self.current_child:
                    if node.status == pt.common.Status.RUNNING or\
                       node.status == pt.common.Status.SUCCESS:
                        self.status = node.status
                        yield self
                        return
            previous_children.append(self.current_child)
            children_left = [child for child in self.children if child not in previous_children]
            if len(children_left) > 0:
                # Don't set current_child in last loop so we remember the last
                # child that failed
                self.current_child = random.choice(children_left)
        # all children failed,
        # set failure ourselves and current child to the last bugger who failed us
        self.status = pt.common.Status.FAILURE
        yield self
