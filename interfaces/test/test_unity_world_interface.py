"""Unit test for unity_world_interface.py module."""

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
import numpy as np
import ikpy.chain
from interfaces.unity_world_interface import WorldInterface
from interfaces.base_world_interface import BaseWorldInterfaceParameters

def test_ik():
    """ Test inverse kinematics functionality."""
    parameters = BaseWorldInterfaceParameters()
    urdf_path = os.path.join(os.path.dirname(__file__), '../../simulation/Assets/URDF/crb15000_5_95_gripper.urdf')
    parameters.chain = ikpy.chain.Chain.from_urdf_file(urdf_path,
        active_links_mask=[False, True, True, True, True, True, True, False])  # Turn links on / off for IK
    world_interface = WorldInterface(parameters, 0)
    target_position = [0.5, 0.0, 0.3]
    target_orientation = world_interface.get_orientation_from_yaw(np.pi / 2)
    assert world_interface.do_ik(target_position=target_position, target_orientation=target_orientation)
    joint_reference = world_interface.joint_reference

    for _ in range(10):
        assert world_interface.do_ik(target_position=target_position, target_orientation=target_orientation)
        assert np.allclose(world_interface.joint_reference, joint_reference), "IK solution should be consistent across calls."


if __name__ == "__main__":
    test_ik()
    print("All tests passed.")
