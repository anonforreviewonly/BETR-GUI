""" A module containing all the behaviors the robot can use """
#pylint: disable=too-many-lines

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
from enum import IntEnum
import re
import numpy as np
from behaviors.common_behaviors import Behavior, ActionBehavior
from interfaces.base_world_interface import BaseWorldInterface
import py_trees as pt

class AtPos(Behavior):
    """
    Check if object is at position
    """
    def __init__(self, name, parameters, world_interface, _index=0, _verbose=False):
        name = AtPos.to_string_static(parameters)
        super().__init__(name, parameters, world_interface)

    @staticmethod
    def check_string_match(node_string):
        """ Check if the string description of the node matches this node """
        if "at pos" in node_string:
            return True
        return False

    def to_string(self):
        """ Creates a string """
        return AtPos.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = parameters["target_object"]
        node_string += " at pos \n"
        node_string += parameters["relative_object"]
        node_string += " " + str(parameters["offset"])
        if "angle" in parameters:
            node_string += " " + str(parameters["angle"])
        node_string += "?"
        return Behavior.common_string_rules(node_string, parameters)

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Check if target object is at given offset from the relative object.\n" + \
               "The angle parameter is relative the global coordinate system"

    @staticmethod
    def is_parameter_valid(parameters, _name):
        """ Checks if parameter of given name is valid """
        if parameters["target_object"].value is not None and parameters["target_object"].value == parameters["relative_object"].value:
            return False
        return True

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
        parameters = {}
        n_marks = 4
        marks = [0] * n_marks
        marks[0] = node_descriptor.find('"')
        for i in range(1, n_marks):
            if marks[i - 1] >= 0:
                marks[i] = node_descriptor.find('"', marks[i - 1] + 1)
            else:
                raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        parameters["relative_object"] = node_descriptor[marks[2]: marks[3] + 1]
        #parameters["not"] = node_descriptor[0] == "~"
        numbers = list(map(float, re.findall(r'-?\d+\.\d+|-?\d+', node_descriptor)))
        if len(numbers) > 2:
            offset = tuple(numbers[0:3]) #pylint: disable=superfluous-parens
        else:
            offset = tuple([0.0, 0.0, 0.0])
        parameters["offset"] = offset
        if len(numbers) > 3:
            angle = numbers[3]
            parameters["angle"] = angle

        return parameters

    def __eq__(self, other) -> bool:
        if not isinstance(other, AtPos):
            # don't attempt to compare against unrelated types
            return False
        return super().__eq__(other)

    @staticmethod
    def ok_after(parameters, other, other_parameters):
        """ Check if the other behavior is ok after this behavior """
        if other == AtPos:
            if parameters["target_object"] == other_parameters["target_object"]:
                return False
        return True

    @staticmethod
    def compute_fitness(parameters, world_interface, fitness_coeff):
        """ Computes fitness from this behaviors perspective, used if this behavior represents a goal"""
        fitness = 0.0

        object_at_pos = world_interface.object_at(parameters["target_object"],
                                                  parameters["relative_object"],
                                                  parameters["offset"],
                                                  parameters.get("angle", None),
                                                  pos_acc=fitness_coeff.pos_acc,
                                                  angle_acc=fitness_coeff.angle_acc)
        object_grasped = world_interface.get_grasped_object() == parameters["target_object"]
        target_object_position = world_interface.get_position(parameters["target_object"])
        if object_at_pos and object_grasped:
            # Object is grasped, but should be at pos, give penalty anyway from observed position
            target_object_position = world_interface.object_observed_positions.get(parameters["target_object"], np.zeros(3))

        relative_object_position = world_interface.get_position(parameters["relative_object"])
        pos_distance = np.linalg.norm(target_object_position - (relative_object_position + parameters["offset"]))
        pos_distance_root = np.sqrt(pos_distance) #Use sqrt to reduce large distances
        if "angle" in parameters:
            yaw = world_interface.get_yaw(parameters["target_object"])
            angle_distance = world_interface.get_yaw_distance(yaw, parameters["angle"])
        else:
            angle_distance = 0.0
        if not parameters.get("not", False):
            if pos_distance > fitness_coeff.pos_acc:
                fitness += fitness_coeff.position * pos_distance_root
            if angle_distance > fitness_coeff.angle_acc:
                fitness += fitness_coeff.angle * angle_distance
        else:
            # Goal is to stay away, fitness instead a function of how far we are from exceeding the threshold
            if pos_distance < fitness_coeff.pos_acc:
                fitness += fitness_coeff.position * (fitness_coeff.pos_acc - pos_distance_root)

            if angle_distance < fitness_coeff.angle_acc:
                fitness += fitness_coeff.angle * (fitness_coeff.angle_acc - angle_distance)
        return fitness

    @staticmethod
    def check_success(parameters, world_interface):
        """ Check if the condition is successful """
        return Behavior.check_negated_static(world_interface.object_at(parameters["target_object"],
                                                                       parameters["relative_object"],
                                                                       parameters["offset"],
                                                                       parameters.get("angle", None),
                                                                       pos_acc=parameters.get("pos_acc", None),
                                                                       angle_acc=parameters.get("angle_acc", None)) and \
                                             world_interface.get_grasped_object() != parameters["target_object"],
                                             parameters.get("not", False))

    def update(self):
        return AtPos.check_success(self.parameters, self.world_interface)

