"""Visualization window for running a Behavior Tree."""

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
import sys
from typing import Any

import time
import platform
from PyQt5 import QtGui, QtWidgets, QtCore

from bt_gui.bt_editor_scene import QBTGraphicsView
from bt_gui.base_graphic_scene import BaseScene
from bt_gui.bt_editor_elements import Node

if platform.system() == "Windows":
    import win32gui

class BehaviorTreeVisualizer(QtWidgets.QWidget):
    """Visualization window for running a Behavior Tree."""
    def __init__(self, backend: Any, parent=None, unity_hwnd=None, minimize_on_close=True) -> None: #pylint: disable=redefined-outer-name
        super().__init__(parent)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.setWindowTitle("Behavior Tree Visualizer")
        self.resize(1920, 1200)

        self.minimize_on_close = minimize_on_close
        self.backend = backend
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.bt_widget = QtWidgets.QWidget()
        self.bt_layout = QtWidgets.QVBoxLayout()
        self.bt_widget.setLayout(self.bt_layout)

        self.unity_widget = QtWidgets.QWidget()
        self.unity_layout = QtWidgets.QVBoxLayout()
        self.unity_widget.setLayout(self.unity_layout)
        self.graphics_view = QBTGraphicsView()
        self.scene = BaseScene(backend)

        self.graphics_view.setScene(self.scene)
        self.bottom_widget = QtWidgets.QWidget()
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.step_button = QtWidgets.QPushButton("Step and Pause simulation", font=font)
        self.step_button.clicked.connect(self.step_simulation)
        self.bottom_layout.addWidget(self.step_button)
        self.play_button = QtWidgets.QPushButton("Play simulation", font=font)
        self.play_button.clicked.connect(self.play_simulation)
        self.bottom_layout.addWidget(self.play_button)
        self.restart_button = QtWidgets.QPushButton("Reset simulation", font=font)
        self.restart_button.clicked.connect(self.restart_simulation)
        self.bottom_layout.addWidget(self.restart_button)
        self.bottom_widget.setLayout(self.bottom_layout)

        self.bt_layout.addWidget(self.graphics_view)
        self.status_label = QtWidgets.QLabel("Behavior Tree Status: Initializing...", font=font)
        self.bt_layout.addWidget(self.status_label)
        self.bt_layout.addWidget(self.bottom_widget)

        if platform.system() == "Windows" and unity_hwnd is not None:
            self.unity_window = QtGui.QWindow.fromWinId(unity_hwnd)
        else:
            self.unity_window = QtGui.QWindow()
        self.unity_window.setFlags(QtCore.Qt.FramelessWindowHint)
        self.unity_container = self.createWindowContainer(self.unity_window)
        self.unity_layout.addWidget(self.unity_container)

        # Create a splitter to hold the widgets
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)  # Horizontal splitter
        splitter.addWidget(self.bt_widget)
        splitter.addWidget(self.unity_widget)

        # Set initial sizes for the splitter
        splitter.setSizes([900, 900])
        self.main_layout.addWidget(splitter)
        self.node_list = []
        self.releaseMouse()

    def step_simulation(self):
        """ Steps simulation one step """
        self.backend.step_simulation()
        self.backend.log_event("Stepping simulation")

    def play_simulation(self):
        """ Plays simulation until finished """
        self.backend.play_simulation()
        self.backend.log_event("Playing simulation")

    def restart_simulation(self):
        """ Restarts simulation run """
        self.backend.stop_simulation()
        self.backend.reset_simulation()
        self.reset_tree()
        self.backend.log_event("Reset simulation")

    def visualize_tree(self, string_tree: list[str]) -> None: #pylint: disable=redefined-outer-name
        """Visualize the behavior tree in the scene."""
        self.scene = BaseScene(self.backend)
        self.graphics_view.setScene(self.scene)
        self.node_list = self.scene.load_bt(string_tree[:])

        # Make the connection points invisible
        for node in self.node_list:
            for point in node.connection_points:
                point.setPen(QtGui.QPen(QtCore.Qt.NoPen))

    def reset_tree(self) -> None:
        """Reset the behavior tree visualization, make all nodes gray."""
        for node in self.node_list:
            node.node_item.setPen(QtGui.QPen(QtGui.QColor("gray"), 5))
        self.status_label.setText("Behavior Tree Status: Initializing...")

    def update_tree(self, colors: list[QtGui.QColor], last_update=False) -> None:
        """Update the behavior tree visualization with new colors."""
        for i, node in enumerate(self.node_list):
            color = colors[i]
            node.node_item.setPen(QtGui.QPen(color, 5))
            if i == 0:
                self.update_status_label(color, last_update)

    def update_status_label(self, status_color: QtGui.QColor, last_update=False) -> None:
        """
        Update the status label in the GUI. 
        Would be better if we don't translate from colors but it works
        """
        if status_color == QtGui.QColor("green"):
            text = "Behavior Tree Status: Success"
        elif status_color == QtGui.QColor("red"):
            text = "Behavior Tree Status: Failure"
        elif status_color ==  QtGui.QColor("#fcd303"):
            if last_update:
                text = "Behavior Tree Status: Running (Stopped due to maximum allowed time exceeded)"
            else:
                text = "Behavior Tree Status: Running"
        else:
            text = "Behavior Tree Status: Invalid"
        self.status_label.setText(text)

    def _set_node_transparency(self, node: Node, alpha: int) -> None:
        """Set the transparency of a node."""
        pen = node.node_item.pen()
        color = pen.color()
        color.setAlpha(alpha)
        pen.setColor(color)
        node.node_item.setPen(pen)

        # Set brush transparency for filling
        brush = node.node_item.brush()
        fill_color = brush.color()
        fill_color.setAlpha(alpha)
        brush.setColor(fill_color)
        node.node_item.setBrush(brush)

    def closeEvent(self, evnt) -> None: #pylint: disable=invalid-name
        """ When closing, optionally only hide the window so it's faster to open next time """
        if self.minimize_on_close:
            self.hide()
            evnt.ignore()
            self.backend.log_event("Closed Behavior Tree Visualizer")
        else:
            self.backend.log_event("Closed Behavior Tree Visualizer and simulation")
            self.backend.close_backend()  # Close processes in the backend
            evnt.accept()


