"""Unit test for base_world_interface.py module."""

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
from interfaces.unity_world_interface import WorldInterface
from interfaces.base_world_interface import BaseWorldInterfaceParameters

def test_transform_to_robot_frame():
    """ Test transform_to_robot_frame functionality."""
    # Create a BaseWorldInterface instance
    parameters = BaseWorldInterfaceParameters()
    world_interface = WorldInterface(parameters, 0)

    # Define a test object and its position
    test_object = "test_object"
    world_interface.set_object_position(test_object, np.array([1.0, 0.0, 0.0]))
    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), 0.0)

    # Transform the position to the robot frame
    world_interface.transform_to_robot_frame(test_object)

    # Check if the transformed position is correct
    expected_transformed_position = np.array([0.5, 0.0, 0.0])
    robot_frame_position = world_interface.get_position_robot_frame(test_object)
    assert np.allclose(expected_transformed_position, robot_frame_position)

    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), np.pi)
    world_interface.transform_to_robot_frame(test_object)
    expected_transformed_position = np.array([-0.5, 0.0, 0.0])
    robot_frame_position = world_interface.get_position_robot_frame(test_object)
    assert np.allclose(expected_transformed_position, robot_frame_position)

    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), np.pi / 2)
    world_interface.transform_to_robot_frame(test_object)
    expected_transformed_position = np.array([0.0, 0.5, 0.0])
    robot_frame_position = world_interface.get_position_robot_frame(test_object)
    assert np.allclose(expected_transformed_position, robot_frame_position)

    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), -np.pi / 2)
    world_interface.transform_to_robot_frame(test_object)
    expected_transformed_position = np.array([0.0, -0.5, 0.0])
    robot_frame_position = world_interface.get_position_robot_frame(test_object)
    assert np.allclose(expected_transformed_position, robot_frame_position)

def test_transform_to_world_frame():
    """ Test transform_to_world_frame functionality."""
    # Create a BaseWorldInterface instance
    parameters = BaseWorldInterfaceParameters()
    world_interface = WorldInterface(parameters, 0)

    # Define a test object and its position in robot frame
    test_object = "test_object"
    world_interface.object_position_robot_frame[test_object] = np.array([0.5, 0.0, 0.0])
    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), 0.0)

    # Transform the position to the world frame
    world_interface.transform_to_world_frame(test_object)

    # Check if the transformed position is correct
    expected_world_position = np.array([1.0, 0.0, 0.0])
    world_position = world_interface.get_position(test_object)
    assert np.allclose(expected_world_position, world_position)

    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), np.pi)
    world_interface.transform_to_world_frame(test_object)
    expected_world_position = np.array([0.0, 0.0, 0.0])
    world_position = world_interface.get_position(test_object)
    assert np.allclose(expected_world_position, world_position)

    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), np.pi / 2)
    world_interface.transform_to_world_frame(test_object)
    expected_world_position = np.array([0.5, -0.5, 0.0])
    world_position = world_interface.get_position(test_object)
    assert np.allclose(expected_world_position, world_position)

    world_interface.set_robot_base_position(np.array([0.5, 0.0, 0.0]), -np.pi / 2)
    world_interface.transform_to_world_frame(test_object)
    expected_world_position = np.array([0.5, 0.5, 0.0])
    world_position = world_interface.get_position(test_object)
    assert np.allclose(expected_world_position, world_position)

if __name__ == "__main__":
    test_transform_to_robot_frame()
    test_transform_to_world_frame()
    print("All tests passed.")
