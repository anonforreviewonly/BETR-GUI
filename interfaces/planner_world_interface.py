"""Simple planning interface simulating ABB robots and sensors."""
#pylint: disable=unused-argument
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
import numpy as np
from interfaces.base_world_interface import BaseWorldInterface

class WorldInterface(BaseWorldInterface):
    """
    Class for handling the simple planning world
    """
    def __init__(self, parameters=None, seed=0):
        self.index = seed

        BaseWorldInterface.__init__(self, parameters)
        self.robot_position = np.array([0.5, 0.0, 0.3])
        self.robot_orientation = self.get_orientation_from_yaw(0.0)

    @staticmethod
    def start_unity_process(n_agents=1, channel=50010, timescale=1, steps_per_tick=10,
                            headless=False, hide_window=True, unity_log_file="", scenario=""):
        """ Start the Unity process """
        return None

    @staticmethod
    def get_sim_client(channel=50010):
        """ Get simulation client """
        return None

    def get_references(self):
        """ Get current set references"""
        return None

    @staticmethod
    def get_default_reference(index):
        """ Get default reference"""
        return None

    @staticmethod
    def reset(sim_client):
        """ Reset the world """
        return None

    @staticmethod
    def get_camera_position(scenario):
        """ Get camera position based on scenario """
        return None

    def move_linear(self, position, orientation=None):
        """ Teleports the robot to the position """
        self.robot_position = np.copy(position)
        self.robot_orientation = np.copy(orientation)
        return True

    def move_joint(self, position, orientation=None):
        """ Teleports the robot to the position """
        result = super().move_joint(position, orientation)
        if result:
            self.robot_position = np.copy(position)
            self.robot_orientation = np.copy(orientation)
        return result

    def move_joint_home(self):
        """ Moves the robot joints to the home position """
        return True

    def move_joint_tucked(self):
        """ Move joints to tucked position without checking for collisions """
        self.joint_feedback = np.array([0.0])
        self.joint_feedback = np.append(self.joint_feedback, self.joint_reference_tucked)
        self.joint_feedback = np.append(self.joint_feedback, np.array([0.0]))
        return True

    def move_robot_base(self, position, yaw=None):
        """ Moves the robot base to the specified position and orientation """
        if yaw is None:
            yaw = 0.0
        self.robot_base_position = np.copy(position)
        self.robot_base_position[2] = 0.0
        self.robot_base_yaw = yaw
        return True

    def get_position(self, target_object):
        """
        Returns position of object
        """
        if self.grasped_object == target_object:
            return self.robot_position
        return super().get_position(target_object)

    def set_object_upright(self, target_object, value):
        """ Set the object upright variable """
        self.object_upright[target_object] = value

    def get_grip_successful(self):
        """ Returns if the grip was successful """
        return True

    def grasp_action_completed(self, target_object):
        """ Called when grasp action is completed """
        self.grasping = False
        self.set_grasped_object(target_object)

    def place_action_completed(self, target_object, release_position, yaw=0.0):
        """ Called when place action is completed """
        self.releasing = False
        self.object_position_robot_frame[target_object] = release_position
        self.object_yaws[target_object] = yaw
        self.transform_to_world_frame(target_object)
        self.set_grasped_object(None)

    def move_base_action_completed(self, base_position, base_yaw):
        """ Called when move base action is completed """
        self.moving_base = False
        self.robot_base_position = base_position
        self.robot_base_position_last_known = base_position
        self.robot_base_yaw = base_yaw
        self.robot_base_yaw_last_known = base_yaw
        for key in self.object_positions:
            self.transform_to_robot_frame(key)

    def get_release_successful(self):
        """ 
        Check if attempted release was successful, in this case, 
        if the object is not between the gripper anymore 
        """
        return True

    def get_grasp_offset(self, target_object):
        """
        Returns grasp offset for object
        """
        return np.array([0.0, 0.0, 0.0])

    def get_grasp_yaw(self, target_object):
        """
        Returns grasp yaw for object
        """
        return 0.0