class InContainer(Behavior):
    """
    Check if object is in container object
    """
    def __init__(self, name, parameters, world_interface, _index=0, _verbose=False):
        name = InContainer.to_string_static(parameters)
        super().__init__(name, parameters, world_interface)

    @staticmethod
    def check_string_match(node_string):
        """ Check if the string description of the node matches this node """
        if ("in " in node_string or len(node_string) < 5 and "in" in node_string) and "place" not in node_string:
            return True
        return False

    def to_string(self):
        """ Creates a string """
        return InContainer.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = parameters["target_object"]
        node_string += " in \n"
        node_string += parameters["relative_object"]
        node_string += "?"
        return Behavior.common_string_rules(node_string, parameters)

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Check if target object is inside the relative object."

    @staticmethod
    def is_parameter_valid(parameters, _name):
        """ Checks if parameter of given name is valid """
        if parameters["target_object"].value is not None and parameters["target_object"].value == parameters["relative_object"].value:
            return False
        return True

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
        parameters = {}
        n_marks = 4
        marks = [0] * n_marks
        marks[0] = node_descriptor.find('"')
        for i in range(1, n_marks):
            if marks[i - 1] >= 0:
                marks[i] = node_descriptor.find('"', marks[i - 1] + 1)
            else:
                raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        parameters["relative_object"] = node_descriptor[marks[2]: marks[3] + 1]

        return parameters

    def __eq__(self, other) -> bool:
        if not isinstance(other, InContainer):
            # don't attempt to compare against unrelated types
            return False
        return super().__eq__(other)

    @staticmethod
    def ok_after(parameters, other, other_parameters):
        """ Check if the other behavior is ok after this behavior """
        if other == InContainer:
            if parameters["target_object"] == other_parameters["target_object"]:
                return False
        return True

    @staticmethod
    def compute_fitness(parameters, world_interface, fitness_coeff):
        """ Computes fitness from this behaviors perspective, used if this behavior represents a goal"""
        fitness = 0.0
        object_in_container = world_interface.object_in(parameters["target_object"], parameters["relative_object"])
        object_grasped = world_interface.get_grasped_object() == parameters["target_object"]
        if not parameters.get("not", False) and (not object_in_container or object_grasped):
            if object_in_container and object_grasped:
                # Object is grasped, but should be in container, give penalty anyway from observed position
                target_object_position = world_interface.object_observed_positions.get(parameters["target_object"], np.zeros(3))
            else:
                target_object_position = world_interface.get_position(parameters["target_object"])
            relative_object_position = world_interface.get_position(parameters["relative_object"])
            pos_distance = np.linalg.norm(target_object_position - relative_object_position)
            pos_distance_root = np.cbrt(pos_distance) #Reduce impact of large distances
            if pos_distance > fitness_coeff.pos_acc:
                fitness += fitness_coeff.position * pos_distance_root

        return fitness

    @staticmethod
    def check_success(parameters, world_interface):
        """ Check if the condition is successful """
        return Behavior.check_negated_static(world_interface.object_in(parameters["target_object"],
                                                                       parameters["relative_object"]) and \
                                             world_interface.get_grasped_object() != parameters["target_object"],
                                             parameters.get("not", False))

    def update(self):
        return InContainer.check_success(self.parameters, self.world_interface)

class BaseAt(Behavior):
    """
    Check if robot base is at position
    """
    def __init__(self, name, parameters, world_interface, _index=0, _verbose=False):
        name = BaseAt.to_string_static(parameters)
        super().__init__(name, parameters, world_interface)

    @staticmethod
    def check_string_match(node_string):
        """ Check if the string description of the node matches this node """
        if "robot at" in node_string:
            return True
        return False

    def to_string(self):
        """ Creates a string """
        return BaseAt.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = "robot at \n"
        node_string += parameters["target_object"]
        node_string += " " + str(parameters["offset"][0:2])
        if "angle" in parameters:
            node_string += " " + str(parameters["angle"])
        node_string += "?"
        return Behavior.common_string_rules(node_string, parameters)

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Check if the robot base is at given offset from the relative object.\n" + \
               "The angle parameter is relative the global coordinate system"

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
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
        numbers = list(map(float, re.findall(r'-?\d+\.\d+|-?\d+', node_descriptor)))
        if len(numbers) > 1:
            offset = tuple(numbers[0:2]) #pylint: disable=superfluous-parens
        else:
            offset = tuple([0.0, 0.0])
        parameters["offset"] = offset
        if len(numbers) > 2:
            angle = numbers[2]
            parameters["angle"] = angle

        return parameters

    def __eq__(self, other) -> bool:
        if not isinstance(other, BaseAt):
            # don't attempt to compare against unrelated types
            return False
        return super().__eq__(other)

    @staticmethod
    def ok_after(parameters, other, other_parameters):
        """ Check if the other behavior is ok after this behavior """
        if other == BaseAt:
            return False
        return True

    @staticmethod
    def compute_fitness(parameters, world_interface, fitness_coeff):
        """ Computes fitness from this behaviors perspective, used if this behavior represents a goal"""
        fitness = 0.0

        robot_base_position = world_interface.robot_base_position
        target_object_position = world_interface.get_position(parameters["target_object"])
        if len(parameters["offset"]) < 3:
            offset = parameters["offset"] + (0.0,) # Add one for z direction since offset is only xy
        else:
            offset = parameters["offset"]
        pos_distance = np.linalg.norm(robot_base_position - (target_object_position + offset))
        pos_distance_root = np.sqrt(pos_distance) #Use sqrt to reduce large distances
        if "angle" in parameters:
            yaw = world_interface.get_yaw(parameters["target_object"])
            angle_distance = world_interface.get_yaw_distance(yaw, parameters["angle"])
        else:
            angle_distance = 0.0
        if not parameters.get("not", False):
            if pos_distance > fitness_coeff.pos_acc_base:
                fitness += fitness_coeff.position * pos_distance_root
            if angle_distance > fitness_coeff.angle_acc:
                fitness += fitness_coeff.angle * angle_distance
        else:
            # Goal is to stay away, fitness instead a function of how far we are from exceeding the threshold
            if pos_distance < fitness_coeff.pos_acc_base:
                fitness += fitness_coeff.position * (fitness_coeff.pos_acc_base - pos_distance_root)

            if angle_distance < fitness_coeff.angle_acc:
                fitness += fitness_coeff.angle * (fitness_coeff.angle_acc - angle_distance)
        return fitness

    @staticmethod
    def check_success(parameters, world_interface):
        """ Check if the condition is successful """
        target_object_position = world_interface.get_position(parameters["target_object"])
        if len(parameters["offset"]) < 3:
            offset = parameters["offset"] + (0.0,) # Add one for z direction since offset is only xy
        else:
            offset = parameters["offset"]
        target_position = target_object_position + offset
        return Behavior.check_negated_static(world_interface.robot_base_at(target_position, parameters["angle"], last_known=True),
                                             parameters.get("not", False))

    def update(self):
        return BaseAt.check_success(self.parameters, self.world_interface)


