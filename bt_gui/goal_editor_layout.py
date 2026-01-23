"""Editor for goal layout"""

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
from typing import Any
import time
import numpy as np
from PyQt5 import QtGui, QtWidgets

from bt_gui.bt_editor_scene import EditorSceneWindow
from behaviors.common_behaviors import ParameterizedNode
from scenarios.behaviors import AtPos, Grasped, InContainer, BaseAt, BaseNear, MoveBase
from interfaces.base_world_interface import BaseWorldInterface


class GoalEditorLayout(QtWidgets.QVBoxLayout):
    """ Main layout for editing goals """
    def __init__(self, backend: Any, parent=None) -> None:
        super().__init__(parent)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.backend = backend

        editor_header_layout = QtWidgets.QHBoxLayout()
        self.editor_label = QtWidgets.QLabel("Behavior Tree Editor", font=font)

        self.icons_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons")

        self.save_button = QtWidgets.QPushButton("Save", font=font)
        save_icon = QtGui.QIcon(os.path.join(self.icons_folder, "disk--plus.png"))
        self.save_button.setIcon(save_icon)

        editor_header_layout.addWidget(self.editor_label)
        editor_header_layout.addWidget(self.save_button)

        self.addLayout(editor_header_layout)

        bt_editor_layout = QtWidgets.QVBoxLayout()
        bt_editor_layout.setContentsMargins(0, 0, 0, 0)

        # crate editor
        self.editor = EditorSceneWindow(backend)
        bt_editor_layout.addWidget(self.editor.get_widget())

        self.save_button.clicked.connect(self.save_goals)
        self.bt = None
        self.addLayout(bt_editor_layout)

    def load_LLM_goals(self, input_text: str) -> None: #pylint: disable=invalid-name
        """ Load goals from LLM into the editor """
        self.editor.load_bt_from_LLM(input_text)

    @staticmethod
    def find_target_objects(bt_remaining) -> dict:
        """ Find target objects in the behavior tree."""
        known_target_objects = {}
        for node in bt_remaining:
            if isinstance(node, ParameterizedNode):
                if node.behavior is AtPos:
                    target_object = node.parameters["target_object"].value
                    if target_object not in known_target_objects: #pylint: disable=consider-iterating-dictionary
                        known_target_objects[target_object] = 1
        return known_target_objects

    def get_object_pos(self, object_name, object_positions, known_target_objects):
        """ Get the position of an object if its known. """
        object_pos = None
        if object_name == '"origin"':
            return tuple(np.zeros(3))
        if object_name in object_positions:  #pylint: disable=consider-iterating-dictionary
            object_pos = object_positions[object_name]
        elif object_name not in known_target_objects:
            # If the relative object is not known and will not be known, we can use the default position
            object_pos = self.backend.get_default_object_position(object_name)
        return object_pos

    def check_for_removable_nodes(self, bt_remaining, object_positions, object_yaws, known_target_objects) -> None:
        """ Check for nodes that can be removed based on whether relative_object positions are known."""
        updated = False
        for i in range(len(bt_remaining) - 1, -1, -1):
            if isinstance(bt_remaining[i], ParameterizedNode):
                if bt_remaining[i].behavior is AtPos:
                    relative_object_pos = self.get_object_pos(bt_remaining[i].parameters["relative_object"].value, \
                                                              object_positions, known_target_objects)
                    if relative_object_pos is not None:
                        object_positions[bt_remaining[i].parameters["target_object"].value] = relative_object_pos + \
                                                                                                bt_remaining[i].parameters["offset"].value
                        object_yaws[bt_remaining[i].parameters["target_object"].value] = bt_remaining[i].parameters["angle"].value
                        updated = True
                        bt_remaining.pop(i)
                elif bt_remaining[i].behavior is Grasped:
                    # If the object is to be grasped, mark it as such
                    object_positions[bt_remaining[i].parameters["target_object"].value] = "grasped"
                    object_yaws[bt_remaining[i].parameters["target_object"].value] = 0.0
                    updated = True
                    bt_remaining.pop(i)
                elif bt_remaining[i].behavior is InContainer:
                    relative_object_pos = self.get_object_pos(bt_remaining[i].parameters["relative_object"].value, \
                                                              object_positions, known_target_objects)
                    if relative_object_pos is not None:
                        if "bin" in bt_remaining[i].parameters["relative_object"].value:
                            offset = np.array([0.0, 0.0, 0.04])
                        elif "goal area" in bt_remaining[i].parameters["relative_object"].value:
                            if "yellow ball" in bt_remaining[i].parameters["target_object"].value:
                                offset = np.array([0.0, 0.0, 0.15])
                            elif "green ball" in bt_remaining[i].parameters["target_object"].value:
                                offset = np.array([0.0, 0.0, 0.25])
                            else:
                                offset = np.array([0.0, 0.0, 0.02])
                        else:
                            offset = np.array([0.0, 0.0, 0.02])
                        object_positions[bt_remaining[i].parameters["target_object"].value] = relative_object_pos + \
                                                                                                offset
                        object_yaws[bt_remaining[i].parameters["target_object"].value] = 0.0
                        updated = True
                        bt_remaining.pop(i)
                elif bt_remaining[i].behavior is BaseAt:
                    target_object = bt_remaining[i].parameters["target_object"].value
                    target_object_pos = self.get_object_pos(target_object, \
                                                              object_positions, known_target_objects)
                    if target_object_pos is not None:
                        object_yaws['"robot base"'] = bt_remaining[i].parameters["angle"].value
                        object_positions['"robot base"'] = tuple(np.add(target_object_pos,  \
                                                                       (bt_remaining[i].parameters["offset"].value + (0.0,))))
                        updated = True
                        bt_remaining.pop(i)
                elif bt_remaining[i].behavior is BaseNear:
                    target_object = bt_remaining[i].parameters["target_object"].value
                    target_object_pos = self.get_object_pos(target_object, \
                                                            object_positions, known_target_objects)
                    default_object_positions = {target_object: target_object_pos}
                    if target_object_pos is not None:
                        object_yaws['"robot base"'] = MoveBase.get_default_parameter_value("angle", \
                                                                                          bt_remaining[i].parameters, \
                                                                                          default_object_positions)
                        offset = MoveBase.get_default_parameter_value("offset", \
                                                                       bt_remaining[i].parameters, \
                                                                       default_object_positions)
                        object_positions['"robot base"'] = tuple(np.add(target_object_pos, \
                                                                        (offset + (0.0,))))
                        updated = True
                        bt_remaining.pop(i)
                else:
                    # If the behavior is not recognized, just pop the node
                    bt_remaining.pop(i)
                    updated = True
            else:
                bt_remaining.pop(i)
                updated=True
        return updated

    def get_object_positions(self, bt) -> dict:
        """ 
        Get the object positions from the BT.
        Relative objects must be set first.
        """
        object_positions = {}
        object_positions['"table"'] = BaseWorldInterface.get_table_position()
        object_yaws = {}

        bt_remaining = bt[:]
        known_target_objects = GoalEditorLayout.find_target_objects(bt_remaining)
        updated = True
        while len(bt_remaining) > 0 and updated:
            updated = self.check_for_removable_nodes(bt_remaining, object_positions, object_yaws, known_target_objects)

        valid = True
        if len(bt_remaining) > 0:
            valid = False
            print("Error, some goals could not be extracted, most likely due to a circular reference")
            for node in bt_remaining:
                print(node)
            text = "Some goals could not be extracted, most likely due to a circular reference. \n"
            text += "Make sure objects don't depend on each other in a cycle."
            QtWidgets.QMessageBox.warning(
                self.parentWidget(),
                "Invalid goals",
                text,
            )
            self.backend.log_event("Save goals failed: Circular reference")
        return valid, object_positions, object_yaws

    def save_goals(self) -> None:
        """ Save the goals from the editor to the backend """
        try:
            if not self._goals_valid():
                return
            new_bt = self.editor.get_and_clean_current_bt()[0]
            if new_bt is not None:
                new_bt = new_bt.bt.bt
                if new_bt != self.bt:
                    valid, object_positions, object_yaws = self.get_object_positions(new_bt[:])
                    if valid:
                        self.bt = new_bt[:]
                        self.backend.set_goal_positions(object_positions, object_yaws)
                        self.backend.start_goal_simulation()

                        max_waits = 200
                        waits = 0
                        while self.backend.visualizing_goal and waits < max_waits:
                            QtWidgets.QApplication.processEvents()  # Wait until the positions are set in the simulation
                            time.sleep(0.1) # To avoid busy waiting
                            waits += 1
                        if waits >= max_waits:
                            QtWidgets.QMessageBox.warning(
                            self.parentWidget(),
                            "Warning, goals could not be set",
                            "The goals could not be set in the simulation due to timeout. Please try again with different goals.",
                            )
                            self.backend.log_event("Warning, goals not correct due to timeout")
                        else:
                            failing_objects = []
                            for obj_name, obj_pos in object_positions.items():
                                if isinstance(obj_pos, np.ndarray):
                                    simulated_pos = self.backend.get_current_object_position(obj_name)
                                    if isinstance(simulated_pos, np.ndarray):
                                        if np.linalg.norm(simulated_pos - obj_pos) > 0.01:
                                            failing_objects.append(obj_name)

                            if failing_objects:
                                QtWidgets.QMessageBox.warning(
                                    self.parentWidget(),
                                    "Warning, goals could not be set",
                                    "The following objects could not be set correctly in the simulation, likely due to collision: " + \
                                    ", ".join(failing_objects),
                                )
                                self.backend.log_event("Warning, goals not correct for: " + str(failing_objects))
                            else:
                                # Set the goals in the environment
                                self.backend.set_goals_from_tree(new_bt)

                                # Enable the editor tab in the main window
                                main_window = self.parentWidget().window()  # Get the MainWindow instance
                                if hasattr(main_window, "enable_editor_tab"):
                                    main_window.enable_editor_tab()
                                    bt_data = self.backend.get_bt_data_from_tree(new_bt)
                                    main_window.load_goals_to_editor(bt_data)

                                self.backend.log_event("Saved goals: " + str(self.bt))
                                    # Jump to the editor tab
                                    # main_window.tabs.setCurrentWidget(main_window.editor_tab)
        except ValueError as e:
            print(e)

    def _goals_valid(self) -> bool:
        current_targets = []
        goal_valid = True
        for item in self.editor.get_scene().get_nodes():
            param_node, _ = self.backend.get_behavior_from_name(self.backend.node_to_string(item))
            try:
                parameters = param_node.get_parameters()
            except AttributeError:
                continue

            if parameters["target_object"] not in current_targets:
                current_targets.append(parameters["target_object"])
            else:
                goal_valid = False
                break

        if not goal_valid:
            text = "More than one condition node has the same target item.\n"
            text += "Please modify such nodes accordingly."
            QtWidgets.QMessageBox.warning(
                self.parentWidget(),
                "Invalid Goals",
                text,
            )
            self.backend.log_event("Save goals failed: Multiple goals with same target")

        return goal_valid
