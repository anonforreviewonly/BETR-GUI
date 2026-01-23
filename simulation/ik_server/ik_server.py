import logging
import os
import random
import subprocess
import time
from io import StringIO, BytesIO

import numpy.linalg
from scipy.spatial.transform import Rotation as R

import ikpy.chain
import numpy as np
import requests
from PIL import Image
from google.protobuf.message import DecodeError

try:
    from simulation.ik_server.generated import ik_pb2
except ImportError:
    from generated import ik_pb2


class SimClient:
    def __init__(self, port):
        self.port = port

    def screenshot(self, message: ik_pb2.TakeScreenshot):
        image_png_bytes = self.do_request(ik_pb2.TakeScreenshot.SerializeToString(message), "admin/screenshot")
        return image_png_bytes

    def get_screenshot(self, camera_position=None):
        """ 
        Takes and returns a screenshot of the current generated .
        Works with "-headless", "-batchmode" but not with "-nographics"
         """
        if camera_position is None:
            position = ik_pb2.Vector3(x=-0.7, y=0.9, z=1.7)
            euler = ik_pb2.Vector3(x=35, y=150, z=0)
        else:
            position = camera_position.position
            euler = camera_position.euler
        scr = self.do_request(ik_pb2.TakeScreenshot.SerializeToString(ik_pb2.TakeScreenshot(position=position,
                                                                                            orientationEuler=euler)),
                              "admin/screenshot")
        return Image.open(BytesIO(scr))

    def configure(self):
        pass  # TODO: Working, but needs an example. See proto if in a hurry.

    def reset(self, message: ik_pb2.Reset):
        attempts = 0
        while attempts < 20:
            try:
                obs_bytes = self.do_request(ik_pb2.Reset.SerializeToString(message), "reset", timeout=10)
                observations = ik_pb2.Observations.FromString(obs_bytes)
                break
            except DecodeError:
                print("Bad host issue, retrying...")
                time.sleep(1)
                attempts += 1
        return observations

    def step(self, message: ik_pb2.Step):
        obs_bytes = self.do_request(ik_pb2.Step.SerializeToString(message), "step")
        observations = ik_pb2.Observations.FromString(obs_bytes)
        return observations

    def do_request(self, msg, method, **kwargs):
        attempts = 0
        while attempts < 20:
            try:
                response = requests.post(
                    f'http://localhost:{self.port}/{method}',
                    data=msg,
                    headers={
                        'Content-Type': 'application/octet-stream',
                    },
                    **kwargs
                )
                return response.content
            except (ConnectionRefusedError, ConnectionError, requests.exceptions.ConnectionError) as e:
                print(e)
                print("Connection refused, retrying...")
                time.sleep(1)
                attempts += 1

        print("Failed to connect after multiple attempts.")
        return None


class ExampleManager:
    def __init__(self, chain):
        self.agent_ids = None
        self.chain = chain
        self.grip_enabled = dict()
        self.angles_rad = None

    def reset(self):
        self.grip_enabled = dict()

    def handle_agent_observation(self, observation):
        joint_angles = np.array(observation.currentJointAnglesDeg)

        item = self.vector_from_unity_to_ikpy(observation.transformsByNameArmFrame["sphereRed"].position)
        container = self.vector_from_unity_to_ikpy(observation.transformsByNameArmFrame["goal"].position)

        target_position = item
        if observation.index == 0: target_position += np.array([0, 0, 0.01])
        if observation.index == 1: target_position += np.array([0, 0, 0.1])

        target_rotation = np.array([0, 0, -1])  # Use orientation above
        if self.grip_enabled.get(observation.index, False) and observation.gripSuccessful:
            target_position = container + np.array([0, 0, 0.5])  # Move to above container

        if self.grip_enabled.get(observation.index, False) and numpy.linalg.norm(np.array(item) - target_position) < 0.05:
            print("disable grip")
            self.grip_enabled[observation.index] = False

        if (observation.isBetweenGripper and
                (observation.betweenGripper == "sphereRed" or observation.betweenGripper == "trashPaper" or observation.betweenGripper == "glass")
                and not self.grip_enabled.get(observation.index, False)):
            self.grip_enabled.setdefault(observation.index, True)

        # angles = self.do_fake_ik(self.grip_enabled.get(agent_request.index, False))
        angles = self.do_ik(self.chain, target_position, target_rotation, joint_angles)

        return angles

    def build_agent_controls(self, agent_index, angles):
        step = ik_pb2.AgentControls(
            targetBasePose=ik_pb2.Transform(position=ik_pb2.Vector3(x=0, y=0, z=0.2),
                                            euler=ik_pb2.Vector3(x=0, y=0, z=0)
                                            )
        )
        if angles is not None:
            step.jointTargetsDeg.extend(angles)
        step.activateGrip = self.grip_enabled.get(agent_index, False)  # Basically, stupid logic for example. If object detected once, grasp and never let go.
        step.index = agent_index
        return step

    def vector_from_unity_to_ikpy(self, vector):
        return [vector.z, -vector.x, vector.y]

    def do_ik(self, chain, target_position, target_rotation, joints):
        angles_rad = chain.inverse_kinematics(
            target_position=target_position,
            initial_position=[0, 0, 0, 0, 0, 0, 0, 0],
            target_orientation=target_rotation,
            orientation_mode="X"
        )

        angles = np.degrees(angles_rad[1:-1])
        return angles

    def do_fake_ik(self, state):
        # Just to ensure the arm keeps moving in sim and the physics engine is actually doing the same movements in both cases.
        if state:
            return np.array([-1.46103706e+01, 1.25179298e+01, 3.45932007e+01, 1.75054123e-15, 4.28888694e+01, -0.00000000e+00])
        return np.array([1.00921824e+01, 2.48341571e+01, 4.97829810e+01, -1.30461950e-06, 1.53828621e+01 - 7.32538819e-01])

    def record_ids(self, obs):
        self.agent_ids = np.array([msg.index for msg in obs.agents])


