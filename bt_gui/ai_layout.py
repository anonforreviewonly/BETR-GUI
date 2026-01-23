""" Layout for displaying the AI results and suggestion."""
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

from PyQt5 import QtWidgets, QtSvg, QtGui, QtCore
from interfaces.py_trees_interface import PyTree
from bt_gui.pytrees_backend import BTData, log_best_data, BackendVariants
from bt_gui.threaded_processes import SimulationWorker
from behaviors.behavior_tree import BT


class BTLearningInterface(QtWidgets.QGraphicsView):
    """
    Graphics view to display the AI's best behavior tree (BT) as an svg image.
    Also handles managing the simulation state
    and the code for the main loop for AI.    
    """
    def __init__(self, backend, test: bool = False) -> None:
        super().__init__()

        self.test = test
        if not self.test:
            self.img_folder = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), "gui_figures"
            )
        else:
            self.img_folder = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), "test_figures"
            )

        self.backend = backend
        self.best_bt = BTData()
        self.has_valid_best_bt = False

        self.waiting_to_start = False
        self.waiting_to_stop = False
        self.waiting_to_reset_best_bt = False
        self.running = False
        self.bt_to_send = None
        self.mask_to_send = None

        # Create a scene
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)

        self.renderer = QtSvg.QSvgRenderer()

        # Create an SVG item and add it to the scene
        self.svg_item = QtSvg.QGraphicsSvgItem()
        self.svg_item.setSharedRenderer(self.renderer)
        self.scene.addItem(self.svg_item)

        self._set_scene_size()

        # Resize the view to the available space
        self.setRenderHint(QtGui.QPainter.Antialiasing)

        self.setAcceptDrops(False)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

    def send_bt_to_ai(self, bt: Any, mask: list[bool] = None) -> None:
        """Send the behavior tree (BT) as a baseline to the AI for optimization."""
        # First test if baseline is even valid
        valid, message = bt.bt.is_valid(get_error_string=True, require_behavior=False)
        if not valid:
            raise ValueError(f"{message}")
        self.bt_to_send = bt
        self.mask_to_send = mask

    def reset_valid_best_bt(self) -> None:
        """Reset the valid best behavior tree (BT) flag and the best BT data."""
        self.waiting_to_reset_best_bt = True

    def start_simulation(self) -> None:
        """Start simulation in the worker thread."""
        self.waiting_to_start = True

    def stop_simulation(self) -> None:
        """Stop the simulation."""
        if not self.waiting_to_stop:
            self.waiting_to_stop = True
            if not self.get_run_bo(): #Cannot pause BO, let it complete iteration
                self.backend.set_learning_pause(True) #Pause learning process, discards any unfinished results

    def run_iterative_process(self) -> Any:
        """Main working process for the AI worker."""
        if self.waiting_to_stop:
            self.waiting_to_stop = False
            self.running = False
        if self.waiting_to_start:
            self.waiting_to_start = False
            self.running = True
            self.backend.set_learning_pause(False)

        if self.running and not self.waiting_to_stop: #Check again to help with race conditions
            new_instance = False
            if self.bt_to_send is not None:
                new_instance = self.backend.set_baseline(self.bt_to_send, self.mask_to_send)
                self.bt_to_send = None
                self.mask_to_send = None
            if self.waiting_to_reset_best_bt or new_instance:
                self.has_valid_best_bt = False
                self.best_bt = BTData()
                self.waiting_to_reset_best_bt = False
            return self.get_evolved_bt()
        else:
            time.sleep(0.1)  # Sleep to avoid busy waiting

    def get_run_bo(self) -> bool:
        """Check if the backend is using Bayesian Optimization (BO) for learning."""
        return (not self.backend.learn_structure and self.backend.backend_variant != BackendVariants.NO_BO) or \
                self.backend.backend_variant == BackendVariants.NO_GP

    def get_evolved_bt(self) -> tuple[str, int, str, bool]:
        """ Takes one step in the optimization process and returns the best behavior tree (BT) and its fitness score."""
        improved = False
        same_as_baseline = False
        status = "?"
        fitness_str = "?"
        best_bt = []
        best_bt_length = 0
        if not self.has_valid_best_bt:
            # If no best behavior tree yet, just use the planned default tree to have no delay in the GUI
            if self.get_run_bo():
                # Get baseline from BO
                if self.backend.bo_handler is not None:
                    best_bt = self.backend.bo_handler.bt
                    improved = True
            else:
                #Get baseline from gp_instance to use
                if self.backend.gp_instance is not None:
                    best_bt = self.backend.gp_instance.baseline
                    improved = True
            if improved:
                best_bt_length = BT(best_bt[:], self.backend.get_behavior_list()).length()
                self.best_bt = BTData(best_bt[:], length=best_bt_length)
                improved = True
        else:
            if self.get_run_bo():
                if self.backend.bo_handler is not None:
                    try:
                        self.backend.bo_handler.step_optimization()
                        best_bt, fitness, net_fitness, true_fitness, true_successes, status_code = (
                            self.backend.bo_handler.get_best_individual()
                        )
                    except ValueError:
                         # Something went wrong. Most likely we have more parameters than before, reset BO
                        self.backend.set_new_bo_handler(self.backend.bo_handler.bt,
                                                        self.backend.bo_handler.mask[:])
                        best_bt, fitness, net_fitness, true_fitness, true_successes, status_code = [], 0, 0, 0, 0, 0
                else:
                    best_bt, fitness, net_fitness, true_fitness, true_successes, status_code = [], 0, 0, 0, 0, 0
            else:
                status_code = 0
                best_bt = []
                fitness = 0.0
                try:
                    if self.backend.gp_instance.is_runnable():
                        self.backend.gp_instance.step_gp()
                    best_bt, fitness, net_fitness, true_fitness, true_successes, status_code = (
                        self.backend.gp_instance.get_best_individual()
                    )
                except (AttributeError, IndexError):
                    # Sometimes the gp_instance could be None due to timing, do nothing
                    pass
                except Exception as e:
                    # More serious error with GP, delete it.
                    self.backend.gp_instance = None
                    print("Error in GP step or getting best individual:", e)

            if not self.backend.get_learning_pause(): #If paused we can not trust results
                fitness_str = str(int(round(fitness, 0)))
                status = "SUCCESS" if status_code == 1 else "FAILURE"

                if (best_bt != self.best_bt.bt or self.best_bt.true_fitness >= 0.0) and best_bt != []:
                    best_bt_length = BT(best_bt[:], self.backend.get_behavior_list()).length()
                    self.best_bt = BTData(best_bt[:], fitness, net_fitness, true_fitness, true_successes=true_successes, \
                                          status=status, length=best_bt_length)
                    log_best_data(self.best_bt, self.backend.experiment_name, "/ai_log")
                    improved = True

        if improved:
            # Save figure to show in GUI
            env = self.backend.learning_environment
            params = env.par.py_tree_parameters
            world = env.sim_class(env.par.sim_parameters, env.par.seed)
            pytree = PyTree(best_bt[:], params, world)
            pytree.save_fig(self.img_folder, "best_individual", save_png=False)
            if best_bt_length == 0:
                best_bt_length = pytree.get_length()
            self.has_valid_best_bt = True
            if len(self.backend.baseline) == len(best_bt):
                all_same = True
                for i in range(len(best_bt)): # pylint: disable=consider-using-enumerate
                    if hasattr(best_bt[i], 'is_same') and best_bt[i].is_same(self.backend.baseline[i]) or \
                        best_bt[i] == self.backend.baseline[i]:
                        continue
                    all_same = False
                    break
                if all_same:
                    same_as_baseline = True

        evolved_bt = os.path.join(self.img_folder, "best_individual.svg")

        return evolved_bt, fitness_str, status, best_bt_length, improved, same_as_baseline

    def update_viewer(self, evolved_bt: str) -> None:
        """Update the viewer with the new behavior tree (BT) """
        self.renderer.load(evolved_bt)  # Update the renderer

        # Update scene size
        self.svg_item.setSharedRenderer(self.renderer)
        self._set_scene_size()

        # Resize the view to the available space
        self.setRenderHint(QtGui.QPainter.Antialiasing)

        # Force an update and adjust view
        self.update()
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:  #pylint: disable=invalid-name
        """Zoom in/out when Ctrl is held, otherwise allow normal scrolling."""
        if event.modifiers() == QtCore.Qt.ControlModifier:  # Check if Ctrl is held
            zoom_factor = 1.2
            min_zoom = 0.1
            max_zoom = 5.0

            current_scale = self.transform().m11()  # Get current zoom level
            if event.angleDelta().y() > 0 and current_scale < max_zoom:  # Zoom in
                self.scale(zoom_factor, zoom_factor)
            elif event.angleDelta().y() < 0 and current_scale > min_zoom:  # Zoom out
                self.scale(1 / zoom_factor, 1 / zoom_factor)

            event.accept()  # Prevent normal scrolling when zooming
        else:
            super().wheelEvent(event)  # Default behavior (scrolling)

    def _set_scene_size(self) -> None:
        # Get the default size of the SVG to set the scene size
        svg_size = self.renderer.defaultSize()
        self.setSceneRect(0, 0, svg_size.width(), svg_size.height())


