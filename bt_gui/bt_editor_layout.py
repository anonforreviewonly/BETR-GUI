"""Behavior tree editor layout."""

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
from PyQt5 import QtGui, QtWidgets, QtCore

from bt_gui.bt_editor_scene import EditorSceneWindow
from bt_gui.pytrees_backend import BTData, log_best_data, log_last_run_data


class BTEditorLayout(QtWidgets.QVBoxLayout):
    """Layout for the Behavior Tree Editor."""
    def __init__(self, backend: Any, parent=None, update_score_callback=None) -> None:
        super().__init__(parent)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.title_text = "Behavior Tree Editor"
        self.editor_label = QtWidgets.QLabel(self.title_text, font=font)
        self.addWidget(self.editor_label)

        # AI suggestion label and checkbox
        self.checkbox_layout = QtWidgets.QHBoxLayout()
        self.arrange_label = QtWidgets.QLabel("Automatically arrange tree", font=font)
        self.checkbox_layout.addWidget(self.arrange_label)

        self.arrange_checkbox = QtWidgets.QCheckBox()
        self.arrange_checkbox.setChecked(True)  # Set checkbox to be checked by default
        self.arrange_checkbox.stateChanged.connect(self.on_checkbox_state_changed)
        self.checkbox_layout.addWidget(self.arrange_checkbox)
        self.checkbox_layout.addStretch()
        self.addLayout(self.checkbox_layout)

        bt_editor_layout = QtWidgets.QVBoxLayout()
        bt_editor_layout.setContentsMargins(0, 0, 0, 0)

        # create editor
        self.editor = EditorSceneWindow(backend, scene_update_callback=self.update_score_label, save_bt_callback=self.save_bt)
        bt_editor_layout.addWidget(self.editor.get_widget())

        self.addLayout(bt_editor_layout)
        self.score_layout = QtWidgets.QHBoxLayout()

        self.editor_score_label = QtWidgets.QLabel("Score: ?, Size: ?, ?", font=font)
        self.editor_score_label.setToolTip("Score of the behavior tree. The score is based on a) Goal fulfillment, " + \
                                           "b) Time taken, c) Tree complexity, d) Energy consumption",)
        self.score_layout.addWidget(self.editor_score_label)
        self.update_score_callback = update_score_callback

        self.last_run_bt = BTData()

        self.clear_scene_button = QtWidgets.QPushButton("Delete all nodes", font=font)
        self.clear_scene_button.clicked.connect(self.clear_scene)
        self.score_layout.addWidget(self.clear_scene_button)

        self.current_bt = BTData()
        self.saved_bt = BTData()
        self.load_saved_button_text = "Load saved Behavior Tree"
        self.load_saved_button = QtWidgets.QPushButton(self.load_saved_button_text, font=font)
        self.load_saved_button.clicked.connect(self.load_saved)
        self.load_saved_button.setEnabled(False)
        self.score_layout.addWidget(self.load_saved_button)

        self.save_button_text = "Save Behavior Tree"
        self.save_button = QtWidgets.QPushButton(self.save_button_text, font=font)
        self.save_button.clicked.connect(self.save_bt)
        self.score_layout.addWidget(self.save_button)

        self.addLayout(self.score_layout)

        self.icons_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons")

        # Editor buttons Layout
        self.editor_buttons_layout = QtWidgets.QHBoxLayout()
        self.load_best_button_text = "Load best found Behavior Tree"
        self.load_best_button = QtWidgets.QPushButton(self.load_best_button_text, font=font)
        self.load_best_button.clicked.connect(self.load_best)
        self.load_best_button.setEnabled(False)
        self.best_bt = BTData()
        self.editor_buttons_layout.addWidget(self.load_best_button)

        # Get the lock icon from the system style
        self.lock_icon = QtGui.QIcon(os.path.join(self.icons_folder, "lock.png"))
        self.unlock_icon = QtGui.QIcon(os.path.join(self.icons_folder, "lock-unlock.png"))

        self.run_sim_button = QtWidgets.QPushButton("Run simulation", font=font)
        self.run_sim_button.clicked.connect(self.run_sim)
        self.editor_buttons_layout.addWidget(self.run_sim_button)

        self.addLayout(self.editor_buttons_layout)

        #Update tree after simulation is completed
        backend.set_simulation_result_callback(self.update_gui)

    def update_best(self, bt_data: BTData):
        """Update the log of the best found behavior tree"""
        if bt_data.fitness > self.best_bt.fitness:
            self.editor_label.setText(self.title_text + ", current high score: " + str(int(round(bt_data.fitness, 0))))
            self.load_best_button.setEnabled(True)
            self.best_bt = bt_data
            log_best_data(self.best_bt, self.get_backend().experiment_name, "/editor_best_log")
            self.load_best_button.setText(self.load_best_button_text + " (" + str(int(round(bt_data.fitness, 0))) + ")")
            self.get_backend().log_event("New best with " + str(bt_data.fitness) + ": " + str(bt_data.bt))

    def update_last(self, bt_data: BTData):
        """Update the log of the last run behavior tree that the score label is based on"""
        self.last_run_bt = bt_data
        log_last_run_data(self.best_bt, self.get_backend().experiment_name, "/editor_last_run_log")

    def update_gui(self, fitness, py_tree) -> None:
        """Update GUI with simulation step result."""
        status = "SUCCESS" if fitness[-2] == 1 else "FAILURE"
        length = py_tree.get_length() if py_tree else 0
        bt_data = BTData(py_tree.bt.bt[:], fitness[0], fitness[1], fitness[2],
                         true_successes=fitness[-3], status=status, length=length)
        self.update_score_label(bt_data, check_if_still_active=True)
        self.update_best(bt_data)
        self.update_last(bt_data)

    def load_bt(self, string_tree: list[str]) -> None:
        """Load a behavior tree into the editor from a list of strings."""
        # Check if there is a tree in editor already, if so ask to clear
        if self.editor.is_empty() is False:
            reply = QtWidgets.QMessageBox.question(
                self.parentWidget(),
                "Clear existing tree?",
                "There is a behavior tree in the editor already. Do you want it cleared before loading?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.clear_scene()

        self.editor.load_bt(string_tree)

    def clear_scene(self) -> None:
        """Clear the behavior tree editor scene."""
        self.editor.clear_scene()
        self.update_score_label(scene_cleared=True)
        self.get_backend().log_event("Cleared behavior tree editor scene")

    def clear_scores(self) -> None:
        """ Clear the best found and score of last run and saved behavior tree, most likely due to new goals"""
        # Save the last run as it's still the last run, just score not valid
        old_last_bt = self.last_run_bt.bt
        old_last_length = self.last_run_bt.length
        old_saved_bt = self.saved_bt.bt
        old_saved_length = self.saved_bt.length

        self.best_bt = BTData()
        self.last_run_bt = BTData(bt=old_last_bt, length=old_last_length) #Keep tree and length, just reset score
        self.saved_bt = BTData(bt=old_saved_bt, length=old_saved_length) #Keep tree and length, just reset score
        self.editor_label.setText(self.title_text)
        self.load_best_button.setText(self.load_best_button_text)
        self.load_best_button.setEnabled(False)

    def load_saved(self) -> None:
        """ Load the saved behavior tree into the editor."""
        if self.saved_bt is not None:
            self.load_bt(self.saved_bt.bt[:])
            self.update_score_label(self.saved_bt)
            self.get_backend().log_event("Loaded saved behavior tree: " + str(self.saved_bt.bt))

    def save_bt(self) -> None:
        """Save the current behavior tree."""
        current_bt, _ = self.get_and_clean_current_bt()
        if current_bt is not None:
            if self.current_bt.bt != current_bt.bt.bt:
                self.current_bt = BTData(bt=current_bt.bt.bt)
            self.saved_bt = self.current_bt
            self.get_backend().log_event("Saved behavior tree: " + str(self.saved_bt.bt))
            self.load_saved_button.setEnabled(True)

    def load_best(self) -> None:
        """Load the best behavior tree into the editor."""
        if self.best_bt is not None:
            self.load_bt(self.best_bt.bt[:])
            self.update_score_label(self.best_bt)
            self.get_backend().log_event("Loaded best behavior tree: " + str(self.best_bt.bt))

    def get_best_score(self) -> BTData:
        """Get the best behavior tree data."""
        return self.best_bt.fitness

    def load_last(self) -> None:
        """Load the last run behavior tree """
        if self.last_run_bt is not None:
            self.load_bt(self.last_run_bt.bt[:])
            self.update_score_label(self.last_run_bt)
            self.get_backend().log_event("Loaded last behavior tree: " + str(self.last_run_bt.bt))

    def on_checkbox_state_changed(self, state: int) -> None:
        """Handle the state change of the auto arrange checkbox."""
        backend = self.get_backend()
        if state == QtCore.Qt.Checked:
            backend.auto_arrange_tree = True
            backend.log_event("Auto arrange tree enabled")
            self.editor.get_scene().arrange_nodes_tree_structure(node=None, no_update_callback=True)
        else:
            backend.auto_arrange_tree = False
            backend.log_event("Auto arrange tree disabled")

    def update_score_label(self, bt_data: BTData=None, scene_cleared=False, check_if_still_active=False) -> None:
        """Update the score label with the current fitness and status."""
        if bt_data is None:
            user_bt = None
            user_bt_length = 0
            if not scene_cleared: # If the scene is cleared, we don't need to get the user BT
                try:
                    temp_bt = self.editor.get_scene().build_bt()[0].bt
                    user_bt = temp_bt.bt
                    user_bt_length = temp_bt.length()
                except (ValueError, AttributeError):
                    user_bt = None
            if user_bt == self.last_run_bt.bt:
                # No change, no need to update
                return
            bt_data = BTData(bt=user_bt, length=user_bt_length)
        elif check_if_still_active:
            if bt_data.bt != self.editor.get_scene().build_bt()[0].bt.bt:
                return # bt no longer active in editor, do not update score label

        self.current_bt = bt_data
        if bt_data.fitness < -999999:
            str_fitness = "?"
        else:
            str_fitness = str(int(round(bt_data.fitness, 0)))
        if bt_data.length <= 0:
            str_length = "0"
        else:
            str_length = str(bt_data.length)
        self.editor_score_label.setText(
            "Score: " + str_fitness + ", Size:" + str_length + ", Goal state: " + bt_data.status)
        if self.update_score_callback is not None:
            self.update_score_callback()

    def get_backend(self) -> Any:
        """Get the backend object."""
        return self.editor.get_backend()

    def get_and_clean_current_bt(self):
        """ Get current bt and clean up unused nodes """
        return self.editor.get_and_clean_current_bt()

    def get_current_tree(self) -> Any:
        """Get the current behavior tree from the editor without cleaning."""
        return self.editor.get_current_tree()

    def run_sim(self) -> None:
        """Run the simulation of the behavior tree after checking for unused nodes."""
        try:
            py_tree, _ = self.get_and_clean_current_bt()

            if py_tree is not None:
                self.get_backend().simulate_bt(py_tree, True)
                self.get_backend().log_event("Run simulation with BT: " + str(py_tree.bt.bt))
        except ValueError as e:
            QtWidgets.QMessageBox.warning(
                self.parentWidget(),
                "Invalid Behavior Tree",
                str(e),
            )


class TestWindow(QtWidgets.QMainWindow):
    """ Test window to quickly test the layout of the behavior tree editor. """
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Behavior Tree Editor")
        self.resize(1490, 800)

        self.centralwidget = QtWidgets.QWidget(self)

        bt_editor_layout = BTEditorLayout(self.centralwidget)

        from bt_gui.pytrees_backend import PytreesBackend # pylint: disable=import-outside-toplevel
        import bt_gui.test_behavior_list as bt_lib # pylint: disable=import-outside-toplevel
        from scenarios.cubes_and_bowl import get_environment # pylint: disable=import-outside-toplevel
        vis_environment = get_environment(planner_environment=True, n_agents=1)
        learning_environment = get_environment(planner_environment=True, n_agents=20)
        planner_environment = get_environment(planner_environment=True)
        backend = PytreesBackend(vis_environment, learning_environment, planner_environment)
        for item in bt_lib.behavior_list:
            qt_node = backend.behavior_to_qt(item)
            bt_editor_layout.editor.grScene.addItem(qt_node)

        self.setCentralWidget(self.centralwidget)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    test_window = TestWindow()
    test_window.show()
    test_window.raise_()

    sys.exit(app.exec_())