class BaseNear(Behavior):
    """
    Check if robot base is near position
    """
    pos_acc = 0.9
    def __init__(self, name, parameters, world_interface, _index=0, _verbose=False):
        new_parameters = {}
        if parameters.get("relative_object", None) is not None:
            new_parameters["target_object"] = parameters["relative_object"]
        else:
            new_parameters["target_object"] = parameters["target_object"] #Only use target object
        name = BaseNear.to_string_static(new_parameters)
        super().__init__(name, new_parameters, world_interface)

    @staticmethod
    def check_string_match(node_string):
        """ Check if the string description of the node matches this node """
        if "robot near" in node_string:
            return True
        return False

    def to_string(self):
        """ Creates a string """
        return BaseNear.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = "robot near \n"
        if parameters.get("relative_object", None) is not None:
            node_string += parameters["relative_object"]
        else:
            node_string += parameters["target_object"]
        node_string += "?"
        return Behavior.common_string_rules(node_string, parameters)

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Check if the robot base is near the target object (within 0.9m)."

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
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

    @staticmethod
    def translate_parameters_from_dict(parameters: dict) -> dict:
        """ Translate parameters from a dictionary to the behavior's parameter format """
        translated = {}
        if "relative_object" in parameters:
            translated["target_object"] = parameters["relative_object"].value
        else:
            translated["target_object"] = parameters.get("target_object", None).value
        return translated

    def __eq__(self, other) -> bool:
        if not isinstance(other, BaseNear):
            # don't attempt to compare against unrelated types
            return False
        return super().__eq__(other)

    @staticmethod
    def ok_after(parameters, other, other_parameters):
        """ Check if the other behavior is ok after this behavior """
        if other == BaseNear:
            return False
        return True

    @staticmethod
    def compute_fitness(parameters, world_interface, fitness_coeff):
        """ Computes fitness from this behaviors perspective, used if this behavior represents a goal"""
        fitness = 0.0
        pos_acc = BaseNear.pos_acc
        robot_base_position = world_interface.robot_base_position
        target_object_position = world_interface.get_position(parameters["target_object"])[:]
        pos_difference = robot_base_position - target_object_position
        pos_difference[2] = 0.0  # Ignore z coordinate for position difference
        pos_distance = np.linalg.norm(pos_difference)
        pos_distance_root = np.sqrt(pos_distance) #Use sqrt to reduce large distances

        if not parameters.get("not", False):
            if pos_distance > pos_acc:
                fitness += fitness_coeff.position * pos_distance_root
        else:
            # Goal is to stay away, fitness instead a function of how far we are from exceeding the threshold
            if pos_distance < pos_acc:
                fitness += fitness_coeff.position * (pos_acc - pos_distance_root)
        return fitness

    @staticmethod
    def check_success(parameters, world_interface):
        """ Check if the condition is successful """
        target_object_position = world_interface.get_position(parameters["target_object"])
        return Behavior.check_negated_static(world_interface.get_grasped_object() == parameters["target_object"] or \
                                             world_interface.robot_base_at(target_object_position, 0.0,
                                                                           pos_acc=BaseNear.pos_acc, angle_acc=999, last_known=True),
                                             parameters.get("not", False))

    def update(self):
        return BaseNear.check_success(self.parameters, self.world_interface)

class Grasped(Behavior):
    """
    Check if object is grasped
    """
    def __init__(self, name, parameters, world_interface, _index=0, _verbose=False):
        name = Grasped.to_string_static(parameters)
        super().__init__(name, parameters, world_interface)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Grasped):
            # don't attempt to compare against unrelated types
            return False
        return super().__eq__(other)

    def to_string(self):
        """ Creates a string """
        return Grasped.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = 'grasped ' + parameters["target_object"]
        node_string += "?"
        return Behavior.common_string_rules(node_string, parameters)

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Check if target object currently grasped by the robot."

    @staticmethod
    def ok_after(parameters, other, other_parameters):
        """ Check if the other behavior is ok after this behavior """
        if other == Grasped:
            if parameters["target_object"] == other_parameters["target_object"]:
                return False
        return True

    @staticmethod
    def compute_fitness(parameters, world_interface, fitness_coeff):
        """ Computes fitness from this behaviors perspective, used if this behavior represents a goal"""
        fitness = 0.0
        target_object_grasped = world_interface.get_grasped_object() == parameters["target_object"]
        if parameters.get("not", False) and target_object_grasped or not parameters.get("not", False) and not target_object_grasped:
            fitness += fitness_coeff.grasped

        return fitness

    @staticmethod
    def check_success(parameters, world_interface):
        """ Check if the condition is successful """
        return Behavior.check_negated_static(world_interface.get_grasped_object() == parameters["target_object"],
                                             parameters.get("not", False))

    def update(self):
        return Grasped.check_success(self.parameters, self.world_interface)