class AILayout(QtWidgets.QVBoxLayout):
    """Layout for displaying the AI results and suggestion."""
    def __init__(self, backend: Any, parent=None, ai_update_callback=None, test: bool = False) -> None:
        super().__init__(parent)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.icons_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons")
        self.backend = backend
        self.ai_update_callback = ai_update_callback

        self.top_layout = QtWidgets.QVBoxLayout()

        self.ai_label = QtWidgets.QLabel("AI-optimized Behavior Tree", font=font)
        self.top_layout.addWidget(self.ai_label)
        self.has_locked_structure = False
        if backend.backend_variant != BackendVariants.MANUAL_ONLY:
            # AI suggestion label and checkbox
            checkbox_layout = QtWidgets.QHBoxLayout()

            self.structure_label = QtWidgets.QLabel("Allow changing the tree structure ", font=font)
            checkbox_layout.addWidget(self.structure_label)

            self.suggestion_checkbox = QtWidgets.QCheckBox()
            self.suggestion_checkbox.setChecked(True)  # Set checkbox to be checked by default
            self.suggestion_checkbox.stateChanged.connect(self.on_checkbox_state_changed)

            # Change switching between GP and BO with checkbox to button instead
            # suggestion_layout.addWidget(self.change_optimization_button)
            checkbox_layout.addWidget(self.suggestion_checkbox)
            checkbox_layout.addStretch()
            self.top_layout.addLayout(checkbox_layout)

        self.paused_text = "Paused. Press <Send> to restart optimization."
        self.running_text = "Trying to improve on your Behavior Tree."
        self.running_extra_dots = 0
        self.running_label = QtWidgets.QLabel(self.paused_text, font=font)
        self.top_layout.addWidget(self.running_label)


        self.addLayout(self.top_layout)
        self.learning_interface = BTLearningInterface(backend, test)
        self.addWidget(self.learning_interface)

        lower_layout = QtWidgets.QVBoxLayout()
        self.ai_score_label = QtWidgets.QLabel("Score: ?, Size: ?, Goal state: ?", font=font)
        lower_layout.addWidget(self.ai_score_label)

        self.show_sim_button = QtWidgets.QPushButton("Show simulation of suggested Behavior Tree from AI", font=font)
        self.show_sim_button.clicked.connect(self.show_sim)
        lower_layout.addWidget(self.show_sim_button)
        self.addLayout(lower_layout)

        # Create worker and move it to a separate thread
        self.worker = SimulationWorker(self.learning_interface)
        self.worker_thread = QtCore.QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)

        # Connect worker signal to update GUI
        self.worker.update_signal.connect(self.update_layout)


        # Create worker purely for animation and move it to a separate thread
        self.animation_worker = SimulationWorker(self)
        self.animation_worker_thread = QtCore.QThread()
        self.animation_worker.moveToThread(self.animation_worker_thread)
        self.animation_worker_thread.started.connect(self.animation_worker.run)
        self.animation_worker_thread.start()
        # Connect worker signal to update GUI
        self.animation_worker.update_signal.connect(self.update_animation)

    def reset_valid_best_bt(self) -> None:
        """Reset the valid best behavior tree (BT) flag."""
        self.learning_interface.reset_valid_best_bt()

    def show_sim(self) -> None:
        """ Show simulation of AI BT."""
        bt = self.learning_interface.best_bt
        self.backend.simulate_bt(bt, False)
        self.backend.log_event("Show simulation of AI BT")

    def run_iterative_process(self) -> None:
        """Run the iterative process in the worker thread."""
        if self.learning_interface.running and not self.learning_interface.waiting_to_stop:
            self.running_extra_dots += 1
            if self.running_extra_dots > 2:
                self.running_extra_dots = 0

            time.sleep(0.5) # Determines speed of animation
            return (self.running_extra_dots, None)

        self.running_extra_dots = 0
        time.sleep(0.1)  # Sleep to avoid busy waiting

    def start_simulation(self) -> None:
        """Start simulation in the worker thread."""
        self.learning_interface.start_simulation()
        if not self.worker_thread.isRunning():
            self.worker_thread.start(0) # Start the worker thread with low priority

        self.running_label.setText(self.running_text)

    def stop_simulation(self) -> None:
        """Stop simulation and thread."""
        self.learning_interface.stop_simulation()
        self.running_label.setText(self.paused_text)

    def update_layout(self, result) -> None:
        """Update GUI with simulation step result."""
        evolved_bt, score, status, best_bt_length, improved, same_as_baseline = result
        if improved:
            self.learning_interface.update_viewer(evolved_bt)
            self.ai_score_label.setText(f"Score: {score}, Size: {best_bt_length}, Goal state: {status}")
            if not same_as_baseline and self.ai_update_callback is not None:
                self.ai_update_callback()

    def update_animation(self, result) -> None:
        """Update the running label with dots animation."""
        if self.learning_interface.running and not self.learning_interface.waiting_to_stop:
            self.running_label.setText(self.running_text + "." * result[0])

    def on_checkbox_state_changed(self, state: int) -> None:
        """Handle the state change of the suggestion checkbox."""
        self.stop_simulation()
        if state == QtCore.Qt.Checked:
            self.backend.learn_structure = True
            self.backend.log_event("AI structure optimization enabled")
        else:
            self.backend.learn_structure = False
            self.backend.log_event("AI structure optimization disabled")
            self.has_locked_structure = True
        self.reset_valid_best_bt()
