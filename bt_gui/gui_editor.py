""" Contains the class for the main editor window of the GUI."""
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
import time
from typing import Any
from PyQt5 import QtCore, QtGui, QtWidgets

from bt_gui.pytrees_backend import BackendVariants
from bt_gui.ai_layout import AILayout
from bt_gui.bt_editor_layout import BTEditorLayout
from bt_gui.skills_list_layout import SkillLayout
from bt_gui.popup_hints import PopupHint


class EditorWindow(QtWidgets.QWidget):
    """Main window for the Behavior Tree Editor."""
    def __init__(self, backend: Any) -> None: #pylint: disable=redefined-outer-name
        super().__init__()
        font = QtGui.QFont()
        font.setPointSize(8)
        self.backend = backend

        self.setWindowTitle("Behavior Tree Editor")
        self.resize(1490, 800)

        self.icons_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons")

        # Set up the layout
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # BT Layout: where the BT is created
        self.bt_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.bt_layout)

        # Skill Layout: where the robot skills are listed
        self.skill_widget = QtWidgets.QWidget()
        self.skill_layout = SkillLayout(self.backend)
        self.skill_widget.setLayout(self.skill_layout)

        # BT Editor layout: where the BT can be manually designed
        self.editor_widget = QtWidgets.QWidget()
        self.editor_layout = BTEditorLayout(self.backend, update_score_callback=self.show_sending_hint)
        self.editor_widget.setLayout(self.editor_layout)

        if self.backend.backend_variant != BackendVariants.MANUAL_ONLY:
            # BT Connection layout: where the BT can be sent to or received from the AI
            self.connection_widget = QtWidgets.QWidget()
            self.connection_widget.setMaximumWidth(70)
            self.connection_layout = QtWidgets.QVBoxLayout()
            self.connection_widget.setLayout(self.connection_layout)

            self.send_button = QtWidgets.QPushButton("Send", font=font)
            send_icon = QtGui.QIcon(os.path.join(self.icons_folder, "control.png"))
            self.send_button.setIcon(send_icon)
            # Place the text on the left and icon on the right
            self.send_button.setLayoutDirection(
                QtCore.Qt.RightToLeft # type: ignore
            )
            self.send_button.setFixedSize(60, 30)
            self.connection_layout.addWidget(self.send_button)

            self.load_button = QtWidgets.QPushButton("Load", font=font)
            load_icon = QtGui.QIcon(os.path.join(self.icons_folder, "control-180.png"))
            self.load_button.setIcon(load_icon)
            self.load_button.setFixedSize(60, 30)
            self.connection_layout.addWidget(self.load_button)


            # AI layout: where the BT is provided by the AI
            self.ai_widget = QtWidgets.QWidget()
            self.ai_layout = AILayout(self.backend, ai_update_callback=self.show_ai_hint)
            self.ai_widget.setLayout(self.ai_layout)

            self.send_button.clicked.connect(self.send_to_ai)
            self.send_button_clicked = False

            self.load_button.clicked.connect(
                lambda: self.load_to_editor(self.ai_layout.learning_interface.best_bt)
            )
        else:
            self.ai_layout = None

        # Create a splitter to hold the widgets
        splitter = QtWidgets.QSplitter()  # Horizontal splitter
        splitter.addWidget(self.skill_widget)
        splitter.addWidget(self.editor_widget)
        if self.backend.backend_variant != BackendVariants.MANUAL_ONLY:
            splitter.addWidget(self.connection_widget)
            splitter.addWidget(self.ai_widget)

        # Set initial sizes for the splitter
        splitter.setSizes([50, 500, 70, 400])
        self.bt_layout.addWidget(splitter)
        self.last_time_sent_to_ai = time.time()
        self.start_time = 0
        self.start_time_set = False
        self.locking_structure_hint_shown = False # Only show once
        self.sending_hint_label = None
        if self.backend.backend_variant != BackendVariants.MANUAL_ONLY:
            self.locking_hint_label = PopupHint(self, "Remember to lock nodes you are satisfied with to make the AI work faster!",
                                                size=(330, 50), position=(200, 75))
            self.locking_structure_hint_label = PopupHint(self,
                                                          "Remember that you can also lock the entire structure of the tree! " + \
                                                          "The AI is much faster when it only needs to optimize parameters!",
                                                          size=(350, 80), position=(200, 75))
            self.sending_hint_label = PopupHint(self,
                                                "Remember to send your behavior tree to the AI! " + \
                                                "The AI can work much faster from a good starting point!",
                                                size=(300, 80), position=(200, 75))
            self.ai_hint_label = PopupHint(self, "The AI just found an improved tree!",
                        size=(400, 100), position=(1300, 900))
            large_font = QtGui.QFont()
            large_font.setPointSize(12)
            self.ai_hint_label.setFont(large_font)
            self.ai_hint_label.setAlignment(QtCore.Qt.AlignCenter)
            self.ai_hint_label.setMargin(10)
            self.ai_hint_label.timeline = QtCore.QTimeLine(20000, self.ai_hint_label)
            self.ai_hint_label.timeline.setFrameRange(0, 100)
            self.ai_hint_label.timeline.setUpdateInterval(200)
            self.ai_hint_label.timeline.frameChanged.connect(self.ai_hint_label.set_anim_number)

    def load_to_editor(self, bt_data, clear_scene=False) -> None:
        """Load a behavior tree into the editor from a list of strings."""
        if clear_scene:
            self.editor_layout.clear_scene()
        else:
            #Means we pressed the button
            self.ai_hint_label.hide()
        self.editor_layout.load_bt(bt_data.bt[:])
        self.editor_layout.update_best(bt_data)
        self.editor_layout.update_last(bt_data)
        self.editor_layout.update_score_label(bt_data)
        self.backend.log_event("Loaded BT to editor: " + str(bt_data.bt))

    def get_best_score(self) -> Any:
        """Get the best behavior tree from the AI layout."""
        return self.editor_layout.get_best_score()

    def stop_ai_simulation(self):
        """Stop the AI simulation."""
        if self.ai_layout is not None:
            self.ai_layout.stop_simulation()

    def start_ai_simulation(self) -> None:
        """Start the AI simulation."""
        if self.ai_layout is not None:
            self.ai_layout.start_simulation()

    def get_current_tree(self) -> Any:
        """Get the current behavior tree from the editor layout."""
        return self.editor_layout.get_current_tree()

    def send_to_ai(self) -> None:
        """Send the behavior tree as a baseline to the AI for optimization."""
        if not self.send_button_clicked and self.ai_layout is not None: #Protect against button spamming problems
            self.send_button_clicked = True
            self.stop_ai_simulation()
            try:
                tree, mask = self.editor_layout.get_and_clean_current_bt()
                if tree is not None:
                    self.ai_layout.learning_interface.send_bt_to_ai(tree, mask)
                    self.last_time_sent_to_ai = time.time()
                    self.sending_hint_label.hide()
                    if not isinstance(mask, list) or not any(mask):
                        send_button_position = self.send_button.mapTo(self, QtCore.QPoint(0, 0))
                        self.locking_hint_label.move(send_button_position.x() - 300, send_button_position.y() - 50)
                        self.locking_hint_label.show()
                    else:
                        self.locking_hint_label.hide()
                    if not self.ai_layout.has_locked_structure and not self.locking_structure_hint_shown and \
                            self.start_time_set and time.time() - self.start_time > 600: # 10 minutes until this is needed
                        send_button_position = self.send_button.mapTo(self, QtCore.QPoint(0, 0))
                        self.locking_structure_hint_label.move(send_button_position.x() + 310, send_button_position.y() - 300)
                        self.locking_structure_hint_label.show()
                        self.locking_structure_hint_shown = True
                    else:
                        self.locking_structure_hint_label.hide()
                    self.backend.log_event("Sent BT to AI: " + str(tree.bt.bt) + " with mask: " + str(mask))
            except ValueError as e:
                QtWidgets.QMessageBox.warning(
                    self.parentWidget(),
                    "Invalid Behavior Tree",
                    str(e),
                )
            self.start_ai_simulation()
            self.send_button_clicked = False

    def set_start_time(self) -> None:
        """Set the start time for the editor window."""
        if not self.start_time_set:
            self.start_time = time.time()
            self.start_time_set = True

    def show_sending_hint(self) -> None:
        """Show the sending hint label."""
        if self.sending_hint_label is not None and time.time() - self.last_time_sent_to_ai > 200: # 200 seconds
            send_button_position = self.send_button.mapTo(self, QtCore.QPoint(0, 0))
            self.sending_hint_label.move(send_button_position.x() - 320, send_button_position.y() - 70)
            self.sending_hint_label.show()

    def show_ai_hint(self) -> None:
        """Show the AI hint label."""
        if self.ai_hint_label is not None:
            load_button_position = self.load_button.mapTo(self, QtCore.QPoint(0, 0))
            self.ai_hint_label.move(load_button_position.x() + 200, load_button_position.y() - 50)
            self.ai_hint_label.show()


if __name__ == "__main__":
    import sys
    from scenarios.cubes_and_bowl import get_environment
    from bt_gui.pytrees_backend import PytreesBackend #pylint: disable=ungrouped-imports

    app = QtWidgets.QApplication(sys.argv)
    vis_environment = get_environment(planner_environment=True, n_agents=1)
    learning_environment = get_environment(planner_environment=True, n_agents=20)
    planner_environment = get_environment(planner_environment=True)
    backend = PytreesBackend(vis_environment, learning_environment, planner_environment)

    main_window = EditorWindow(backend)
    main_window.show()
    main_window.raise_()

    sys.exit(app.exec_())
