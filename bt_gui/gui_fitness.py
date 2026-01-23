""" Contains the class for defining the fitness function/goals of the scenario."""
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
from PyQt5 import QtCore, QtGui, QtWidgets

from bt_gui.goal_editor_layout import GoalEditorLayout
from bt_gui.goal_layout import GoalState
from bt_gui.skills_list_layout import SkillLayout
from bt_gui.pytrees_backend import BackendVariants
from bt_gui.popup_hints import PopupHint

class FitnessWindow(QtWidgets.QWidget):
    """Main window for defining the fitness function/goals of the scenario."""
    def __init__(self, backend: Any) -> None: #pylint: disable=redefined-outer-name
        super().__init__()

        self.backend = backend

        self.setWindowTitle("Goal Editor")
        self.resize(1490, 800)

        self.icons_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons")

        # Set up the layout
        self.main_layout = QtWidgets.QVBoxLayout(self)

        if self.backend.backend_variant not in (BackendVariants.MANUAL_ONLY, BackendVariants.NO_LLM):
            # Task Layout: where the target task is defined in natural language
            self.task_layout = QtWidgets.QHBoxLayout()

            self.task_input = QtWidgets.QPlainTextEdit()
            self.task_input.setPlaceholderText("Define your input task here...")

            font = QtGui.QFont()
            font.setPointSize(10)
            font.setItalic(True)
            self.task_input.setFont(font)
            self.task_input.setFixedHeight(100)
            self.task_layout.addWidget(self.task_input)

            self.translate_button = QtWidgets.QPushButton("Convert to tree")
            self.task_layout.addWidget(self.translate_button)
            self.main_layout.addLayout(self.task_layout)

        # BT Layout: where the BT is created
        self.bt_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.bt_layout)

        # Skill Layout: where the robot skills are listed
        self.skill_widget = QtWidgets.QWidget()
        self.skill_layout = SkillLayout(self.backend, goal_definition=True)
        self.skill_widget.setLayout(self.skill_layout)

        # Goal State: where the simulation output the current goal state
        self.goal_state_widget = GoalState(self.backend)

        # BT Editor layout: where the BT can be manually designed
        self.editor_widget = QtWidgets.QWidget()
        self.editor_layout = GoalEditorLayout(self.backend)
        self.editor_widget.setLayout(self.editor_layout)

        # Use the button to prompt the LLM with the natural language task description
        def process_text() -> None:
            """Function to get text from QLineEdit and send it somewhere."""
            input_text = self.task_input.toPlainText()  # Get text from input field
            self.editor_layout.load_LLM_goals(input_text)

        if self.backend.backend_variant not in (BackendVariants.MANUAL_ONLY, BackendVariants.NO_LLM):
            self.translate_button.clicked.connect(process_text)

        # Create a splitter to hold the widgets
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)  # Horizontal splitter
        splitter.addWidget(self.skill_widget)
        splitter.addWidget(self.editor_widget)
        splitter.addWidget(self.goal_state_widget)

        # Set initial sizes for the splitter
        splitter.setSizes([200, 500, 400])
        self.bt_layout.addWidget(splitter)

        if self.backend.backend_variant not in (BackendVariants.MANUAL_ONLY, BackendVariants.NO_LLM):
            hint_text = "\U0001F854 Don't forget that you can describe the goal in text and have it converted into a tree!"
            self.llm_hint_label = PopupHint(self, hint_text, size=(350, 50), position=(200, 75))
            self.llm_hint_label.show()
        goal_hint_text = "This is where you define the goal state as goal conditions that the robot can understand. " + \
                         "The policy to actually achieve it is defined in the next step."
        self.goal_hint_label = PopupHint(self, goal_hint_text,
            size=(330, 100), position=(600, 400))
        self.goal_hint_label.show()

    def tab_entered(self) -> None:
        """Function to be called when the tab is entered."""
        if self.backend.backend_variant not in (BackendVariants.MANUAL_ONLY, BackendVariants.NO_LLM):
            self.llm_hint_label.show()


if __name__ == "__main__":
    import sys
    from scenarios.cubes_and_bowl import get_environment
    from bt_gui.pytrees_backend import PytreesBackend #pylint: disable=ungrouped-imports

    app = QtWidgets.QApplication(sys.argv)
    environment = get_environment(planner_environment=True)
    backend = PytreesBackend(environment, environment)

    main_window = FitnessWindow(backend)
    main_window.show()
    main_window.raise_()

    sys.exit(app.exec_())
