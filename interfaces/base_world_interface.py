""" Basic world interface for ABB robots and sensors to be inherited in for use in both planning and real robot stages."""

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
from typing import Any
from dataclasses import dataclass, field
import numpy as np
from scipy.spatial.transform import Rotation as R
from ikpy.utils import geometry

@dataclass
class BaseWorldInterfaceParameters:
    """Data class for parameters for the simulations."""
    chain: Any = None                                      # IK chain
    movable_objects: Any = None                            # List of all movable objects
    object_positions: dict = field(default_factory=dict)   # Dictionary with positions of all objects
    object_yaws: dict = field(default_factory=dict)        # Dictionary with yaws of all objects
    graspable_objects: Any = None                          # List of all graspable objects
    table_offset: float = 0.0                              # Table offset relative robot base
    pos_acc: float = 0.02                                  # Position accuracy for object placement
    angle_acc: float = 0.2                                 # Angle accuracy for object placement

class BaseWorldInterface:
    """
    Base world interface class
    """
    def __init__(self, parameters: Any = None):
        self.chain = parameters.chain
        self.joint_reference_home = np.array([0, 0, 0, 0, 90, 0])
        self.joint_reference_tucked = np.array([0, 0, 0, 0, 90, 0])
        self.joint_reference = self.joint_reference_home
        self.joint_feedback = np.array([0, 0, 0, 0, 0, 0, 0, 0])
        self.robot_position = None
        self.robot_orientation = None
        self.robot_base_position = np.array([0.0, 0.0, 0.0])
        self.robot_base_position_last_known = np.array([0.0, 0.0, 0.0])
        self.robot_base_yaw = 0.0
        self.robot_base_yaw_last_known = 0.0
        self.robot_base_tilt = 0.0 # Maximum of roll and pitch, how much is the base tilted
        self.robot_base_tilt_last_known = 0.0
        self.robot_base_speed = 0.0
        self.robot_base_position_ref = np.array([0, 0, 0])
        self.robot_base_yaw_ref = 0.0
        self.base_immobile = False
        self.energy_consumed = 0.0
        self.grasped_object = None
        self.manipulation_target = None
        self.grasping = False
        self.releasing = False
        self.moving_base = False
        self.object_stationary_since_grasp = {} # Don't update position until stationary after grasp release
        self.object_positions = {}
        self.object_observed_positions = {}
        self.object_speeds = {}
        self.object_default_positions = {}
        self.object_position_robot_frame = {}
        self.object_yaws = {}
        self.object_observed_yaws = {}
        self.object_yaw_speeds = {}
        self.object_position_known = {}
        self.object_upright = {}
        self.object_opened = {}
        self.object_unlocked = {}
        self.movable_objects = parameters.movable_objects
        if parameters.object_positions is not None:
            for key in parameters.object_positions:
                if key == '"robot base"':
                    self.robot_base_position = parameters.object_positions[key]
                    self.robot_base_position_last_known = parameters.object_positions[key]
                    self.robot_base_position_ref = parameters.object_positions[key]
                else:
                    self.object_positions[key] = parameters.object_positions[key]
                    self.object_observed_positions[key] = parameters.object_positions[key]
                    self.object_speeds[key] = 0.0
                    self.object_yaw_speeds[key] = 0.0
                    self.object_stationary_since_grasp[key] = True
                self.object_default_positions[key] = parameters.object_positions[key]
        if parameters.object_yaws is not None:
            for key in parameters.object_yaws:
                if key == '"robot base"':
                    self.robot_base_yaw = parameters.object_yaws[key]
                    self.robot_base_yaw_last_known = parameters.object_yaws[key]
                    self.robot_base_yaw_ref = parameters.object_yaws[key]
                else:
                    self.object_yaws[key] = parameters.object_yaws[key]
                    self.object_observed_yaws[key] = parameters.object_yaws[key]
        if parameters.object_positions is not None: #Must be done after robot base position and yaw is set
            for key in parameters.object_positions:
                self.transform_to_robot_frame(key)
        if parameters.movable_objects is not None:
            for movable_object in parameters.movable_objects:
                if movable_object not in self.object_positions:
                    self.object_positions[movable_object] = None
                if movable_object not in self.object_yaws:
                    self.object_yaws[movable_object] = 0.0
                self.object_position_known[movable_object] = False
                self.object_upright[movable_object] = True
                self.object_opened[movable_object] = False
                self.object_unlocked[movable_object] = False
        self.object_positions['"table"'] = BaseWorldInterface.get_table_position()
        self.object_yaws['"table"'] = 0.0
        self.object_position_known['"table"'] = True
        if parameters.graspable_objects is None:
            self.graspable_objects = parameters.movable_objects
        else:
            self.graspable_objects = parameters.graspable_objects
        self.table_offset = parameters.table_offset
        self.pos_acc = parameters.pos_acc
        self.angle_acc = parameters.angle_acc
        self.error_message = ''
        self.last_action_index = -1
        self.lower_action_index = False
        self.failed_action = ''
        self.n_failed_actions = 0
        self.extra_preconditions = True # Whether to use extra preconditions for behaviors, only for testing

    @staticmethod
    def get_table_position():
        """ Returns table position"""
        return np.array([0.0, 0.0, 0.3])

    def get_feedback(self):
        # pylint: disable=no-self-use
        """ Get feedback from sensors to update world state """
        self.n_failed_actions = 0
        return True

    def send_references(self):
        # pylint: disable=no-self-use
        """ Dummy to fit template """
        return

    def set_last_action(self, index):
        """ Sets index of last action """
        if index < self.last_action_index:
            self.lower_action_index = True
        else:
            self.lower_action_index = False
        self.last_action_index = index

    def get_lower_action_index(self):
        """ Returns True if last action index was lower than previous """
        return self.lower_action_index

    def set_failed_action(self, failed_action):
        """ Sets memory of last failed action and increments counter """
        self.n_failed_actions += 1
        self.failed_action = failed_action

    def get_failed_action(self):
        """ Returns memory of last failed action """
        return self.failed_action

    def get_n_failed_actions(self):
        """ Returns number of failed actions """
        return self.n_failed_actions

    def set_error_message(self, error_message):
        """ Sets most recent error message """
        self.error_message = error_message

    def get_error_message(self):
        """ Returns most recent error message """
        return self.error_message

    def is_graspable(self, target_object):
        """ True if object is graspable """
        return target_object in self.graspable_objects

    def get_grasped_object(self):
        """ Returns grasped object"""
        return self.grasped_object

    def set_grasped_object(self, target_object):
        """ Set grasped object"""
        if target_object is None or target_object == '':
            if not self.releasing:
                self.grasped_object = None
        else:
            if not self.grasping: # Currently grasping in progress, wait until done
                self.grasped_object = target_object
                self.object_position_known[target_object] = False

    def grasp_action_completed(self, target_object): #pylint: disable=unused-argument
        """ Called when grasp action is completed """
        self.grasping = False

    def place_action_completed(self, target_object, release_position, yaw=0.0): #pylint: disable=unused-argument
        """ Called when place action is completed """
        self.releasing = False

    def do_ik(self, target_position, target_orientation, start_guess_input=None): #pylint: disable=redefined-outer-name
        """ Calculate inverse kinematics """
        try:
            if start_guess_input is not None:
                start_guess = start_guess_input
            if start_guess_input is None:
                start_guess = np.radians(np.concatenate([[0.0], self.joint_reference, [0.0]]))
                #clamp joint 6 to +/- pi
                start_guess[6] = self.clamp_angle(start_guess[6])
            joints_rad = self.chain.inverse_kinematics(
                target_position=target_position,
                initial_position=start_guess,
                target_orientation=target_orientation,
                orientation_mode="all"
            )
            #clamp joint 6 to +/- pi
            joints_rad[6] = self.clamp_angle(joints_rad[6])
        except ValueError:
            if start_guess_input is None:
                start_guess = np.radians(np.concatenate([[0.0], self.joint_reference_home, [0.0]])) #Try from home position instead
                return self.do_ik(target_position, target_orientation, start_guess)
            return False

        #Verify solution, typical reason for failure is out of reach
        transformation_matrix = self.chain.forward_kinematics(joints_rad)
        end_effector_position = np.array(transformation_matrix[:3, 3])
        end_effector_orientation = np.array(transformation_matrix[:3, :3])
        if np.linalg.norm(end_effector_position - target_position) < 0.001 and \
           np.linalg.norm(end_effector_orientation - target_orientation) < 0.001:
            self.joint_reference = np.degrees(joints_rad[1:-1])
            return True
        else:
            if start_guess_input is None:
                start_guess = np.radians(np.concatenate([[0.0], self.joint_reference_home, [0.0]])) #Try from home position instead
                return self.do_ik(target_position, target_orientation, start_guess)
            return False

    def move_joint(self, position, orientation=None):
        """ Move joints to position without checking for collisions """
        self.base_immobile = True #Fix base during movements
        if orientation is None:
            orientation = self.get_orientation_from_yaw(0.0)
        return self.do_ik(position, orientation)

    def move_joint_home(self):
        """ Move joints to home position without checking for collisions """
        self.joint_reference = self.joint_reference_home

    def move_joint_tucked(self):
        """ Move joints to tucked position without checking for collisions """
        self.base_immobile = True #Fix base during movements
        self.joint_reference = self.joint_reference_tucked

    def move_linear(self, position, orientation=None):
        """ Move linearly to position without checking for collisions, not implemented in unity """
        return self.move_joint(position, orientation)

    def robot_at(self, position, orientation, pos_acc=0.01, ori_acc=0.1):
        """ Checks if robot is at target_position and angle"""
        if np.linalg.norm(self.robot_position - position) < pos_acc:
            if orientation is None or sum(sum(abs(self.robot_orientation - orientation))) < ori_acc: # type: ignore
                return True

        return False

    def robot_tucked(self):
        """ Checks if robot is in tucked position """
        if np.linalg.norm(self.joint_feedback[1:-1] - self.joint_reference_tucked) < 0.1:
            return True
        return False

    def robot_base_at(self, position, yaw, pos_acc=0.1, angle_acc=0.1, last_known=False):
        """ Checks if robot is at target_position and yaw angle, ignore z since base is 2D"""
        if last_known:
            robot_base_position = np.copy(self.robot_base_position_last_known)
            robot_base_yaw = self.robot_base_yaw_last_known
            robot_base_tilt = self.robot_base_tilt_last_known
        else:
            robot_base_position = np.copy(self.robot_base_position)
            robot_base_yaw = self.robot_base_yaw
            robot_base_tilt = self.robot_base_tilt
        robot_base_position[2] = 0.0  # Ignore z coordinate for base position
        position_xy = np.copy(position)
        position_xy[2] = 0.0  # Ignore z coordinate for target position

        if np.linalg.norm(robot_base_position - position_xy) < pos_acc:
            if yaw is None or self.get_yaw_distance(robot_base_yaw, yaw) < angle_acc: # type: ignore
                if robot_base_tilt < 0.05: # Base not tilted too much as that indicates collision or unstable
                    return True

        return False

    def set_robot_base_position(self, base_position, base_yaw, tilt=0.0):
        """ Sets the robot base position. If moving, position is not reliable so no update but only update the last known """
        if not self.moving_base:
            self.robot_base_position_last_known = base_position
            self.robot_base_yaw_last_known = base_yaw
            self.robot_base_tilt_last_known = tilt
        self.robot_base_position = base_position
        self.robot_base_yaw = base_yaw
        self.robot_base_tilt = tilt

    def move_base_action_completed(self, base_position, base_yaw): #pylint: disable=unused-argument
        """ Called when move base action is completed """
        self.moving_base = False
        self.base_immobile = True
        self.robot_base_position_ref = self.robot_base_position
        self.robot_base_yaw_ref = self.robot_base_yaw

    def get_manipulation_target(self):
        """ Returns manipulation target"""
        return self.manipulation_target

    def set_manipulation_target(self, target_object):
        """ Set manipulation target"""
        self.manipulation_target = target_object

    def close_gripper(self):
        """ No gripper simulation for now """
        return

    def open_gripper(self):
        """ No gripper simulation for now """
        return

    @staticmethod
    def get_close_gripper_program():
        """ Returns only the one program row needed to close gripper """
        return "    g_GripIn \\holdForce:=7; \n"

    @staticmethod
    def get_open_gripper_program(no_wait=False):
        """ Returns only the one program row needed to open gripper """
        if no_wait:
            return "    g_GripOut \\NoWait; \n"
        else:
            return "    g_GripOut; \n"

    def is_running(self):
        """ Program start assumed instantaneous so always true """
        return True

    def has_stopped(self):
        """ Program execution assumed instantaneous so always done """
        return True

    def stop(self):
        """ Program execution assumed instantaneous so always done """
        return

    def calc_distance(self, target_object, position):
        """ Calculates the distance between target object and given position """
        return np.linalg.norm(self.object_positions[target_object] - position)

    def get_position(self, target_object):
        """
        Returns position of object
        """
        if target_object in self.object_positions:
            return self.object_positions[target_object]
        else:
            return np.array([0.0, 0.0, 0.0])

    def get_default_object_positions(self):
        """ Return default positions of objects """
        return self.object_default_positions

    def get_position_robot_frame(self, target_object):
        """
        Returns position of object in robot frame. 
        Returns None if base is moving as it's not reliable then
        """
        if not self.moving_base and target_object in self.object_position_robot_frame:
            return self.object_position_robot_frame[target_object]
        else:
            return None

    def get_yaw(self, target_object):
        """
        Returns yaw angle (rotation around z) of object
        """
        if target_object == "robot base":
            return self.robot_base_yaw_last_known
        if target_object is None or target_object not in self.object_yaws:
            return 0.0
        return self.object_yaws[target_object]

    def get_yaw_distance(self, yaw_1, yaw_2):
        """
        Returns the distance between two yaw angles,
        accounting for the circular nature of angles
        """
        yaw_distance = abs(yaw_1 - yaw_2)
        if yaw_distance > np.pi:
            yaw_distance = 2 * np.pi - yaw_distance
        return yaw_distance

    def get_object_yaw_distance(self, target_object_1, target_object_2, offset_angle = 0.0):
        """
        Returns the distance between the yaw angles of two objects,
        accounting for the circular nature of angles
        """
        yaw_1 = self.get_yaw(target_object_1)
        yaw_2 = self.get_yaw(target_object_2) + offset_angle
        return self.get_yaw_distance(yaw_1, yaw_2)

    def clamp_angle(self, angle):
        """
        Clamps angle to keep it between +/- pi
        """
        while angle > np.pi:
            angle -= 2 * np.pi
        while angle < -np.pi:
            angle += 2 * np.pi
        return angle

    def set_object_position(self, target_object, position):
        """ Sets position of object """
        self.object_positions[target_object] = position
        if position is not None:
            self.object_position_known[target_object] = True
        else:
            self.object_position_known[target_object] = False

    def transform_to_robot_frame(self, target_object):
        """ Transforms target_object position to robot frame and saves it """
        if target_object in self.object_positions:
            offset = self.object_positions[target_object] - self.robot_base_position_last_known
            self.object_position_robot_frame[target_object] = self.rotate_vector_yaw(offset, self.robot_base_yaw)

    def transform_to_world_frame(self, target_object):
        """ Transforms target_object position to world frame and saves it """
        if target_object in self.object_position_robot_frame:
            offset = self.rotate_vector_yaw(self.object_position_robot_frame[target_object], -self.robot_base_yaw)
            self.set_object_position(target_object, offset + self.robot_base_position_last_known)

    def object_at(self, target_object, relative_object, offset, angle, pos_acc=None, angle_acc=None):
        """ Checks if object is at target_position and angle"""
        if pos_acc is None:
            pos_acc = self.pos_acc
        if angle_acc is None:
            angle_acc = self.angle_acc
        if self.calc_distance(target_object, self.object_positions[relative_object] + offset) < pos_acc:
            yaw = self.get_yaw(target_object)
            if angle is None or self.get_yaw_distance(yaw, angle) < angle_acc:
                return True

        return False

    @staticmethod
    def get_object_height(target_object):
        """ Returns height of object """
        if target_object == '"bowl"':
            return 0.1
        elif "bin" in target_object:
            return 0.2
        elif target_object == '"goal area"':
            return 0.1
        return 0.0

    @staticmethod
    def get_object_width(target_object):
        """ Returns width of object """
        if target_object == '"bowl"':
            return 0.2
        elif "bin" in target_object:
            return 0.3
        elif target_object == '"goal area"':
            return 1.0
        elif target_object == '"plate"':
            return 0.6
        elif target_object == '"glass"':
            return 0.1
        return 0.0

    def object_in(self, target_object, relative_object):
        """ Checks if target_object is inside relative_object """
        if "area" in relative_object:
            container_height = 10.0 # Assume infinite height for goal area
        else:
            container_height = self.get_object_height(relative_object)
        half_container_width= self.get_object_width(relative_object) / 2
        target_object_position = self.object_positions[target_object]
        relative_object_position = self.object_positions[relative_object]

        if abs(target_object_position[0] - relative_object_position[0]) < half_container_width and \
           abs(target_object_position[1] - relative_object_position[1]) < half_container_width and \
            target_object_position[2] > relative_object_position[2] and \
            target_object_position[2] < relative_object_position[2] + container_height:
            return True
        return False

    def is_object_upright(self, target_object):
        """ Checks if target is standing upright or not """
        return self.object_upright[target_object]

    def set_object_upright(self, _target_object, _value):
        """ Set the object upright variable only set directly in planner"""

    def is_opened(self, target_object):
        """ Checks if object is opened """
        return self.object_opened[target_object]

    def set_object_opened(self, target_object, _value):
        """ Set the object opened variable only set directly in planner"""

    def is_unlocked(self, target_object):
        """ Checks if object is unlocked """
        return self.object_unlocked[target_object]

    @staticmethod
    def finalize_program(program):
        """ Wraps program in a module so that it can be loaded and executed """
        return "MODULE MyModule \n    PROC my_proc() \n" + program + \
               "   ENDPROC \nENDMODULE \n"

    def run_program(self, program): #pylint: disable=unused-argument
        """ Executes the input program"""
        return True

    def get_orientation_from_yaw(self, yaw):
        """
        Returns orientation matrix for from yaw angle
        """
        return self.get_rotation_matrix(0, np.pi / 2, -yaw) # z for robot in opposite direction to yaw of object

    @staticmethod
    def get_rotation_matrix(x, y, z):
        """ Converts euler angles to rotation matrix """
        return geometry.rpy_matrix(x, y, z)

    def rotate_vector_yaw(self, vector, yaw):
        """ Rotates a vector by a given yaw angle (rad) """
        r1 = R.from_euler('z', yaw, degrees=False)
        return r1.apply(vector)
