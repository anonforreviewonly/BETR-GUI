"""Interface to Unity robots and sensors."""

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
import os
import subprocess
import win32con
import numpy as np
from scipy.spatial.transform import Rotation as R
from interfaces.base_world_interface import BaseWorldInterface, BaseWorldInterfaceParameters
from simulation.ik_server.generated import ik_pb2
from simulation.ik_server.ik_server import SimClient

class WorldInterface(BaseWorldInterface):
    """
    Class for handling the interface to the unity simulation environment
    """
    def __init__(self, parameters, index):
        self.gripper_position = 0

        self.index = index
        self.grip_enabled = False
        self.grip_successful = False
        self.target_between_gripper = False

        BaseWorldInterface.__init__(self, parameters)

    @staticmethod
    def reset(sim_client): #pylint: disable=redefined-outer-name
        """ Reset the simulation environment """
        reset_msg = ik_pb2.Reset()
        reset_msg.reloadScene = True
        return sim_client.reset(reset_msg)  # First empty step to start the environment and get first obs

    @staticmethod
    def get_camera_position(scenario):
        """ Get camera position based on scenario """
        if scenario == "trashpicking":
            return ik_pb2.Transform(position=ik_pb2.Vector3(x=-1.0, y=2.0, z=3.5),
                                    euler=ik_pb2.Vector3(x=35, y=165, z=0))
        elif scenario == "tableware":
            return ik_pb2.Transform(position=ik_pb2.Vector3(x=1.5, y=1.5, z=0.5),
                                    euler=ik_pb2.Vector3(x=35, y=250, z=0))
        elif scenario == "cubebowl":
            return ik_pb2.Transform(position=ik_pb2.Vector3(x=-0.7, y=0.9, z=3.5),
                                    euler=ik_pb2.Vector3(x=20, y=165, z=0))
        elif scenario == "spheres":
            return ik_pb2.Transform(position=ik_pb2.Vector3(x=-0.7, y=1.5, z=4.5),
                                    euler=ik_pb2.Vector3(x=35, y=165, z=0))
        else:
            return ik_pb2.Transform(position=ik_pb2.Vector3(x=-0.7, y=0.9, z=1.7),
                                    euler=ik_pb2.Vector3(x=35, y=150, z=0))

    @staticmethod
    def custom_reset(sim_client, agent_indices, object_positions, object_yaws=None, scenario=None): #pylint: disable=redefined-outer-name
        """ Reset the simulation environment """
        reset_msg = ik_pb2.Reset(cameraPosition=WorldInterface.get_camera_position(scenario))

        if scenario == "cubebowl":
            bowl_position, bowl_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "bowl")
            red_cube_position, red_cube_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "cubeRed")
            green_cube_position, green_cube_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "cubeGreen")
            yellow_cube_position, yellow_cube_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "cubeYellow")
            blue_cube_position, blue_cube_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "cubeBlue")
            agent_position, agent_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "agentPosition")

            scenario_parameters = ik_pb2.EnvCubeBowlParameters(
                bowl=ik_pb2.Transform(position=bowl_position, euler=bowl_euler),
                cubeRed=ik_pb2.Transform(position=red_cube_position, euler=red_cube_euler),
                cubeGreen=ik_pb2.Transform(position=green_cube_position, euler=green_cube_euler),
                cubeYellow=ik_pb2.Transform(position=yellow_cube_position, euler=yellow_cube_euler),
                cubeBlue=ik_pb2.Transform(position=blue_cube_position, euler=blue_cube_euler),
                agentPosition=ik_pb2.Transform(position=agent_position, euler=agent_euler))
        elif scenario == "tableware":
            plate_position, plate_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "plate")
            knife_position, knife_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "knife")
            spoon_position, spoon_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "spoon")
            fork_position, fork_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "fork")
            glass_position, glass_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "glass")
            agent_position, agent_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "agentPosition")

            scenario_parameters = ik_pb2.EnvTablewareParameters(
                plate=ik_pb2.Transform(position=plate_position, euler=plate_euler),
                knife=ik_pb2.Transform(position=knife_position, euler=knife_euler),
                spoon=ik_pb2.Transform(position=spoon_position, euler=spoon_euler),
                fork=ik_pb2.Transform(position=fork_position, euler=fork_euler),
                glass=ik_pb2.Transform(position=glass_position, euler=glass_euler),
                agentPosition=ik_pb2.Transform(position=agent_position, euler=agent_euler))
        elif scenario == "trashpicking":
            paper_position, paper_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "trashPaper")
            food_position, food_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "trashFood")
            metal_position, metal_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "trashMetal")
            green_bin_position, green_bin_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "binGreen")
            yellow_bin_position, yellow_bin_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "binYellow")
            blue_bin_position, blue_bin_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "binBlue")
            agent_position, agent_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "agentPosition")
            scenario_parameters = ik_pb2.EnvTrashPickingParameters(
                trashPaper=ik_pb2.Transform(position=paper_position, euler=paper_euler),
                trashFood=ik_pb2.Transform(position=food_position, euler=food_euler),
                trashMetal=ik_pb2.Transform(position=metal_position, euler=metal_euler),
                binGreen=ik_pb2.Transform(position=green_bin_position, euler=green_bin_euler),
                binYellow=ik_pb2.Transform(position=yellow_bin_position, euler=yellow_bin_euler),
                binBlue=ik_pb2.Transform(position=blue_bin_position, euler=blue_bin_euler),
                agentPosition=ik_pb2.Transform(position=agent_position, euler=agent_euler))
        elif scenario == "spheres":
            red_position, red_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "sphereRed")
            green_position, green_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "sphereGreen")
            yellow_position, yellow_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "sphereYellow")
            goal_position, goal_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "goal")
            agent_position, agent_euler = WorldInterface.get_object_position_euler(object_positions, object_yaws, "agentPosition")

            scenario_parameters = ik_pb2.EnvSpheresParameters(
                sphereRed=ik_pb2.Transform(position=red_position, euler=red_euler),
                sphereGreen=ik_pb2.Transform(position=green_position, euler=green_euler),
                sphereYellow=ik_pb2.Transform(position=yellow_position, euler=yellow_euler),
                goal=ik_pb2.Transform(position=goal_position, euler=goal_euler),
                agentPosition=ik_pb2.Transform(position=agent_position, euler=agent_euler))
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        for index in agent_indices:
            if scenario == "cubebowl":
                reset_parameters = ik_pb2.ResetParameters(
                    index=index,
                    envCubeBowl=scenario_parameters)
            elif scenario == "tableware":
                reset_parameters = ik_pb2.ResetParameters(
                    index=index,
                    envTableware=scenario_parameters)
            elif scenario == "trashpicking":
                reset_parameters = ik_pb2.ResetParameters(
                    index=index,
                    envTrashPicking=scenario_parameters)
            elif scenario == "spheres":
                reset_parameters = ik_pb2.ResetParameters(
                    index=index,
                    envSpheres=scenario_parameters)
            else:
                raise ValueError(f"Unknown scenario: {scenario}")
            reset_msg.envsToReset.append(reset_parameters)
        reset_msg.reloadScene = True
        return sim_client.reset(reset_msg)  # First empty step to start the environment and get first obs

    @staticmethod
    def get_sim_client(channel=50010): #pylint: disable=redefined-outer-name
        """ Get simulation client """
        return SimClient(channel)

    @staticmethod
    def start_unity_process(n_agents=1, channel=50010, timescale=1, #pylint: disable=redefined-outer-name
                            steps_per_tick=10, headless=False, hide_window=True,
                            unity_log_file="unity.log", scenario="cubebowl"):
        """ Starts the unity simulation executable and returns handle """
        executable_path = os.path.join(os.path.dirname(__file__), '../simulation/Builds/Win/SimExample.exe')
        arguments = [executable_path,
                     "-agents", str(n_agents),  # Number of agents
                     "-logfile", unity_log_file,
                     "-channel", str(channel),  # Param to change connection port. If you want to start multiple instances
                     "-timescale", str(timescale),  # Param to change sim speed
                     "-decisionperiod", str(steps_per_tick),  # Simulation time step is 0.02 (50hz). Run control every 10 steps (0.2 - 5hz)
                     "-environment", scenario]  # cubebowl, trashpicking, tableware 

        if headless: #Params for no-graphics
            arguments.append("-headless")
            arguments.append("-batchmode")
            startupinfo = None
        else:
            if hide_window:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = win32con.SW_HIDE  # Hidden start for embedding later
            else:
                startupinfo = None
        unity_process = subprocess.Popen(arguments, startupinfo=startupinfo)

        print("Started Unity process")
        return unity_process

    def vector_from_unity_to_ikpy(self, vector):
        """ Translate vector from unity to ikpy """
        return np.array([vector.z, -vector.x, vector.y])

    def do_fk(self, joints):
        """ Calculate forward kinematics """
        joints_rad = np.radians(joints)
        transformation_matrix = self.chain.forward_kinematics(joints_rad)
        end_effector_position = np.array(transformation_matrix[:3, 3])
        end_effector_orientation = np.array(transformation_matrix[:3, :3])

        return end_effector_position, end_effector_orientation

    def set_observation(self, observation):
        """ Sets observation and calculates object positions """
        self.grip_successful = observation.gripSuccessful
        if self.grip_successful:
            self.set_grasped_object(WorldInterface.translate_unity_object_name(observation.betweenGripper))
        else:
            self.set_grasped_object(None)

        self.target_between_gripper = observation.isBetweenGripper

        for obj in observation.transformsByNameArmFrame.keys():
            if obj != "robot":
                object_name = WorldInterface.translate_unity_object_name(obj)
                observed_position = self.vector_from_unity_to_ikpy(observation.transformsByNameEnvFrame[obj].position)
                self.object_speeds[object_name] = np.linalg.norm(observed_position - \
                                                                 self.object_observed_positions.get(object_name, np.zeros(3)))
                self.object_observed_positions[object_name] = observed_position

                observed_yaw = np.radians(observation.transformsByNameEnvFrame[obj].euler.y)
                self.object_yaw_speeds[object_name] = self.get_yaw_distance(observed_yaw,
                                                                            self.object_observed_yaws.get(object_name, 0))
                self.object_observed_yaws[object_name] = observed_yaw

                if object_name != self.grasped_object:
                    if not self.object_stationary_since_grasp[object_name]:
                        if (self.object_speeds[object_name] < 0.005 and \
                           self.object_yaw_speeds[object_name] < 0.02) or \
                            object_name in ('"paper"', '"banana"'): # These two will roll around in the bin and it's ok
                            self.object_stationary_since_grasp[object_name] = True
                    if self.object_stationary_since_grasp[object_name]:
                        self.object_positions[object_name] = observed_position
                        self.object_position_robot_frame[object_name] = self.vector_from_unity_to_ikpy(
                                                                            observation.transformsByNameArmFrame[obj].position)
                        yaw_radians = np.radians(observation.transformsByNameEnvFrame[obj].euler.y)  # Unity uses Y as yaw
                        self.object_yaws[object_name] = self.clamp_angle(yaw_radians)
                else:
                    self.object_stationary_since_grasp[object_name] = False
        self.joint_feedback = np.array(observation.currentJointAnglesDeg)

        # Take rot matrix from unity quaternion and transform it to IKPy
        orientation = observation.linkTransformsArm[-1].orientation
        unity_quat = [orientation.x, orientation.y, orientation.z, orientation.w]
        r = R.from_quat(unity_quat)
        rot_matrix_unity = r.as_matrix()

        T = np.array([ #pylint: disable=invalid-name
            [0, 0, 1],  # X_ikpy =  Z_unity
            [-1, 0, 0],  # Y_ikpy = -X_unity
            [0, 1, 0],  # Z_ikpy =  Y_unity
        ])

        rot_matrix_ikpy = T @ rot_matrix_unity @ T.T

        new_robot_position = self.vector_from_unity_to_ikpy(observation.linkTransformsArm[-1].position)
        self.energy_consumed = 0.0 # Calculate for every step
        if self.robot_position is not None:
            self.energy_consumed += np.linalg.norm(new_robot_position - self.robot_position)
        self.robot_position = new_robot_position
        self.robot_orientation = rot_matrix_ikpy

        new_robot_base_position = self.vector_from_unity_to_ikpy(observation.transformsByNameEnvFrame["robot"].position)
        self.robot_base_speed = np.linalg.norm(self.robot_base_position[:2] - new_robot_base_position[:2]) #Ignore z in speed calculation
        if self.robot_base_position is not None:
            self.energy_consumed += np.linalg.norm(new_robot_base_position - self.robot_base_position) * 10 # Base consumes more
        self.set_robot_base_position(new_robot_base_position,
                                     self.clamp_angle(np.radians(observation.transformsByNameEnvFrame["robot"].euler.y)),
                                     max(abs(self.clamp_angle(np.radians(observation.transformsByNameEnvFrame["robot"].euler.x))),
                                         abs(self.clamp_angle(np.radians(observation.transformsByNameEnvFrame["robot"].euler.z)))))
        self.index = observation.index

    def get_references(self):
        """ Get current set references"""
        ref = ik_pb2.AgentControls(targetBasePose=ik_pb2.Transform(position=self.get_vector3(self.robot_base_position_ref),
                                   euler=self.get_vector3([0.0, 0.0, np.degrees(self.robot_base_yaw_ref)])))
        ref.jointTargetsDeg.extend(self.joint_reference)
        ref.activateGrip = self.grip_enabled
        ref.index = self.index
        ref.baseImmobile = self.base_immobile
        return ref

    @staticmethod
    def get_default_reference(index):
        """ Get default reference"""
        ref = ik_pb2.AgentControls(targetBasePose=ik_pb2.Transform(position=ik_pb2.Vector3(x=0, y=0, z=0.0),
                                   euler=ik_pb2.Vector3(x=0, y=0, z=0)))
        ref.jointTargetsDeg.extend(np.array([0, 0, 0, 0, 0, 0, 0, 0]))
        ref.activateGrip = False
        ref.index = index
        return ref

    @staticmethod
    def send_parallel_references(sim_client, references): #pylint: disable=redefined-outer-name
        """ Send references to all agents in the simulation """
        step_msg = ik_pb2.Step()
        #step_msg.stepCount = 10  # Optional, how many sim steps to take every step. Overrides "decisionperiod" from startup for one step.
        #step_msg.timeScale = 100 # Optional, how fast sim moves w.r.t real time. Overrides "timescale" from startup for one step.
        for ref in references:
            step_msg.controls.append(ref)
        return sim_client.step(step_msg)

    def move_robot_base(self, position, yaw=None):
        """ Move robot base to position without checking for collisions """
        if yaw is None:
            yaw = 0.0
        self.robot_base_position_ref = np.copy(position)
        self.robot_base_position_ref[2] = 0.0
        self.robot_base_yaw_ref = yaw
        self.base_immobile = False  # Allow base to move again

    def close_gripper(self):
        """ Closes the gripper """
        self.grip_enabled = True

    def open_gripper(self):
        """ Opens the gripper """
        self.grip_enabled = False

    def get_grip_successful(self):
        """ Check if attempted grip was successful """
        return self.grip_successful

    def get_release_successful(self):
        """ 
        Check if attempted release was successful, in this case, 
        if the object is not between the gripper anymore 
        """
        return not self.grip_successful

    @staticmethod
    def get_object_position_euler(object_positions, object_yaws, object_name):
        """ Get object position and euler angles in degrees for orientation """
        target_object_name = WorldInterface.translate_unity_object_name(object_name)
        if object_positions is not None and target_object_name in object_positions:
            object_position = object_positions[target_object_name]
            if isinstance(object_position, str) and object_position == "grasped":
                # If object is grasped, use the default robot gripper position as the object position
                object_position = WorldInterface.get_vector3([0.55, 0.0, 0.72] - WorldInterface.get_grasp_offset(target_object_name) + \
                                                              object_positions['"robot base"'])  # If robot is not at 0
            else:
                object_position = WorldInterface.get_vector3(object_position)
        else:
            object_position =  WorldInterface.get_default_object_position(target_object_name)

        if object_yaws is not None and target_object_name in object_yaws:
            # Convert yaw from radians to ik_pb2.Vector3 format
            object_euler = ik_pb2.Vector3(x=0.0, y=object_yaws[target_object_name], z=0.0)
        else:
            object_euler = WorldInterface.get_default_object_orientation(target_object_name)

        #Convert to degrees
        object_euler.x = np.degrees(object_euler.x)
        object_euler.y = np.degrees(object_euler.y)
        object_euler.z = np.degrees(object_euler.z)

        return object_position, object_euler

    @staticmethod
    def get_vector3(numpy_array):
        """ Get ik_pb2.Vector3 from numpy array 
            In unity, the vectors are in this order:
            [vector.z, -vector.x, vector.y]
            so to translate we do
            [-vector.y, vector.z, vector.x]
        """
        return ik_pb2.Vector3(x=-numpy_array[1], y=numpy_array[2], z=numpy_array[0])

    @staticmethod
    def get_array(vector3):
        """ Get numpy array from ik_pb2.Vector3 
            In unity, the vectors are in this order:
            [vector.z, -vector.x, vector.y]
        """
        return np.array([vector3.z, -vector3.x, vector3.y])

    @staticmethod
    def get_default_object_position(object_name): #pylint: disable=unused-argument
        """ Get default object position 
            In unity, the vectors are in this order:
            [vector.z, -vector.x, vector.y]
        """
        return ik_pb2.Vector3(x=0.0, y=0.0, z=0.0)

    @staticmethod
    def get_default_object_orientation(object_name): #pylint: disable=unused-argument
        """ Get default object orientation 
            In unity, the vectors are in this order:
            [vector.z, -vector.x, vector.y]
            so yaw angle is y.
            x and z always default 0.0
        """
        return ik_pb2.Vector3(x=0.0, y=0.0, z=0.0)

    @staticmethod
    def translate_unity_object_name(unity_object_name):
        """ Translates unity object name into target object name """
        if unity_object_name in ("cubeRed", "redCube"):
            return '"red cube"'
        elif unity_object_name in ("cubeGreen", "greenCube"):
            return '"green cube"'
        elif unity_object_name in ("cubeBlue", "blueCube"):
            return '"blue cube"'
        elif unity_object_name == "cubeYellow":
            return '"yellow cube"'
        elif unity_object_name == "bowl":
            return '"bowl"'
        elif unity_object_name == "glass":
            return '"glass"'
        elif unity_object_name == "plate":
            return '"plate"'
        elif unity_object_name == "knife":
            return '"knife"'
        elif unity_object_name == "spoon":
            return '"spoon"'
        elif unity_object_name == "fork":
            return '"fork"'
        elif unity_object_name == "binGreen":
            return '"green bin"'
        elif unity_object_name == "binYellow":
            return '"yellow bin"'
        elif unity_object_name == "binBlue":
            return '"blue bin"'
        elif unity_object_name == "trashPaper":
            return '"paper"'
        elif unity_object_name == "trashFood":
            return '"banana"'
        elif unity_object_name == "trashMetal":
            return '"can"'
        elif unity_object_name == "sphereRed":
            return '"red ball"'
        elif unity_object_name == "sphereGreen":
            return '"green ball"'
        elif unity_object_name == "sphereYellow":
            return '"yellow ball"'
        elif unity_object_name == "goal":
            return '"goal area"'
        elif unity_object_name == "agentPosition":
            return '"robot base"'
        elif unity_object_name == '':
            return unity_object_name
        elif 'Wall' in unity_object_name or 'chair' in unity_object_name or \
             'Table' in unity_object_name: # Apparently this happens sometimes
            return ''
        elif unity_object_name == "robot":
            return unity_object_name
        else:
            raise ValueError(f"Unknown object name {unity_object_name}")

    @staticmethod
    def translate_target_object_name(target_object_name):
        """ Translates target object name into unity object name """
        if target_object_name == '"red cube"':
            return "cubeRed"
        elif target_object_name == '"green cube"':
            return "cubeGreen"
        elif target_object_name == '"blue cube"':
            return "cubeBlue"
        elif target_object_name == '"yellow cube"':
            return "cubeYellow"
        elif target_object_name == '"bowl"':
            return "bowl"
        else:
            raise ValueError(f"Unknown object name {target_object_name}")

    @staticmethod
    def get_grasp_offset(target_object):
        """
        Returns grasp offset for object
        """
        if target_object == '"bowl"':
            return np.array([0.0, -0.15, 0.07])
        elif target_object == '"can"':
            return np.array([0.0, 0.0, 0.15])
        elif target_object == '"glass"':
            return np.array([0.0, 0.0, 0.1])
        elif target_object == '"plate"':
            return np.array([0.0, -0.15, 0.03])
        elif target_object == '"banana"':
            return np.array([0.05, 0.0, 0.0])
        return np.array([0.0, 0.0, 0.0])

    def get_grasp_yaw(self, target_object):
        """
        Returns grasp yaw for object
        """
        if target_object == '"fork"' or target_object == '"spoon"' or target_object == '"knife"':
            return np.pi / 2
        return 0.0

