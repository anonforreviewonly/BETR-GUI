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
import time
from typing import Any
import platform
import argparse
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QTimer, QLocale

from bt_gui.gui_editor import EditorWindow
from bt_gui.gui_fitness import FitnessWindow
from bt_gui.gui_info import InfoWindow
from bt_gui.pytrees_backend import BTData, PytreesBackend, BackendVariants

import scenarios.cubes_and_bowl
import scenarios.tableware
import scenarios.trashpicking
import scenarios.demo


class MainWindow(QtWidgets.QMainWindow):
    """Main window for the Behavior Tree GUI."""
    def __init__(self, backend: Any) -> None: #pylint: disable=redefined-outer-name
        super().__init__()
        font = QtGui.QFont()
        font.setPointSize(8)
        self.backend = backend
        self.setWindowTitle("Behavior Tree Creator")
        self.resize(1920, 1200)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setFont(font)
        self.tabs.currentChanged.connect(self.tab_change)
        self.setCentralWidget(self.tabs)

        self.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))

        # Creating label to show remaining time
        self.timer_label = QtWidgets.QLabel("Time left: 15.00", self, font=font)

        # Set label position and size
        self.timer_label.setGeometry(1650, -40, 100, 100)

        # Creating a timer object
        self.timer = QTimer(self)
        if self.backend.learning_environment.par.scenario == "spheres":
            self.max_time = 5 * 60 # time left in seconds
        else:
            self.max_time = 15 * 60 # time left in seconds
        self.time_left = self.max_time
        self.set_timer_label()  # Set initial timer label
        self.start_time_set = False
        self.start_time = 0.0

        # Adding action to timer
        self.timer.timeout.connect(self.update_timer)

        # Add Instructions Tab
        self.info_tab = InfoWindow(self.backend.learning_environment.par.scenario)
        self.tabs.addTab(self.info_tab, "Instructions")

        # Add Fitness Generation Tab
        self.fitness_tab = FitnessWindow(backend)
        self.tabs.addTab(self.fitness_tab, "Goal Editor")
        self.goals_updated = False

        # Add Editor Tab (disabled by default)
        self.editor_tab = EditorWindow(backend)
        self.tabs.addTab(self.editor_tab, "Behavior Tree Editor")
        self.tabs.setTabEnabled(self.tabs.indexOf(self.editor_tab), False)

    def update_timer(self):
        """Update the timer label."""
        self.time_left = self.max_time - (time.time() - self.start_time)

        self.set_timer_label()  # Update the label with the new time

        if self.time_left < 0.1:
            self.finish_experiment()  # If time is up, finish the experiment

    def finish_experiment(self) -> None:
        """ Time out, end experiment and close down """
        self.timer.stop()

        self.backend.stop_simulation()  # Call the backend to finish the experiment
        self.editor_tab.stop_ai_simulation()  # Stop the AI simulation in the editor tab
        self.backend.log_event("Experiment completed")
        text = "Time is up! Well done! This experiment will now close. Please give the laptop to the experiment supervisor. \nThe final score was: " + \
               f"{int(round(self.editor_tab.get_best_score(), 0))}\n"

        QtWidgets.QMessageBox.information(
            self.parentWidget(),
            "Time up!",
            text,
        )
        py_tree, mask, unconnected_objects = self.editor_tab.get_current_tree()
        self.backend.log_event("Current tree:" + str(py_tree.bt.bt) + ", " + str(mask) + ", " + str(unconnected_objects))
        self.backend.close_backend()  # Close the visualization in the backend
        self.close()  # Close the main window

    def closeEvent(self, evnt) -> None: #pylint: disable=invalid-name
        """ When closing, if there is time left, ask user if they want to close """
        if self.time_left >= 0.1:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Confirm Close",
                "There is still time left. This will terminate the experiment. Do you really want to close?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                evnt.ignore()
                return
        self.backend.close_backend()  # Close the visualization in the backend

    def set_timer_label(self) -> None:
        """Set the timer label to a specific time."""
        minutes = int(self.time_left // 60)
        seconds = int(self.time_left % 60)
        self.timer_label.setText(f"Time left: {minutes:02}:{seconds:02}")

        if minutes < 1:
            # If less than 1 minute left, change label color to red
            self.timer_label.setStyleSheet("color: red")

    def enable_editor_tab(self) -> None:
        """Enable the editor tab."""
        self.tabs.setTabEnabled(self.tabs.indexOf(self.editor_tab), True)

    def load_goals_to_editor(self, goals_bt: BTData) -> None:
        """Load the behavior tree into the editor."""
        self.editor_tab.load_to_editor(goals_bt, clear_scene=True)  # Clear the scene before loading
        self.goals_updated = True

    def tab_change(self, i):
        """ Called when tab index is changed """
        try:
            if i == self.tabs.indexOf(self.editor_tab):
                if self.goals_updated:
                    self.editor_tab.ai_layout.reset_valid_best_bt() # Assume best bt is not valid anymore
                    self.editor_tab.editor_layout.clear_scores()
                    self.editor_tab.send_to_ai() #Start the ai process
                    self.goals_updated = False
                else:
                    self.editor_tab.start_ai_simulation() #Start the ai process
                self.backend.log_event("Editor tab")
            else:
                self.editor_tab.stop_ai_simulation() #Stop the ai process
                if i == self.tabs.indexOf(self.fitness_tab):
                    if self.start_time_set is False:
                        self.start_time_set = True
                        self.start_time = time.time()
                        self.editor_tab.set_start_time()
                    self.timer.start(100)
                    self.backend.log_event("Fitness tab")
                    self.fitness_tab.tab_entered()
        except AttributeError:
            pass #Sometimes due to timing in startup, the editor tab is not yet created

def get_variant_seq_from_user_id(user_id):
    """ Returns variant sequence number from user id """
    if user_id <= 24:
        return user_id
    elif user_id <= 48:
        return user_id - 24
    elif user_id == 49:
        return 21
    elif user_id == 50:
        return 22
    elif user_id == 51:
        return 19
    elif user_id == 52:
        return 20
    elif user_id == 53:
        return 7
    elif user_id == 54:
        return 8
    elif user_id == 55:
        return 1
    elif user_id == 56:
        return 2
    elif user_id == 57:
        return 13
    elif user_id == 58:
        return 14
    elif user_id == 59:
        return 11
    elif user_id == 60:
        return 12
    else:
        print("ERROR, user_id not found")
        raise Exception("user_id not found")

def get_variant_id(variant_seq, experiment: int) -> str:
    """Get the variant from the experiment id."""
    full_list = [[1, 3, 2], #1
                 [1, 4, 2], #2
                 [1, 5, 2], #3
                 [1, 6, 2], #4
                 [1, 2, 3], #5
                 [1, 2, 4], #6
                 [1, 2, 5], #7
                 [1, 2, 6], #8
                 [3, 1, 2], #9
                 [4, 1, 2], #10
                 [5, 1, 2], #11
                 [6, 1, 2], #12
                 [3, 2, 1], #13
                 [4, 2, 1], #14
                 [5, 2, 1], #15
                 [6, 2, 1], #16
                 [2, 3, 1], #17
                 [2, 4, 1], #18
                 [2, 5, 1], #19
                 [2, 6, 1], #20
                 [2, 1, 3], #21
                 [2, 1, 4], #22
                 [2, 1, 5], #23
                 [2, 1, 6], #24
                 ]

    return full_list[variant_seq - 1][experiment - 1]

def get_variant_from_id(variant_id: int):
    """Get the variant from the variant id."""
    variant_list = [BackendVariants.FULL, BackendVariants.MANUAL_ONLY, BackendVariants.NO_BO,
                    BackendVariants.NO_GP, BackendVariants.NO_LLM, BackendVariants.NO_PLANNER]
    return variant_list[variant_id - 1]

def get_task_id(user_id: int, experiment: int):
    """Get the environment from the user id and experiment."""
    task_order_ids = [1, 6, 4, 4, 5, 4, 2, 6, 1, 2, 6, 3, 1, 6, 6, 3,
                      6, 1, 2, 1, 4, 2, 6, 2, 4, 5, 3, 3, 1, 6, 5, 5,
                      5, 5, 2, 5, 3, 2, 5, 1, 1, 3, 6, 2, 5, 5, 1, 6,
                      3, 4, 4, 4, 1, 3, 3, 2, 4, 4, 3, 2]

    task_order_id = task_order_ids[user_id - 1]

    task_list = [[1, 2, 3],
                 [1, 3, 2],
                 [2, 1, 3],
                 [2, 3, 1],
                 [3, 2, 1],
                 [3, 1, 2]]
    return task_list[task_order_id - 1][experiment - 1]

def get_environment_from_task_id(task_id: int):
    """Get the environment from the task id."""
    task_list = [scenarios.cubes_and_bowl.get_environment,
                 scenarios.tableware.get_environment,
                 scenarios.trashpicking.get_environment]
    return task_list[task_id - 1]

def get_variant_and_environment(user_id, experiment):
    """ Returns variant and environment given user_id and experiment no"""
    variant_seq = get_variant_seq_from_user_id(user_id)
    variant_id = get_variant_id(variant_seq, experiment)
    backend_variant = get_variant_from_id(variant_id)
    task_id = get_task_id(user_id, experiment)
    get_environment = get_environment_from_task_id(task_id)
    return backend_variant, get_environment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--user_id', type=int, default='0', help='The id of the current user')
    parser.add_argument('--experiment', type=int, default='0', help='The experiment number to run')
    args = parser.parse_args()
    if args.user_id <= 0 or args.experiment <= 0:
        # Demo scenario
        backend_variant, get_environment = BackendVariants.MANUAL_ONLY, scenarios.demo.get_environment
    else:
        backend_variant, get_environment = get_variant_and_environment(args.user_id, args.experiment)

    app = QtWidgets.QApplication(sys.argv)

    USE_PLANNER = False
    if platform.system() != "Windows":
        USE_PLANNER = True
    else:
        import psutil
        if "SimExample.exe" in (p.name() for p in psutil.process_iter()):
            print("WARNING: SimExample window already open")

    sys.setswitchinterval(0.0005)  # Set the switch interval to a very low value for better GUI performance

    experiment_name = "gui_logs/gui_log_" + str(args.user_id) + "_" + str(args.experiment) #pylint: disable=invalid-name

    vis_environment = get_environment(planner_environment=USE_PLANNER, n_agents=1)
    learning_environment = get_environment(planner_environment=USE_PLANNER, n_agents=32, \
                                           preplan_subtrees=backend_variant != BackendVariants.NO_PLANNER)
    learning_environment.set_seeds(int(args.user_id) * 1000 + int(args.experiment))
    planner_environment = get_environment(planner_environment=True)
    backend = PytreesBackend(vis_environment,
                             learning_environment,
                             planner_environment,
                             backend_variant=backend_variant,
                             experiment_name=experiment_name)

    main_window = MainWindow(backend)
    main_window.show()
    main_window.raise_()
    main_window.showMaximized()
    backend.visualizer.releaseMouse()
    backend.start_goal_simulation()
    sys.exit(app.exec_())