def start_example_manager():
    urdf_path = os.path.join(os.path.dirname(__file__), '../Assets/URDF/crb15000_5_95_gripper.urdf')
    chain = ikpy.chain.Chain.from_urdf_file(urdf_path, active_links_mask=[False, True, True, True, True, True, False, False])  # Turn links on / off for IK
    return ExampleManager(chain)


def start_client(channel_port):
    client = SimClient(channel_port)
    print("Client started, configured for port " + str(channel_port))  # Confirm server started
    return client


def start_unity_process(agent_nr, port):
    executable_path = os.path.join(os.path.dirname(__file__), '../Builds/Win/SimExample.exe')
    popen = subprocess.Popen([executable_path,
                              "-agents", str(agent_nr),  # Number of agents
                              "-logfile", "unity.log",
                              "-channel", str(port),  # Param to change connection port. If you want to start multiple instances
                              "-timescale", "1",  # Param to change sim speed
                              "-decisionperiod", "10",  # Time step is 0.02 (50hz). Run control every 10 steps (0.2 - 5hz)
                              "-environment", "spheres"  # trashpicking, cubebowl, tableware, spheres
                                              #"-headless", "-batchmode",  # "-nographics" # Params for no-graphics
                              ])
    print("Started Unity process")
    return popen


def example_screenshot():
    # Works with "-headless", "-batchmode" but not with "-nographics"
    scr = sim_client.screenshot(ik_pb2.TakeScreenshot(position=ik_pb2.Vector3(x=0, y=4, z=0.5),
                                                      orientationEuler=ik_pb2.Vector3(x=90, y=0, z=0)))
    image = Image.open(BytesIO(scr))
    image.show()