if __name__ == '__main__':
    #Just for testing
    n_agents = 1 # pylint: disable=invalid-name
    interfaces = []
    interface_parameters = BaseWorldInterfaceParameters()
    for i in range(n_agents):
        interfaces.append(WorldInterface(interface_parameters, i))

    channel = 50010 # pylint: disable=invalid-name
    unity_proc = WorldInterface.start_unity_process(n_agents=n_agents, channel=50010)
    sim_client = SimClient(50010)
    steps = 0 # pylint: disable=invalid-name
    try:
        obs = WorldInterface.reset(sim_client)  # First empty step to start the environment and get first obs
        for i, msg in enumerate(obs.agents):
            interfaces[i].angles = np.array(msg.currentJointAnglesDeg)
            interfaces[i].index = msg.index
        while True:
            references = []

            for i, msg in enumerate(obs.agents):
                try:
                    interfaces[i].set_observation(msg)
                    if steps < 50:
                        target_position = interfaces[i].get_position('"red cube"')
                    elif steps >= 50 and steps < 100:
                        target_position = interfaces[i].get_position('"green cube"')
                    else:
                        target_position = interfaces[i].get_position('"blue cube"')
                    bowl_target_position = interfaces[i].get_position('"bowl"')

                    if steps > 50 and steps < 60 or steps > 100 and steps < 110:
                        interfaces[i].open_gripper()
                    else:
                        if not interfaces[i].grip_enabled and interfaces[i].grip_successful:
                            target_position = bowl_target_position + np.array([0, 0, 0.2])  # Move to above bowl

                        if interfaces[i].target_between_gripper:
                            interfaces[i].close_gripper()
                    interfaces[i].move_joint(target_position)
                    references.append(interfaces[i].get_references())
                except Exception as e:
                    print(e)

            obs = WorldInterface.send_parallel_references(sim_client, references)
            steps += 1
            if steps > 150: # Example of how to reset entire env. In this case, after every 25 steps.
                steps = 0 # pylint: disable=invalid-name
                obs = WorldInterface.reset(sim_client)

    except (KeyboardInterrupt, SystemExit):
        print("Server stopping...")  # Confirm server stopping

    unity_proc.terminate()