class Grasp(ActionBehavior):
    """
    Grasp an object
    """
    class GraspStates(IntEnum):
        """Define the internal states during execution."""
        INIT = 1
        APPROACHING = 2
        POSITIONING = 3
        GRASPING = 4
        LIFTING = 5
        DONE = 6

    def __init__(self, name, parameters, world_interface, index=0, verbose=False):
        name = Grasp.to_string_static(parameters)
        self.target_object = None
        self.target_object_last_known_position = None
        self.grasp_position = None
        self.approach_position = None
        self.orientation = world_interface.get_orientation_from_yaw(0.0)
        self.internal_state = self.GraspStates.INIT
        self.grasping = False
        new_parameters = {}
        new_parameters["target_object"] = parameters["target_object"] #Only use target object
        ActionBehavior.__init__(self, name, new_parameters, world_interface, \
                                max_ticks=20, index=index, verbose=verbose)

    @staticmethod
    def get_precondition_behaviors(extra_preconditions=False):
        """ Returns a list of precondition behaviors """
        if extra_preconditions:
            return [BaseNear]
        return []

    @staticmethod
    def get_postcondition_behaviors():
        """ Returns a list of postcondition behaviors """
        return [Grasped]

    def to_string(self):
        """ Creates a string """
        return Grasp.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = "grasp " + parameters["target_object"]
        node_string += "!"
        return node_string

    @staticmethod
    def check_string_match(node_string):
        """ Check if the string description of the node matches this node """
        if "grasp " in node_string or node_string == "grasp" or node_string == "grasp!":
            return True
        return False

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Grasps the target object if within reach"

    @staticmethod
    def ok_after(parameters, other, other_parameters): # pylint: disable=unused-argument
        """ Check if the other behavior is ok after this behavior """
        if other == Grasp:
            return False
        return True

    def initialise(self):
        self.internal_state = self.GraspStates.INIT
        self.grasping = False
        self.target_object = self.find_target_object()
        ActionBehavior.initialise(self)

    def terminate(self, _status):
        """ If this behavior was grasping, unmark it. If not, it was some other behavior so don't unmark it."""
        if self.grasping:
            self.world_interface.grasping = False
            self.grasping = False

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
        parameters = {}
        n_marks = 4
        marks = []
        marks.append(node_descriptor.find('"'))
        for i in range(1, n_marks):
            if marks[i-1] >= 0:
                marks.append(node_descriptor.find('"', marks[i-1] + 1))
            else:
                break

        if len(marks) < 2:
            raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        if len(marks) >= 4:
            parameters["relation"] = node_descriptor[marks[1] + 7: marks[2] - 1]
            parameters["relative_object"] = node_descriptor[marks[2]: marks[3] + 1]

        return parameters

    def find_target_object(self):
        """ Finds first target object from possible objects in world """
        if self.parameters["target_object"] == '"any object"':
            if "relation" in self.parameters and "relative_object" in self.parameters:
                for target_object in self.world_interface.movable_objects:
                    if self.world_interface.object_at(target_object, self.parameters["relation"], self.parameters["relative_object"]):
                        return target_object
            return None
        else:
            return self.parameters["target_object"]

    def check_for_success(self):
        """Check if object is grasped."""
        if (self.internal_state == self.GraspStates.DONE or not self.require_execution) and \
            self.world_interface.get_grasped_object() == self.target_object:
            self.success()

    def check_for_failure(self):
        """Fail if some other object is grasped."""
        grasped_object = self.world_interface.get_grasped_object()
        allowed_objects = (self.target_object, None)
        if self.require_execution:
            allowed_objects = (None, )
        return grasped_object not in allowed_objects

    def update(self):
        """Executes behavior """
        self.check_for_success()

        if self.state is pt.common.Status.RUNNING:
            if self.check_for_failure():
                return self.failure("Another object was already grasped")
            ActionBehavior.update(self)
            if self.internal_state == self.GraspStates.INIT:
                self.calc_grasp_position()
                if self.grasp_position is None:
                    return self.failure("Could not calculate grasp position")
                self.calc_approach_position()
                self.world_interface.open_gripper()
                if not self.world_interface.move_joint(self.approach_position, self.orientation):
                    return self.failure("Could not move to approach position")
                self.internal_state = self.GraspStates.APPROACHING
            if self.internal_state == self.GraspStates.APPROACHING:
                if self.calc_grasp_position(): #Recalculate in case it changed
                    if self.grasp_position is None:
                        return self.failure("Could not calculate grasp position")
                    self.calc_approach_position() #Recalculate in case it changed
                    if not self.world_interface.move_joint(self.approach_position, self.orientation):
                        return self.failure("Could not move to approach position")
                if self.world_interface.robot_at(self.approach_position, self.orientation):
                    if self.grasp_position is None:
                        return self.failure("Could not calculate grasp position")
                    if not self.world_interface.move_linear(self.grasp_position, self.orientation):
                        return self.failure("Could not move to grasp position")
                    self.internal_state = self.GraspStates.POSITIONING
            if self.internal_state == self.GraspStates.POSITIONING:
                if self.calc_grasp_position(): #Recalculate in case it changed
                    if self.grasp_position is None:
                        return self.failure("Could not calculate grasp position")
                    self.calc_approach_position() #Recalculate in case it changed
                    if not self.world_interface.move_linear(self.grasp_position, self.orientation):
                        return self.failure("Could not move to grasp position")
                if self.world_interface.robot_at(self.grasp_position, self.orientation):
                    self.world_interface.close_gripper()
                    self.world_interface.grasping = True
                    self.grasping = True
                    self.internal_state = self.GraspStates.GRASPING
            if self.internal_state == self.GraspStates.GRASPING:
                if self.world_interface.get_grip_successful():
                    if not self.world_interface.move_linear(self.approach_position, self.orientation):
                        return self.failure("Could not move to approach position")
                    self.internal_state = self.GraspStates.LIFTING
            if self.internal_state == self.GraspStates.LIFTING:
                if self.world_interface.robot_at(self.approach_position, self.orientation):
                    self.world_interface.grasp_action_completed(self.target_object)
                    self.grasping = False
                    self.internal_state = self.GraspStates.DONE
        return self.state

    def calc_grasp_position(self):
        """Gets grasp position of object, returns True if changed from last check"""
        target_object_position = self.world_interface.get_position_robot_frame(self.target_object)
        if target_object_position is None:
            self.target_object_last_known_position = None
            self.grasp_position = None
            return True
        if self.target_object_last_known_position is None or \
           np.linalg.norm(target_object_position - self.target_object_last_known_position) > 0.001:
            self.target_object_last_known_position = target_object_position
            grasp_offset = self.world_interface.get_grasp_offset(self.target_object)
            grasp_offset_robot_frame = self.world_interface.rotate_vector_yaw(grasp_offset, self.world_interface.get_yaw("robot base"))
            grasp_yaw = self.world_interface.get_grasp_yaw(self.target_object)
            self.grasp_position = target_object_position + grasp_offset_robot_frame
            total_yaw = self.world_interface.clamp_angle(self.world_interface.get_yaw(self.target_object) + grasp_yaw -
                                                         self.world_interface.get_yaw("robot base"))
            self.orientation = self.world_interface.get_orientation_from_yaw(total_yaw)
            return True
        else:
            return False

    def calc_approach_position(self):
        """Gets approach position of object"""
        self.approach_position = self.grasp_position + np.array([0.0, 0.0, 0.15])