def custom_reset(ids):
    reset_msg = ik_pb2.Reset(
        cameraPosition=ik_pb2.Transform(
            position=ik_pb2.Vector3(x=0, y=4, z=0),
            euler=ik_pb2.Vector3(x=0, y=90, z=0),
        ))
    for i, idx in enumerate(ids):
        # parameters = ik_pb2.ResetParameters(
        #     index=idx,
        #     envCubeBowl=ik_pb2.EnvCubeBowlParameters(
        #         bowl=ik_pb2.Transform(position=ik_pb2.Vector3(x=0.350, y=0.0629, z=0.705)),
        #         cubeRed=ik_pb2.Transform(position=ik_pb2.Vector3(x=0.034, y=0.12, z=0.8)),
        #         cubeGreen=ik_pb2.Transform(position=ik_pb2.Vector3(x=0.034, y=0.06, z=0.8)),
        #         cubeYellow=ik_pb2.Transform(position=ik_pb2.Vector3(x=0.034, y=0.18, z=0.8)),
        #         cubeBlue=ik_pb2.Transform(position=ik_pb2.Vector3(x=-0.40, y=0.5, z=0.697))
        #     ),
        # )

        # parameters = ik_pb2.ResetParameters(
        #     index=idx,
        #     envTrashPicking=ik_pb2.EnvTrashPickingParameters(
        #         agentPosition=ik_pb2.Transform(position=ik_pb2.Vector3(x=0, y=0, z=-2), euler=ik_pb2.Vector3(y=90)),
        #         binBlue=ik_pb2.Transform(position=ik_pb2.Vector3(x=3, y=0, z=3), euler=ik_pb2.Vector3(x=-90)),
        #         binYellow=ik_pb2.Transform(position=ik_pb2.Vector3(x=3, y=1, z=3), euler=ik_pb2.Vector3(x=-90)),
        #         binGreen=ik_pb2.Transform(position=ik_pb2.Vector3(x=3, y=2, z=3), euler=ik_pb2.Vector3(x=-90)),
        #         trashFood=ik_pb2.Transform(position=ik_pb2.Vector3(x=-3, y=0, z=3), euler=ik_pb2.Vector3(x=-90)),
        #         trashMetal=ik_pb2.Transform(position=ik_pb2.Vector3(x=-3, y=0.1, z=3), euler=ik_pb2.Vector3(x=-90)),
        #         trashPaper=ik_pb2.Transform(position=ik_pb2.Vector3(x=-3, y=0.2, z=3), euler=ik_pb2.Vector3(x=-90)),
        #     ),
        # )

        # parameters = ik_pb2.ResetParameters(
        #     index=idx,
        #     envTableware=ik_pb2.EnvTablewareParameters(
        #         agentPosition=ik_pb2.Transform(position=ik_pb2.Vector3(x=0, y=0, z=-2), euler=ik_pb2.Vector3(y=90)),
        #         fork=ik_pb2.Transform(position=ik_pb2.Vector3(x=0.034, y=0.12, z=0.85)),
        #         plate=ik_pb2.Transform(position=ik_pb2.Vector3(x=0.034, y=0.06, z=0.8)),
        #         glass=ik_pb2.Transform(position=ik_pb2.Vector3(x=0.034, y=0.18, z=0.8)),
        #         spoon=ik_pb2.Transform(position=ik_pb2.Vector3(x=-0.40, y=0.5, z=0.697)),
        #         knife=ik_pb2.Transform(position=ik_pb2.Vector3(x=-0.40, y=0.6, z=0.697)),
        #     ),
        # )

        parameters = ik_pb2.ResetParameters(
            index=idx,
            envSpheres=ik_pb2.EnvSpheresParameters(
                agentPosition=ik_pb2.Transform(position=ik_pb2.Vector3(x=0, y=0, z=-2), euler=ik_pb2.Vector3(y=90)),
                sphereRed=ik_pb2.Transform(position=ik_pb2.Vector3(x=3, y=0, z=3), euler=ik_pb2.Vector3(x=-90)),
                sphereGreen=ik_pb2.Transform(position=ik_pb2.Vector3(x=3, y=1, z=3), euler=ik_pb2.Vector3(x=-90)),
                sphereYellow=ik_pb2.Transform(position=ik_pb2.Vector3(x=3, y=2, z=3), euler=ik_pb2.Vector3(x=-90)),
                goal=ik_pb2.Transform(position=ik_pb2.Vector3(x=3, y=0, z=3), euler=ik_pb2.Vector3(x=0)),
            ),
        )

        reset_msg.envsToReset.append(parameters)

    return reset_msg


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    agents = 3
    channel = 50010

    unity_proc = start_unity_process(agents, channel)
    example_manager = start_example_manager()
    sim_client = start_client(channel)
    time.sleep(1)

    steps = 0
    i = 0
    timeScaleVar = 1
    try:
        resetMsg = ik_pb2.Reset()
        resetMsg.reloadScene = True

        while True:
            timest = time.time()
            random.seed(42)
            np.random.seed(42)

            agentIds = list(range(0, agents))
            obs = sim_client.reset(custom_reset(agentIds))
            example_manager.record_ids(obs)  # First empty step to start the environment and get first obs

            while steps < 0:
                stepMsg = ik_pb2.Step()
                stepMsg.stepCount = 10  # Optional, can configure how many sim steps to take every step. Overrides "decisionperiod" from startup for one step.
                stepMsg.timeScale = timeScaleVar  # Optional, can configure how fast sim moves w.r.p real time. Overrides "timescale" from startup for one step.

                for msg in obs.agents:
                    try:
                        angles = example_manager.handle_agent_observation(msg)
                        control = example_manager.build_agent_controls(msg.index, angles if steps < 3 else None)

                        stepMsg.controls.append(control)
                    except Exception as e:
                        print(e)

                obs = sim_client.step(stepMsg)
                steps += 1
                # example_screenshot()
            i += 1
            print(f"Timescale: {timeScaleVar} : {time.time() - timest} : {i}")

            steps = 0
            example_manager.reset()


    except (KeyboardInterrupt, SystemExit):
        print("Server stopping...")  # Confirm server stopping
    unity_proc.terminate()