def get_unity_window(title="SimExample", timeout=20):
    """Wait for the Unity window to appear and returns handle"""
    if platform.system() != "Windows":
        return None

    hwnd = None
    for i in range(timeout):
        hwnd = win32gui.FindWindow(None, title) #pylint: disable=possibly-used-before-assignment
        if hwnd:
            break
        time.sleep(1)
    if i >= timeout:
        raise RuntimeError(f"Unity window with title '{title}' not found after {timeout} seconds.")
    return hwnd


if __name__ == "__main__":
    # Example usage
    from bt_gui.pytrees_backend import PytreesBackend #pylint: disable=ungrouped-imports
    from scenarios.trashpicking import get_environment #pylint: disable=ungrouped-imports
    app = QtWidgets.QApplication(sys.argv)

    if platform.system() == "Windows":
        use_planner = False
    else:
        use_planner = True

    vis_environment = get_environment(planner_environment=use_planner, n_agents=1)
    learning_environment = get_environment(planner_environment=True, n_agents=20)
    planner_environment = get_environment(planner_environment=True)

    from behaviors.common_behaviors import Goal
    from scenarios import behaviors
    CUBE_SIZE = 0.06
    goals = []

    goals = []
    goals.append(Goal(behaviors.InContainer, {"target_object": '"paper"',
                                                "relative_object": '"green bin"'}))
    goals.append(Goal(behaviors.InContainer, {"target_object": '"banana"',
                                            "relative_object": '"blue bin"'}))
    goals.append(Goal(behaviors.InContainer, {"target_object": '"can"',
                                            "relative_object": '"yellow bin"'}))
    vis_environment.par.goals = goals
    test = ['s(', 'f(', 'place "banana" in "blue bin"!', 's(', 'move to "banana" (-0.5, -0.3) 0.0!', 'grasp "banana"!', 'move to "blue bin" (0.4, 0.4) 1.57!', ')', ')', 'f(', 'place "can" in "yellow bin"!', 's(', 'move to "can" (-0.2, -0.4) -1.57!', 'grasp "can"!', 'move to "yellow bin" (0.4, 0.4) 1.57!', ')', ')', 'f(', 'place "paper" in "green bin"!', 's(', 'move to "paper" (-0.7, -0.5) -3.14!', 'grasp "paper"!', 'move to "green bin" (0.5, 0.1) -1.57!', ')', ')', ')']

    string_tree = test
    learning_environment.par.py_tree_parameters.behavior_lists.convert_from_string(string_tree)

    def simulation_result_callback(fitness, py_tree) -> None:
        """Update GUI with simulation step result."""
        print(f"Simulation finished. Fitness: {fitness}")
        print("Py tree status:", py_tree.root.status)

    backend = PytreesBackend(vis_environment, learning_environment, planner_environment, minimize_on_close=False)
    backend.set_simulation_result_callback(simulation_result_callback)
    backend.simulate_bt(string_tree[:])


    sys.exit(app.exec_())