class Place(ActionBehavior):
    """
    Place object on position
    """
    class PlaceStates(IntEnum):
        """Define the internal states during execution."""
        INIT = 1
        APPROACHING = 2
        POSITIONING = 3
        RELEASING = 4
        RISING = 5
        DONE = 6

    def __init__(self, name, parameters, world_interface, index=0, verbose=False):
        self.release_position = None
        self.approach_position = None
        self.orientation = world_interface.get_orientation_from_yaw(parameters["angle"])
        self.yaw = parameters["angle"]
        self.internal_state = self.PlaceStates.INIT
        self.releasing = False
        self.target_object = parameters["target_object"]
        name = Place.to_string_static(parameters)
        ActionBehavior.__init__(self, name, parameters, world_interface, \
                                max_ticks=20, index=index, verbose=verbose)

    @staticmethod
    def get_precondition_behaviors(extra_preconditions=False):
        """ Returns a list of precondition behaviors """
        if extra_preconditions:
            return [Grasped, BaseNear]
        return [Grasped]

    @staticmethod
    def get_postcondition_behaviors():
        """ Returns a list of postcondition behaviors """
        return [AtPos]

    @staticmethod
    def check_string_match(node_string):
        """ Check if the string description of the node matches this node """
        if "place" in node_string and " in" not in node_string:
            return True
        return False

    def to_string(self):
        """ Creates a string """
        return Place.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = "place " + parameters["target_object"]
        node_string += " at \n"
        node_string += parameters["relative_object"]
        node_string += " " + str(parameters.get("offset", [0.0, 0.0, 0.0]))
        node_string += " " + str(parameters.get("angle", 0.0))
        node_string += "!"
        return node_string

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Places the target object at given offset from the relative object if within reach.\n" + \
               "The angle parameter is relative the global coordinate system"

    @staticmethod
    def is_parameter_valid(parameters, _name):
        """ Checks if parameter of given name is valid """
        if parameters["target_object"].value is not None and parameters["target_object"].value == parameters["relative_object"].value:
            return False
        return True

    @staticmethod
    def ok_after(parameters, other, other_parameters): # pylint: disable=unused-argument
        """ Check if the other behavior is ok after this behavior """
        if other == Place:
            return False
        return True

    def initialise(self):
        self.internal_state = self.PlaceStates.INIT
        self.releasing = False
        ActionBehavior.initialise(self)
        if self.parameters["target_object"] == '"grasped object"':
            self.target_object = self.world_interface.get_grasped_object()
            if not self.require_execution and self.target_object is None:
                self.success()

    def terminate(self, _status):
        """ If this behavior was releasing, unmark it. If not, it was some other behavior so don't unmark it."""
        if self.releasing:
            self.world_interface.releasing = False
            self.releasing = False

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
        parameters = {}
        n_marks = 4
        marks = [0] * n_marks
        marks[0] = node_descriptor.find('"')
        for i in range(1, n_marks):
            if marks[i-1] >= 0:
                marks[i] = node_descriptor.find('"', marks[i-1] + 1)
            else:
                raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        parameters["relative_object"] = node_descriptor[marks[2]: marks[3] + 1]
        numbers = list(map(float, re.findall(r'-?\d+\.\d+|-?\d+', node_descriptor)))
        if len(numbers) > 2:
            offset = tuple(numbers[0:3]) #pylint: disable=superfluous-parens
        else:
            offset = tuple([0.0, 0.0, 0.0])
        parameters["offset"] = offset
        if len(numbers) > 3:
            angle = numbers[3]
        else:
            angle = 0.0
        parameters["angle"] = angle

        return parameters

    def check_for_success(self):
        """Check if object is at target position."""
        if self.state != pt.common.Status.SUCCESS and (self.internal_state == self.PlaceStates.DONE or not self.require_execution):
            if self.world_interface.object_at(self.target_object,
                                              self.parameters["relative_object"],
                                              self.parameters["offset"],
                                              self.parameters["angle"]) and \
                self.world_interface.get_grasped_object() != self.target_object:
                self.success()

    def check_for_failure(self):
        """Fail if object is not grasped."""
        return self.world_interface.get_grasped_object() != self.target_object

    def update(self):
        """Executes behavior """
        self.check_for_success()

        if self.state is pt.common.Status.RUNNING:
            if self.check_for_failure():
                return self.failure("Object not grasped")
            ActionBehavior.update(self)
            if self.internal_state == self.PlaceStates.INIT:
                self.calc_release_position()
                if self.release_position is None:
                    return self.failure("Could not calculate release position")
                self.calc_place_approach_position()

                if not self.world_interface.move_joint(self.approach_position, self.orientation):
                    return self.failure("Could not move to approach position")
                self.internal_state = self.PlaceStates.APPROACHING

            if self.internal_state == self.PlaceStates.APPROACHING:
                if self.world_interface.robot_at(self.approach_position, self.orientation):
                    if self.release_position is None:
                        return self.failure("Could not calculate release position")
                    if not self.world_interface.move_linear(self.release_position, self.orientation):
                        return self.failure("Could not move to release position")
                    self.internal_state = self.PlaceStates.POSITIONING
            if self.internal_state == self.PlaceStates.POSITIONING:
                if self.world_interface.robot_at(self.release_position, self.orientation):
                    self.world_interface.open_gripper()
                    self.world_interface.releasing = True
                    self.releasing = True
                    self.internal_state = self.PlaceStates.RELEASING
            if self.internal_state == self.PlaceStates.RELEASING:
                if self.world_interface.get_release_successful():
                    if not self.world_interface.move_linear(self.approach_position, self.orientation):
                        return self.failure("Could not move to approach position")
                    self.internal_state = self.PlaceStates.RISING
            if self.internal_state == self.PlaceStates.RISING:
                if self.world_interface.robot_at(self.approach_position, self.orientation):
                    self.world_interface.place_action_completed(self.target_object, self.release_position, self.yaw)
                    self.releasing = False
                    self.internal_state = self.PlaceStates.DONE

        return self.state

    def calc_release_position(self):
        """Gets release position of object"""
        relative_object_position = self.world_interface.get_position_robot_frame(self.parameters["relative_object"])
        if relative_object_position is None:
            self.release_position = None
            return
        offset_robot_frame = self.world_interface.rotate_vector_yaw(self.parameters["offset"], self.world_interface.get_yaw("robot base"))
        grasp_offset_z = self.world_interface.get_grasp_offset(self.target_object)[2]
        self.release_position = relative_object_position + offset_robot_frame + np.array([0.0, 0.0, grasp_offset_z + 0.01])
        grasp_yaw = self.world_interface.get_grasp_yaw(self.target_object)
        total_yaw = self.world_interface.clamp_angle(self.parameters["angle"] + grasp_yaw - self.world_interface.get_yaw("robot base"))
        self.orientation = self.world_interface.get_orientation_from_yaw(total_yaw)

        #Uncomment below to use angle relative to relative_object
        #self.orientation = self.world_interface.get_orientation_from_yaw(
        #                       self.world_interface.get_yaw(self.parameters["relative_object"]) - \
        #                       self.parameters["angle"])

    def calc_place_approach_position(self):
        """ Calculates the place approach position """
        self.approach_position = self.release_position + np.array([0.0, 0.0, 0.15])

