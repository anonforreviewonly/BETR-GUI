"""Define the behavior list for cube pnp tasks."""

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
from behaviors import behavior_lists as bl
from behaviors.common_behaviors import NodeParameter, ParameterizedNode, ParameterTypes
import scenarios.behaviors as behaviors

def get_behavior_list(movable_objects=None,
                      static_objects=None,
                      container_objects=None,
                      relations=None,
                      sequence_nodes=None,
                      root_nodes=None,
                      mobile_base=True,
                      preplan_subtrees=True,
                      default_object_positions=None) -> bl.BehaviorLists:
    """Return the behavior list."""
    if movable_objects is None:
        movable_objects = []
    if static_objects is None:
        static_objects = []
    if relations is None:
        relations = []

    offset_parameter = NodeParameter([], (-0.2, -0.2, 0.0), (0.2, 0.2, 0.1), (0.02, 0.02, 0.02),
                                      data_type=ParameterTypes.POSITION, random_step=True, standard_deviation=0.04)
    base_offset_parameter = NodeParameter([], (-1.0, -1.0), (1.0, 1.0), (0.1, 0.1),
                                      data_type=ParameterTypes.XY_POSITION, random_step=True, standard_deviation=0.4)
    angle_parameter = NodeParameter([], round(-np.pi, 2), round(np.pi, 2), round(np.pi / 2, 2),
                                      data_type=ParameterTypes.FLOAT,
                                        random_step=True, standard_deviation=np.pi / 2)

    condition_nodes = []
    condition_nodes.append(ParameterizedNode(
        name='at pos',
        behavior=behaviors.AtPos,
        parameters={"target_object": NodeParameter(movable_objects),
                    "relative_object": NodeParameter(static_objects +  movable_objects),
                    "offset": offset_parameter,
                    "angle": angle_parameter},
        condition=True
        ))
    condition_nodes.append(ParameterizedNode(
        name='grasped',
        behavior=behaviors.Grasped,
        parameters={"target_object": NodeParameter(movable_objects)},
        condition=True
        ))
    if container_objects is not None:
        condition_nodes.append(ParameterizedNode(
            name='in',
            behavior=behaviors.InContainer,
            parameters={"target_object": NodeParameter(movable_objects),
                        "relative_object": NodeParameter(container_objects)},
            condition=True
        ))
    if mobile_base:
        condition_nodes.append(ParameterizedNode(
            name='robot at',
            behavior=behaviors.BaseAt,
            parameters={"target_object": NodeParameter(static_objects + movable_objects),
                        "offset": base_offset_parameter,
                        "angle": angle_parameter},
            condition=True
        ))
        condition_nodes.append(ParameterizedNode(
            name='robot near',
            behavior=behaviors.BaseNear,
            parameters={"target_object": NodeParameter(static_objects + movable_objects)},
            condition=True
        ))

    action_nodes = []

    action_nodes.append(
        ParameterizedNode(
            name='grasp',
            behavior=behaviors.Grasp,
            parameters={"target_object": NodeParameter(movable_objects)},
            condition=False
        ))
    action_nodes.append(
        ParameterizedNode(
            name='place',
            behavior=behaviors.Place,
            parameters={"target_object": NodeParameter(movable_objects),
                        "relative_object": NodeParameter(static_objects + movable_objects),
                        "offset": offset_parameter,
                        "angle": angle_parameter},
            condition=False
        ))
    if container_objects is not None:
        action_nodes.append(ParameterizedNode(
            name='place in',
            behavior=behaviors.PlaceIn,
            parameters={"target_object": NodeParameter(movable_objects),
                        "relative_object": NodeParameter(container_objects)},
            condition=False
        ))
    action_nodes.append(
        ParameterizedNode(
            name='idle',
            behavior=behaviors.Idle,
            parameters={},
            condition=False
        ))
    if mobile_base:
        action_nodes.append(
            ParameterizedNode(
                name='move to',
                behavior=behaviors.MoveBase,
                parameters={"target_object": NodeParameter(static_objects + movable_objects),
                            "offset": base_offset_parameter,
                            "angle": angle_parameter},
                condition=False,
                default_object_positions=default_object_positions
            ))

    if root_nodes is None:
        root_nodes = ['s(']

    behavior_list = bl.BehaviorLists(sequence_nodes=sequence_nodes, condition_nodes=condition_nodes, action_nodes=action_nodes,
                                     root_nodes=root_nodes, preplan_subtrees=preplan_subtrees)

    return behavior_list