class PlaceIn(ActionBehavior):
    """
    Place target object in container object
    """
    class PlaceStates(IntEnum):
        """Define the internal states during execution."""
        INIT = 1
        APPROACHING = 2
        POSITIONING = 3
        RELEASING = 4
        RISING = 5
        DONE = 6

    def __init__(self, name, parameters, world_interface, index=0, verbose=False):
        self.release_position = None
        self.approach_position = None
        self.orientation = world_interface.get_orientation_from_yaw(0.0)
        self.internal_state = self.PlaceStates.INIT
        self.releasing = False
        self.target_object = parameters["target_object"]
        name = PlaceIn.to_string_static(parameters)
        ActionBehavior.__init__(self, name, parameters, world_interface, \
                                max_ticks=20, index=index, verbose=verbose)

    @staticmethod
    def get_precondition_behaviors(extra_preconditions=False):
        """ Returns a list of precondition behaviors """
        if extra_preconditions:
            return [Grasped, BaseNear]
        return [Grasped]

    @staticmethod
    def get_postcondition_behaviors():
        """ Returns a list of postcondition behaviors """
        return [InContainer]

    @staticmethod
    def check_string_match(node_string):
        """ Check if the string description of the node matches this node """
        if "place in" in node_string or ("in " in node_string and "place" in node_string):
            return True
        return False

    def to_string(self):
        """ Creates a string """
        return PlaceIn.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = "place " + parameters["target_object"]
        node_string += " in \n"
        node_string += parameters["relative_object"]
        node_string += "!"
        return node_string

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Places the target object inside the relative object if within reach."

    @staticmethod
    def is_parameter_valid(parameters, _name):
        """ Checks if parameter of given name is valid """
        if parameters["target_object"].value is not None and parameters["target_object"].value == parameters["relative_object"].value:
            return False
        return True

    @staticmethod
    def ok_after(parameters, other, other_parameters): # pylint: disable=unused-argument
        """ Check if the other behavior is ok after this behavior """
        if other == PlaceIn:
            return False
        return True

    def initialise(self):
        self.internal_state = self.PlaceStates.INIT
        self.releasing = False
        ActionBehavior.initialise(self)
        if self.parameters["target_object"] == '"grasped object"':
            self.target_object = self.world_interface.get_grasped_object()
            if not self.require_execution and self.target_object is None:
                self.success()

    def terminate(self, _status):
        """ If this behavior was releasing, unmark it. If not, it was some other behavior so don't unmark it."""
        if self.releasing:
            self.world_interface.releasing = False
            self.releasing = False

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
        parameters = {}
        n_marks = 4
        marks = [0] * n_marks
        marks[0] = node_descriptor.find('"')
        for i in range(1, n_marks):
            if marks[i-1] >= 0:
                marks[i] = node_descriptor.find('"', marks[i-1] + 1)
            else:
                raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        parameters["relative_object"] = node_descriptor[marks[2]: marks[3] + 1]

        return parameters

    def check_for_success(self):
        """Check if object is at target position."""
        if self.state != pt.common.Status.SUCCESS and (self.internal_state == self.PlaceStates.DONE or not self.require_execution):
            if self.world_interface.object_in(self.target_object,
                                              self.parameters["relative_object"]) and \
                self.world_interface.get_grasped_object() != self.target_object:
                self.success()

    def check_for_failure(self):
        """Fail if object is not grasped."""
        return self.world_interface.get_grasped_object() != self.target_object

    def update(self):
        """Executes behavior """
        self.check_for_success()

        if self.state is pt.common.Status.RUNNING:
            if self.check_for_failure():
                return self.failure("Object not grasped")
            ActionBehavior.update(self)
            if self.internal_state == self.PlaceStates.INIT:
                self.calc_release_position()
                if self.release_position is None:
                    return self.failure("Could not calculate release position")
                self.calc_place_approach_position()

                if not self.world_interface.move_joint(self.approach_position, self.orientation):
                    return self.failure("Could not move to approach position")
                self.internal_state = self.PlaceStates.APPROACHING

            if self.internal_state == self.PlaceStates.APPROACHING:
                if self.world_interface.robot_at(self.approach_position, self.orientation):
                    if self.release_position is None:
                        return self.failure("Could not calculate release position")
                    if not self.world_interface.move_linear(self.release_position, self.orientation):
                        return self.failure("Could not move to release position")
                    self.internal_state = self.PlaceStates.POSITIONING
            if self.internal_state == self.PlaceStates.POSITIONING:
                if self.world_interface.robot_at(self.release_position, self.orientation):
                    self.world_interface.open_gripper()
                    self.world_interface.releasing = True
                    self.releasing = True
                    self.internal_state = self.PlaceStates.RELEASING
            if self.internal_state == self.PlaceStates.RELEASING:
                if self.world_interface.get_release_successful():
                    if not self.world_interface.move_linear(self.approach_position, self.orientation):
                        return self.failure("Could not move to approach position")
                    self.internal_state = self.PlaceStates.RISING
            if self.internal_state == self.PlaceStates.RISING:
                if self.world_interface.robot_at(self.approach_position, self.orientation):
                    self.world_interface.place_action_completed(self.target_object, self.release_position - np.array([0.0, 0.0, 0.1]))
                    self.releasing = False
                    self.internal_state = self.PlaceStates.DONE

        return self.state

    def calc_release_position(self):
        """Gets release position of object"""
        relative_object_position = self.world_interface.get_position_robot_frame(self.parameters["relative_object"])
        if relative_object_position is None:
            self.release_position = None
            return
        relative_object_height = self.world_interface.get_object_height(self.parameters["relative_object"])
        grasp_offset_z = self.world_interface.get_grasp_offset(self.target_object)[2]
        self.release_position = relative_object_position + np.array([0.0, 0.0, relative_object_height + grasp_offset_z + 0.01])

    def calc_place_approach_position(self):
        """ Calculates the place approach position """
        self.approach_position = self.release_position + np.array([0.0, 0.0, 0.15])

class Idle(ActionBehavior):
    """
    Do nothing, always return running
    """

    def __init__(self, name, parameters, world_interface, index=0, verbose=False):
        name = Idle.to_string_static(parameters)
        ActionBehavior.__init__(self, name, parameters, world_interface, \
                                max_ticks=1000, index=index, verbose=verbose)

    def to_string(self):
        """ Creates a string """
        return Idle.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = 'idle!'
        return Behavior.common_string_rules(node_string, parameters)

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Does nothing. Always returns RUNNING."

    @staticmethod
    def ok_after(parameters, other, other_parameters): # pylint: disable=unused-argument
        """ Check if the other behavior is ok after this behavior """
        if other == Idle:
            return False
        return True

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
        return {}

    def update(self):
        """Executes behavior """
        ActionBehavior.update(self)
        return self.state

class MoveBase(ActionBehavior):
    """
    Move robot base to a position and yaw angle
    """
    class MoveBaseStates(IntEnum):
        """Define the internal states during execution."""
        INIT = 1
        TUCKING = 2
        MOVING = 3
        DONE = 4

    def __init__(self, name, parameters, world_interface, index=0, verbose=False):
        self.target_position = None
        self.target_object = parameters["target_object"]
        yaw = parameters.get("angle", None)
        offset = parameters.get("offset", None)
        if yaw is None:
            parameters["angle"] = self.get_default_parameter_value("angle", parameters, world_interface.get_default_object_positions())
        self.yaw = parameters["angle"]
        self.internal_state = self.MoveBaseStates.INIT
        self.moving_base = False

        if offset is None:
            parameters["offset"] = self.get_default_parameter_value("offset", parameters, world_interface.get_default_object_positions())

        if len(parameters["offset"]) < 3:
            parameters["offset"] += (0.0,) # Add one for z direction since offset is only xy
        self.offset = parameters["offset"]

        name = MoveBase.to_string_static(parameters)
        ActionBehavior.__init__(self, name, parameters, world_interface, \
                                max_ticks=30, index=index, verbose=verbose)

    @staticmethod
    def get_postcondition_behaviors():
        """ Returns a list of postcondition behaviors """
        return [BaseNear]

    def to_string(self):
        """ Creates a string """
        return MoveBase.to_string_static(self.parameters)

    @staticmethod
    def to_string_static(parameters):
        """ Creates a string """
        node_string = "move to " + parameters["target_object"]
        node_string += " " + str(parameters.get("offset", [0.0, 0.0])[0:2])
        node_string += " " + str(parameters.get("angle", 0.0))
        node_string += "!"
        return node_string

    @staticmethod
    def get_tooltip():
        """ Short tooltip description of Behavior """
        return "Moves the robot base to the target object position with a given offset.\n" + \
               "The angle parameter is relative the global coordinate system"

    @staticmethod
    def ok_after(parameters, other, other_parameters): # pylint: disable=unused-argument
        """ Check if the other behavior is ok after this behavior """
        if other == MoveBase:
            return False
        return True

    def initialise(self):
        self.internal_state = self.MoveBaseStates.INIT
        self.moving_base = False
        ActionBehavior.initialise(self)

        if not self.require_execution and self.target_object is None:
            self.success()

    def terminate(self, _status):
        """ If this behavior was moving, unmark it. If not, it was some other behavior so don't unmark it."""
        if self.moving_base:
            self.world_interface.moving_base = False
            self.moving_base = False

    @staticmethod
    def get_default_parameter_value(name, other_parameters, default_object_positions):
        """ Get default parameter value for the behavior """
        if name == "angle":
            target_object = other_parameters["target_object"]
            if hasattr(target_object, "value"):
                target_object = target_object.value

            if target_object == '"origin"':
                return 0.0

            #If yaw is not given, set angle to point roughly towards target object starting position
            start_position = default_object_positions[target_object][0:2] - default_object_positions['"robot base"'][0:2]

            if abs(start_position[0]) >= abs(start_position[1]): #Point forwards or backwards
                if start_position[0] > 0:
                    return 0.0 #Point forward
                else:
                    return round(np.pi, 2) #Point backwards
            else:
                if start_position[1] > 0:
                    return -round(np.pi / 2, 2) #Point left
                else:
                    return round(np.pi / 2, 2) #Point right
        elif name == "offset":
            target_object = other_parameters["target_object"]
            if hasattr(target_object, "value"):
                target_object = target_object.value

            # Set offset to be roughly 0.4m (size of base plus margin) towards origin
            if target_object == '"origin"':
                return tuple(np.zeros(2)) #No default offset if target is origin
            else:
                start_position = default_object_positions[target_object][0:2] - default_object_positions['"robot base"'][0:2]
                distance = 0.4
                if "area" not in target_object:
                    distance += BaseWorldInterface.get_object_width(target_object) / 2
                return tuple(np.round(distance / np.linalg.norm(start_position) * -start_position, 1) + np.zeros(2))
        elif name == "target_object":
            return None
        else:
            print("Error: Unknown parameter name")
            return None

    @staticmethod
    def parse_parameters(node_descriptor):
        """ Parse behavior parameters from string """
        parameters = {}
        n_marks = 2
        marks = [0] * n_marks
        marks[0] = node_descriptor.find('"')
        for i in range(1, n_marks):
            if marks[i-1] >= 0:
                marks[i] = node_descriptor.find('"', marks[i-1] + 1)
            else:
                raise AttributeError("Error, parameter parsing failed")

        parameters["target_object"] = node_descriptor[marks[0]: marks[1] + 1]
        numbers = list(map(float, re.findall(r'-?\d+\.\d+|-?\d+', node_descriptor)))
        if len(numbers) > 1:
            offset = tuple(numbers[0:2]) #pylint: disable=superfluous-parens
        else:
            offset = tuple([0.0, 0.0])
        parameters["offset"] = offset
        if len(numbers) > 2:
            angle = numbers[2]
        else:
            angle = 0.0
        parameters["angle"] = angle

        return parameters

    def check_for_success(self):
        """Check if object is at target position."""
        if self.state != pt.common.Status.SUCCESS and (self.internal_state == self.MoveBaseStates.DONE or not self.require_execution):
            target_object_position = self.world_interface.get_position(self.target_object)
            target_position = target_object_position + self.offset
            if self.world_interface.robot_base_at(target_position, self.yaw, last_known=True):
                self.success()

    def update(self):
        """Executes behavior """
        self.check_for_success()
        ActionBehavior.update(self)

        if self.state is pt.common.Status.RUNNING:
            if self.internal_state == self.MoveBaseStates.INIT:
                self.calc_target_position()
                if self.target_position is None:
                    return self.failure("No target position found")

                self.world_interface.moving_base = True
                self.moving_base = True
                self.world_interface.move_joint_tucked()
                self.internal_state = self.MoveBaseStates.TUCKING
            if self.internal_state == self.MoveBaseStates.TUCKING:
                if self.world_interface.robot_tucked():
                    self.world_interface.move_robot_base(self.target_position, self.yaw)
                    self.internal_state = self.MoveBaseStates.MOVING
            if self.internal_state == self.MoveBaseStates.MOVING:
                if self.calc_target_position(): #Recalculate in case it changed
                    if self.target_position is None:
                        return self.failure("No target position found")
                    self.world_interface.move_robot_base(self.target_position, self.yaw)
                if self.world_interface.robot_base_speed < 0.001 and \
                    self.world_interface.robot_base_at(self.target_position, self.yaw):
                    self.world_interface.move_base_action_completed(self.target_position, self.yaw)
                    self.moving_base = False
                    self.internal_state = self.MoveBaseStates.DONE

        return self.state

    def calc_target_position(self):
        """Gets target position of robot base """
        target_object_position = self.world_interface.get_position(self.target_object)
        target_position = target_object_position + self.offset
        if self.target_position is None or \
           np.linalg.norm(target_position - self.target_position) > 0.001:
            self.target_position = target_position
            self.target_position[2] = 0.0
            return True

        return False
