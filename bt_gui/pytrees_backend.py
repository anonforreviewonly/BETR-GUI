"""Large shared backend object for doing calculations and simulations etc."""

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

from os.path import isfile
from typing import Any
from dataclasses import dataclass, field
import pickle
import time
from enum import IntEnum
from PyQt5 import QtCore, QtGui, QtWidgets
import py_trees as pt

from behaviors.common_behaviors import ParameterizedNode, NodeParameter, ParameterTypes, fast_copy
from behaviors.behavior_lists import BehaviorLists
from behaviors.behavior_tree import BT
import bt_learning.gp.genetic_programming as gp
from bt_learning.gp.gp_instance import GPInstance
from bt_learning.bo import bo
from bt_learning.gp.logplot import open_file, get_log_folder, clear_logs
from interfaces.py_trees_interface import PyTree
import llm.llm_utilities as llm
from planner import planner
from bt_gui.bt_editor_elements import Node
from bt_gui.threaded_processes import SimulationWorker
from bt_gui.gui_visualization import BehaviorTreeVisualizer, get_unity_window


@dataclass
class BTData:
    """Data class to hold a behavior tree and its fitness."""

    bt: list = field(default_factory=list)
    fitness: float = -999999999
    net_fitness: float = 0.0
    true_fitness: float = 0.0
    true_successes: int = 0
    status: str = "?"
    time: float = 0.0
    length: int = 0

    def __str__(self) -> str:
        string = f"BT: {self.bt}, fitness: {self.fitness}, net_fitness:, {self.net_fitness}, "
        string += f"true_fitness: {self.true_fitness}, true_successes: {self.true_successes}, "
        string += f"status: {self.status}, time: {self.time}, length: {self.length}"
        return string

class HintingSpinbox(QtWidgets.QDoubleSpinBox):
    """A QDoubleSpinBox that shows a hint when trying to set values of of range."""
    def __init__(
        self, initial_value: Any, min_val: float=-100, max_val: float=100, step: float=1.0
    ):
        """Creates a spin box with a specific range and step size."""
        super().__init__()
        self.setRange(-99, 99)
        self.min_val = min_val
        self.max_val = max_val
        self.setSingleStep(step)
        self.setValue(initial_value)
        self.setDecimals(2)
        self.setReadOnly(False)
        self.valueChanged.connect(self.new_value)

    def new_value(self, new_value: float) -> None: # pylint: disable=invalid-name
        """
        Set the value of the spin box, showing a hint if out of range. 
        Only show hint if more than one step out of range
        """
        if new_value < self.min_val - self.singleStep() or new_value > self.max_val + self.singleStep():
            QtWidgets.QToolTip.showText(
                self.mapToGlobal(QtCore.QPoint(0, 0)),
                f"Value {new_value} out of range ({self.min_val} to {self.max_val})",
            )
        if new_value < self.min_val:
            self.setValue(self.min_val)
        elif new_value > self.max_val:
            self.setValue(self.max_val)

class BackendVariants(IntEnum):
    """Define the parameter types."""
    FULL = 0  # All functionalities are available
    NO_GP = 1  # No Genetic Programming, only Bayesian Optimization is available for learning
    NO_BO = 2  # No Bayesian Optimization, only Genetic Programming is available for learning
    NO_LLM = 3  # No LLM, only GP and BO are available
    NO_PLANNER = 4  # No planner
    MANUAL_ONLY = 5  # Only manual editing of the behavior tree is available, no learning or planning

class PytreesBackend:
    """Backend for the Behavior Tree GUI, interfaces with calculations and AI models etc."""
    behavior_name_mime_type = "behavior/name-data"
    behavior_ai_mime_type = "behavior/name-ai"

    def __init__(
        self,
        vis_environment: Any = None,
        learning_environment: Any = None,
        planner_environment: Any = None,
        backend_variant: BackendVariants = BackendVariants.FULL,
        experiment_name: str = "gui_log",
        minimize_on_close: bool = True,
        minimal_backend: bool = False, # A minimal backend without starting simulations etc
    ) -> None:
        self.experiment_name = experiment_name
        if not minimal_backend:
            clear_logs(experiment_name)
            self.log_event("Backend created for experiment: " + experiment_name + \
                        ", variant: " + str(backend_variant) + \
                        ", scenario: " + str(vis_environment.par.scenario))
        self.vis_environment = vis_environment
        if not minimal_backend:
            self.vis_environment.start_simulation(channel=50050, headless=False, timescale=1, unity_log_file="vis_unity.log")

            if self.vis_environment.par.physics_sim:
                # Create the visualizer window
                self.unity_hwnd = get_unity_window()
            else:
                self.unity_hwnd = None

            self.visualizer = BehaviorTreeVisualizer(self, unity_hwnd=self.unity_hwnd, minimize_on_close=minimize_on_close)

        self.learning_environment = learning_environment
        if not minimal_backend:
            self.learning_environment.start_simulation(channel=50011, headless=True, timescale=10, unity_log_file="learning_unity.log")
        self.planner_environment = planner_environment
        self.parameters = self.learning_environment.par.py_tree_parameters
        self.backend_variant = backend_variant
        self.gp_instance = None
        self.bo_handler = None

        self.learn_structure = True
        self.gui_bo_log_id = 0
        self.gui_gp_log_id = 0

        self.world_interface = self.learning_environment.sim_class(
            self.learning_environment.par.sim_parameters, self.learning_environment.par.seed
        )

        if not minimal_backend:
            # Create worker and move it to a separate thread
            self.worker = SimulationWorker(self)
            self.worker_thread = QtCore.QThread()
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker.update_signal.connect(self.handle_simulation_result)
        self.simulating = False
        self.stepping = False
        self.new_step_requested = False
        self.simulation_result_callback = None
        self.update_score_after_sim = True
        self.visualizing_goal = False
        self.goal_result_callback = None
        self.goal_positions = None
        self.goal_yaws = None
        self.simulation_tree = None
        self.auto_arrange_tree = True
        self.last_built_bt = []
        self.last_mask = []
        self.baseline = []

    def set_simulation_result_callback(self, callback):
        """ Set extra callback for signal after simulation worker is done """
        self.simulation_result_callback = callback

    def set_goal_result_callback(self, callback):
        """ Set extra callback for goal visualization after worker is done """
        self.goal_result_callback = callback

    def get_default_object_position(self, object_name: str) -> Any:
        """Get the default position of an object."""
        if self.vis_environment is not None and object_name in self.vis_environment.par.sim_parameters.object_positions:
            return self.vis_environment.par.sim_parameters.object_positions[object_name]
        return None

    def get_current_object_position(self, object_name: str) -> Any:
        """Get the current position of an object in the vis environment."""
        if self.vis_environment is not None:
            return self.vis_environment.world_interface[0].get_position(object_name)
        return None

    def set_goal_positions(self, goal_positions, goal_yaws=None):
        """ Set the goal positions for later visualization """
        self.goal_positions = goal_positions
        self.goal_yaws = goal_yaws

    def handle_simulation_result(self, result):
        """Handle simulation results."""
        if self.simulating or self.stepping:
            if self.stepping:
                self.stop_simulation()
            status_ok, exec_statuses = result

            if status_ok:
                self.visualizer.update_tree(exec_statuses)
            else:
                self.visualizer.update_tree(exec_statuses, last_update=True)
                self.stop_simulation()

                if self.simulation_result_callback is not None and self.update_score_after_sim:
                    fitness = self.compile_fitness()[0]
                    py_tree = self.vis_environment.get_last_pytree()
                    self.simulation_result_callback(fitness, py_tree)
        elif self.visualizing_goal:
            self.vis_environment.reset_world([], [0], object_positions=self.goal_positions, object_yaws=self.goal_yaws)
            camera_position = self.world_interface.get_camera_position(self.vis_environment.par.scenario)
            self.goal_result_callback(self.vis_environment.get_screenshot(camera_position))
            self.stop_simulation()

    def start_simulation_worker(self):
        """ Start the simulation worker"""
        if not self.worker_thread.isRunning():
            self.worker_thread.start()

    def start_goal_simulation(self):
        """ Start a goal simulation """
        if self.simulating:
            self.stop_simulation()
        self.visualizing_goal = True

        self.start_simulation_worker()

    def step_simulation(self):
        """ Step the simulation one step """
        self.stepping = True
        self.new_step_requested = True
        self.start_simulation_worker()

    def play_simulation(self):
        """ Play the simulation until finished """
        self.simulating = True
        self.stepping = False
        self.start_simulation_worker()

    def reset_simulation(self, string_tree=None, object_positions=None, object_yaws=None) -> None:
        """Reset the simulation environment."""
        if self.vis_environment is not None:
            if string_tree is None:
                string_tree = self.simulation_tree
            self.vis_environment.reset([string_tree], object_positions=object_positions, object_yaws=object_yaws)

    def simulate_bt(self, bt: Any = None, update_score: Any=None) -> None:
        """Simulate the behavior tree."""
        if update_score is not None:
            self.update_score_after_sim = update_score
        self.stop_simulation()
        self.simulating = True
        if bt is not None:
            self.simulation_tree = self.get_string_tree(bt)
        self.reset_simulation()
        self.visualizer.visualize_tree(self.simulation_tree)
        self.visualizer.show()
        self.visualizer.raise_()
        self.visualizer.showMaximized()

        self.start_simulation_worker()

    def stop_simulation(self) -> None:
        """Stop simulation and thread."""
        self.simulating = False
        self.stepping = False
        self.visualizing_goal = False
        self.worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()

    def close_backend(self) -> None:
        """Close the visualizer window and simulation processes."""
        if self.visualizer is not None:
            self.visualizer.close()
        self.vis_environment.delete_sim()
        self.learning_environment.delete_sim()
        self.planner_environment.delete_sim()

    def initialize_gp(self) -> GPInstance:
        """Initialize the GP instance."""
        n_processes = 1
        gp_par = gp.GpParameters()
        gp_par.behavior_lists = self.parameters.behavior_lists
        gp_par.ind_start_length = 5
        gp_par.min_length = 5
        gp_par.n_population = 32
        gp_par.f_crossover = 0.0625
        gp_par.n_offspring_crossover = 2
        gp_par.f_mutation = 0.4375
        gp_par.n_offspring_mutation = 2
        gp_par.f_elites = 0.2
        gp_par.f_parents = 0.2
        gp_par.plot = False
        gp_par.n_generations = 10000
        gp_par.max_multi_mutation = 3
        gp_par.verbose = False
        gp_par.fig_best = False
        gp_par.log_name = self.experiment_name + "/gp_run"
        gp_par.save_interval = 10
        gp_par.initialize_from_baseline = True

        self.gp_instance = GPInstance(
            str(self.gui_gp_log_id), self.learning_environment, n_processes, gp_par
        )
        return self.gp_instance

    def get_string_tree(self, behavior_tree: Any) -> list[str]:
        """Return the string representation of the behavior tree."""
        if isinstance(behavior_tree, PyTree):
            string_tree = behavior_tree.bt.bt[:]
            self.parameters.behavior_lists.convert_from_string(string_tree)
            return string_tree
        elif isinstance(behavior_tree, BT):
            self.parameters.behavior_lists.convert_from_string(behavior_tree.bt)
            return behavior_tree.bt
        elif isinstance(behavior_tree, BTData):
            return behavior_tree.bt[:]
        elif isinstance(behavior_tree, list):
            # If it's a list, we assume it's a string representation of the tree
            self.parameters.behavior_lists.convert_from_string(behavior_tree)
            return behavior_tree
        else:
            print("ERROR: behavior_tree is not a PyTree, BTData or list object")

    def get_bt_data_from_tree(self, bt_list: Any) -> BTData:
        """ Returns the BTData object from the behavior tree list, populated with length """
        behavior_tree = BT(bt_list[:], self.parameters.behavior_lists)
        return BTData(bt_list[:], length=behavior_tree.length())

    def set_goals_from_tree(self, bt) -> None:
        """ Set the goals from the user input, make sure to clear gp_instance and bo_handler so no old data is interfering """
        self.learning_environment.set_goals_from_behavior_tree(bt)
        goals = self.learning_environment.get_goals()
        if self.vis_environment is not None:
            self.vis_environment.set_goals(goals)
        self.planner_environment.set_goals(goals)
        self.gp_instance = None
        self.bo_handler = None

    def set_new_bo_handler(self, individual, mask):
        """ Sets a new BO handler, for example if the scenario or goals have changed """
        bo_settings = bo.HandlerSettings(
            runs_per_bt=1,
            validation_runs=0,
            log_name=self.experiment_name + "/bo_run_" + str(self.gui_bo_log_id),
            batch_size=1,
        )

        self.bo_handler = bo.BoHandler(self.learning_environment, individual, bo_settings)
        self.gui_bo_log_id += 1
        self.bo_handler.fix_conditions()
        self.bo_handler.fix_mask(mask) # Fix any nodes in the locked mask

    def set_baseline(self, py_tree: PyTree, mask: list[bool] = None) -> None:
        """Set the baseline for the GP instance or BO run."""
        new_instance = False # True if the learning needed a new instance
        locked_tree = None
        if not any(mask):
            mask = None
        elif mask is not None:
            locked_tree = self.get_string_tree(py_tree)

        if self.backend_variant != BackendVariants.NO_PLANNER and self.backend_variant != BackendVariants.MANUAL_ONLY and \
           self.learn_structure:
            world_interface = self.planner_environment.sim_class(
                self.planner_environment.par.sim_parameters
            )

            baseline, planned_py_tree = planner.plan(
                world_interface,
                py_tree.behavior_lists,
                remove_redundant_conditions=False,
                tree=py_tree.root,
                save_figs=False,
            )

            #Resolve errors iteratively
            if planned_py_tree.status is pt.common.Status.FAILURE and self.backend_variant != BackendVariants.NO_LLM:
                attempts_left = 6
                client = llm.get_gpt_client()
                self.log_event("Planning failed for BT, attempting resolve: " + str(baseline.bt))
                while planned_py_tree.status is pt.common.Status.FAILURE and attempts_left > 0:
                    scene = self.planner_environment.scene_description
                    scene += "The currently grasped object is: " + str(world_interface.get_grasped_object()) + "."
                    failed_action = world_interface.get_failed_action()
                    failed_action = failed_action.replace("\n", "") # Strip linebreaks
                    error_message = world_interface.get_error_message()

                    error_description = '\nFailing action: ' + failed_action + \
                                        '\nError message: ' + error_message
                    self.log_event("LLM resolving scene and error description: " + scene + error_description)
                    try:
                        reasoning, preconditions = llm.resolve_error(client, "cubebowl", scene, error_description, None, verbose=False)
                    except Exception as e:
                        reasoning = e
                        preconditions = []
                    self.log_event("LLM reasoning: " + reasoning)
                    self.log_event("LLM preconditions: " + str(preconditions))

                    if preconditions is None:
                        preconditions = []
                    if len(preconditions) == 0:
                        break #No suggested improvement from the LLM

                    #Run planner again after resolve suggestion from LLM
                    found_failed_node = False
                    i = 0
                    for i, node in enumerate(reversed(baseline.bt)):
                        if failed_action == node:
                            found_failed_node = True
                            break
                    if not found_failed_node:
                        self.log_event("Could not find failed node: " + failed_action)
                        break

                    py_tree.behavior_lists.convert_from_string(preconditions)
                    for precondition in preconditions:
                        if not isinstance(precondition, ParameterizedNode):
                            continue #Not found in conversion step, skip this precondition
                        baseline.add_new_sequential_sibling(len(baseline.bt) - i - 1, precondition)
                    string_bt = baseline.bt
                    py_tree.behavior_lists.convert_from_string(string_bt)

                    world_interface = self.planner_environment.sim_class(self.planner_environment.par.sim_parameters)

                    tree, _ = PyTree.create_from_list(string_bt, None, py_tree.behavior_lists, world_interface)
                    baseline, planned_py_tree =  planner.plan(world_interface, py_tree.behavior_lists, tree=tree,
                                                              remove_redundant_conditions=False, save_figs=False)

                    self.log_event("LLM resolved tree: " + str(baseline.bt))
                    attempts_left -= 1

            # After we are done, run planner again to clean up any redundant conditions
            baseline, planned_py_tree = planner.plan(world_interface, py_tree.behavior_lists,
                                                     remove_redundant_conditions=True,
                                                     tree=planned_py_tree, save_figs=False)

            self.get_string_tree(baseline)
            if not baseline.is_valid(locked_tree=locked_tree, locked_mask=mask):
                baseline = py_tree.bt
        else:
            baseline = py_tree.bt

        if (not self.learn_structure and self.backend_variant != BackendVariants.NO_BO) or self.backend_variant == BackendVariants.NO_GP:
            #Check first if structure has changed from previous BO run
            same_structure = False
            if self.bo_handler is not None:
                same_structure = baseline.same_structure(self.bo_handler.bt, categorical_value_diff_ok=False)

            individual = self.get_string_tree(baseline.bt[:])
            if same_structure:
                #We can reuse previous Bo handler, just make sure to include the new individuals parameters to test it first
                self.bo_handler.set_new_parameter_defaults(individual)
                self.bo_handler.fix_conditions()
                self.bo_handler.fix_mask(mask) # Fix any nodes in the locked mask
            else:
                # Not same structure of the tree, need a completely new run
                self.set_new_bo_handler(individual, mask)
                new_instance = True
            baseline = baseline.bt[:]
        else:
            baseline = baseline.bt[:]
            self.parameters.behavior_lists.convert_from_string(baseline)
            if self.gp_instance is None:
                self.gui_gp_log_id += 1
                self.initialize_gp()
                new_instance = True
            self.gp_instance.set_baseline(baseline, mask, locked_tree)
            self.gp_instance.set_fixed_structure(not self.learn_structure)
        self.baseline = baseline
        return new_instance

    def run_iterative_process(self) -> Any:
        """ Run the iterative process."""
        if self.simulating or (self.stepping and self.new_step_requested):
            return self.step_bt()
        else:
            return (None, None)

    def get_learning_pause(self) -> bool:
        """Get the learning pause state."""
        if self.learning_environment is not None:
            return self.learning_environment.get_paused()
        return False

    def set_learning_pause(self, pause: bool) -> None:
        """Set the learning pause state."""
        if self.learning_environment is not None:
            self.learning_environment.set_paused(pause)

    def step_bt(self) -> tuple[bool, list[str]]:
        """Step the behavior tree in the environment."""

        def append_status_recursive(
            node: pt.behaviour.Behaviour, exec_statuses: list[QtGui.QColor]
        ) -> None:
            if node.children:
                for child in node.children:
                    exec_statuses.append(self._map_status_to_color(child.status))
                    append_status_recursive(child, exec_statuses)
            else:
                return

        exec_statuses = []
        status = self.vis_environment.step()

        root = self.vis_environment.pytree[0].root
        exec_statuses.append(self._map_status_to_color(root.status))
        append_status_recursive(root, exec_statuses)
        self.new_step_requested = False
        return status, exec_statuses

    def compile_fitness(self) -> tuple[float, str]:
        """Compile fitness from the environment."""
        return self.vis_environment.compile_fitnesses()

    def get_behavior_list(self) -> BehaviorLists:
        """Return the behavior list."""
        return self.parameters.behavior_lists

    def get_behavior_from_LLM(self, input_text: str) -> list[str]: #pylint: disable=invalid-name
        """Get the behavior tree suggestion from the LLM."""
        # test_input = "put the red cube on top of the blue cube"
        client = llm.get_gpt_client()

        # Test answer
        # goals = [
        #     '"green cube" at pos "bowl" (0.0, 0.0, 0.025) 0.0?',
        #     '"red cube" at pos "blue cube" (0.0, 0.0, 0.05) 0.0?',
        # ]

        reasoning, goals = llm.get_goal_condition(
            client,
            self.learning_environment.par.scenario,
            self.learning_environment.scene_description,
            input_text,
            verbose=False,
        )
        if goals is not None and 'None' not in goals:
            string_tree = ["s("] + goals + [")"]
        else:
            string_tree =  []
        self.log_event("LLM to tree: " + input_text + ":" + str(string_tree))
        self.log_event("LLM reasoning: " + reasoning)
        return string_tree

    def get_behavior_from_name(self, name: str) -> tuple[ParameterizedNode, bool]:
        """ Get the behavior node from its name."""
        bt_list = self.parameters.behavior_lists

        if name == "Fallback" or name == "f(":
            return pt.composites.Selector("Fallback", memory=False), True
        elif name == "Sequence" or name == "s(":
            return pt.composites.Sequence("Sequence", memory=False), True

        else:
            for parameterized_node_template in bt_list.action_nodes + bt_list.condition_nodes:
                if parameterized_node_template.check_string_match(name):
                    node = fast_copy(parameterized_node_template)
                    try:
                        node.set_parameters_from_string(name)
                    except AttributeError:
                        node.set_default_parameter_values()
                    return node, False

    def get_control_node(self, string_node: str):
        """ Get the control node from its string representation."""
        if string_node == "f(":
            return pt.composites.Selector("Fallback", memory=False)
        elif string_node == "s(":
            return pt.composites.Sequence("Sequence", memory=False)
        else:
            raise ValueError(f"'{string_node}' is an unknown string representation of a control node.")

    def qt_root_to_behavior_tree(self, root: Node) -> tuple[PyTree, list[bool]]:
        """Build a py_trees Behavior Tree from a Qt Node."""
        if root is None:
            raise ValueError("ERROR: root node of the Behavior Tree not defined!")

        string_tree, mask = self._get_str_subtree_recursive(root)
        self.parameters.behavior_lists.convert_from_string(string_tree)
        self.last_built_bt = fast_copy(string_tree)
        self.last_mask = mask[:]
        bt = PyTree(string_tree, self.parameters, self.world_interface)
        return bt, mask

    def bt_to_qt(self, string_tree: list[str]) -> list[Node]:
        """Convert a behavior tree to a list of Qt Nodes."""
        self.parameters.behavior_lists.convert_from_string(string_tree)

        new_mask = [False] * len(string_tree)
        j = 0
        for i, node in enumerate(self.last_built_bt):
            if self.last_mask[i]:
                while j < len(string_tree):
                    if hasattr(string_tree[j], 'is_same') and string_tree[j].is_same(node) or string_tree[j] == node:
                        new_mask[j] = True
                        j += 1
                        break
                    j += 1

        bt = PyTree(string_tree, self.parameters, self.world_interface)
        return self._get_qt_subtree_recursive(bt.root, self.behavior_to_qt(bt.root), new_mask)[0]

    def qt_node_to_behavior(self, node: Node) -> Any:
        """Return the behavior represented by the Node element."""
        string_node = self.node_to_string(node)
        param_node, _ = self.get_behavior_from_name(string_node)

        try:
            return param_node.behavior
        except AttributeError:
            return self.get_control_node(string_node)

    def qt_node_to_parameters(self, node: Node):
        """Return the parameters of the Node element."""
        string_node = self.node_to_string(node)
        param_node, _ = self.get_behavior_from_name(string_node)
        try:
            # parameters = param_node.get_parameters()
            parameters = param_node.parameters
        except AttributeError:
            parameters = None

        return parameters

    def create_node_param_widget(self, value: NodeParameter) -> tuple[Any, str]:
        """Creates an input widget based on the parameter key."""
        additional_text = ""

        if value.data_type == ParameterTypes.LIST:
            if isinstance(value.list_of_values[0], bool):
                widget = QtWidgets.QCheckBox()
                widget.setChecked(str(value.value).lower() == "true")  # Convert to boolean
            else:
                widget = QtWidgets.QComboBox()
                widget.addItems([val for val in value.list_of_values])
                widget.setCurrentText(value.value)

        elif value.data_type == ParameterTypes.POSITION:
            spin_x = HintingSpinbox(
                value.value[0], value.min[0], value.max[0], 0.01
            )
            spin_y = HintingSpinbox(
                value.value[1], value.min[1], value.max[1], 0.01
            )
            spin_z = HintingSpinbox(
                value.value[2], value.min[2], value.max[2], 0.01
            )
            widget = (spin_x, spin_y, spin_z)  # Return a tuple of spin boxes
            additional_text = " [m] (x, y, z)"
        elif value.data_type == ParameterTypes.XY_POSITION:
            spin_x = HintingSpinbox(
                value.value[0], value.min[0], value.max[0], 0.01
            )
            spin_y = HintingSpinbox(
                value.value[1], value.min[1], value.max[1], 0.01
            )
            widget = (spin_x, spin_y)  # Return a tuple of spin boxes
            additional_text = " [m] (x, y)"

        elif value.data_type == ParameterTypes.FLOAT:
            widget = HintingSpinbox(value.value, value.min, value.max, value.step)
            additional_text = " [rad]"

        else:  # Default to a text input
            widget = QtWidgets.QLineEdit(str(value))
            return widget

        return widget, additional_text

    def update_node_parameters(self, node: Node, params: dict) -> None:
        """Update the parameters of the node."""
        string_node = self.node_to_string(node)
        param_node, _ = self.get_behavior_from_name(string_node)
        for key, node_param in param_node.parameters.items():
            node_param.value = params[key]

        node.set_label(param_node.to_string())

    def behavior_to_qt(
        self,
        behavior: Any,
        position: QtCore.QPointF = QtCore.QPointF(0, 0),
    ) -> Node:
        """Convert a behavior to a Qt Node."""
        if type(behavior) is pt.composites.Selector: #pylint: disable=unidiomatic-typecheck
            qt_item = Node(
                self._py_tree_node_item("octagon"),
                behavior.name,
                n_points=2,
                scalable=False,
            )
            qt_item.setPos(position)
        elif type(behavior) is pt.composites.Sequence: #pylint: disable=unidiomatic-typecheck
            qt_item = Node(
                self._py_tree_node_item("rectangle"),
                behavior.name,
                n_points=2,
                scalable=False,
            )
            qt_item.setPos(position)
        else:
            try:
                qt_item = Node(
                    self._py_tree_node_item("ellipse"),
                    behavior.to_string(),
                    n_points=1,
                    scalable=True,
                )
                qt_item.setPos(position)
            except Exception:
                return None

        return qt_item

    def node_to_string(self, node: Node) -> str:
        """Convert a Node to its string representation."""
        node_str = node.to_string()
        return {"Fallback": "f(", "Sequence": "s("}.get(node_str, node_str)

    def _get_qt_subtree_recursive(
        self, bt_root: pt.behaviour.Behaviour, qt_root: Node,
        mask: list[bool], mask_index: int = 0
    ) -> list[Node]:
        """ Recursively get the Qt subtree from a behavior tree root and its corresponding Qt root node.
            If a mask is provided, it will be used to set the locked state of the nodes."""
        if mask[mask_index]:
            qt_root.set_locked(True)
        if mask_index == 0:
            mask_index += 1
        node_list = [qt_root]

        for bt_child in bt_root.children:
            qt_child = self.behavior_to_qt(bt_child)
            if qt_child is not None:
                qt_root.add_child(qt_child)
                qt_child.set_parent(qt_root)
                if mask[mask_index]:
                    qt_child.set_locked(True)
                mask_index += 1
                if bt_child.children:
                    list_extension, mask_index = self._get_qt_subtree_recursive(bt_child, qt_child, mask, mask_index)
                    node_list.extend(list_extension)
                else:
                    node_list.append(qt_child)
        mask_index += 1  # For the closing parenthesis
        return node_list, mask_index

    def _get_str_subtree_recursive(self, root: Node) -> tuple[list[str], list[bool]]:
        string_tree = [self.node_to_string(root)]
        mask = [root.locked]
        if root.children: # Sort to make sure children are in correct order
            root.children.sort(key=lambda child: child.get_center()[0])
        for child in root.children:
            if child.children:
                string_tree.extend(self._get_str_subtree_recursive(child)[0])  # Flatten properly
                mask.extend(self._get_str_subtree_recursive(child)[1])
            else:
                string_tree.append(self.node_to_string(child))
                mask.append(child.locked)
                if len(child.connection_points) > 1:
                    # This is a control node without children, add parentheses still to keep structure
                    string_tree.append(")")
                    mask.append(False)
        if len(string_tree) > 1:
            string_tree.append(")")
            mask.append(False)
        return string_tree, mask

    def copy_py_tree_node_item(self, node_item: QtWidgets.QGraphicsItem) -> QtWidgets.QGraphicsItem:
        """
        Returns a copy of the py tree node item, to be used when creating new nodes.
        Doesn't copy position.
        """
        if isinstance(node_item, QtWidgets.QGraphicsRectItem):
            return self._py_tree_node_item("rectangle")
        elif isinstance(node_item, QtWidgets.QGraphicsEllipseItem):
            return self._py_tree_node_item("ellipse")
        elif isinstance(node_item, QtWidgets.QGraphicsPolygonItem):
            return self._py_tree_node_item("octagon")
        return None

    def _py_tree_node_item(self, shape: str, position: QtCore.QPointF = QtCore.QPointF(0, 0)) -> QtWidgets.QGraphicsItem:
        if shape == "ellipse":
            node_item = QtWidgets.QGraphicsEllipseItem(position.x(), position.y(), 0, 0)
            node_item.setBrush(QtGui.QBrush(QtGui.QColor("lightgray")))
        elif shape == "rectangle":
            w = 100
            h = 50
            node_item = QtWidgets.QGraphicsRectItem(
                position.x() - w / 2, position.y() - h / 2, w, h
            )
            node_item.setBrush(QtGui.QBrush(QtGui.QColor("orange")))
        elif shape == "octagon":
            points = [
                QtCore.QPointF(69.99, -10.54),
                QtCore.QPointF(69.99, -25.46),
                QtCore.QPointF(49.49, -36),
                QtCore.QPointF(20.5, -36),
                QtCore.QPointF(0, -25.46),
                QtCore.QPointF(0, -10.54),
                QtCore.QPointF(20.5, 0),
                QtCore.QPointF(49.49, 0),
            ]
            # Scale points proportionally to the rectangle's size
            scaled_points = [
                QtCore.QPointF(
                    p.x() * 1.5,  # Scale x-coordinate
                    p.y() * 1.5,  # Scale y-coordinate
                )
                for p in points
            ]
            # Offset the polygon to move its center to the desired position
            centroid_x = sum(p.x() for p in scaled_points) / len(scaled_points)
            centroid_y = sum(p.y() for p in scaled_points) / len(scaled_points)

            # Compute offset
            offset_x = position.x() - centroid_x
            offset_y = position.y() - centroid_y

            # Apply offset to each point
            new_points = [
                QtCore.QPointF(p.x() + offset_x, p.y() + offset_y) for p in scaled_points
            ]
            # Create the QPolygonF from the scaled points
            node_item = QtWidgets.QGraphicsPolygonItem(QtGui.QPolygonF(new_points))
            node_item.setBrush(QtGui.QBrush(QtGui.QColor("cyan")))

        return node_item

    def _map_status_to_color(self, status: pt.common.Status) -> QtGui.QColor:
        """Maps the status of a node to a color."""
        if status == pt.common.Status.SUCCESS:
            return QtGui.QColor("green")
        elif status == pt.common.Status.FAILURE:
            return QtGui.QColor("red")
        elif status == pt.common.Status.RUNNING:
            return QtGui.QColor("#fcd303")
            # return QtGui.QColor("yellow")
        else:
            return QtGui.QColor("gray")

    def log_event(self, event_name: str) -> None:
        """Logs actions like button presses."""
        log_event(event_name, self.experiment_name)

def log_best_data(best_data: BTData, folder_name, file_name) -> None:
    """Log the best data."""
    best_data.time = time.time()
    folder_name = get_log_folder(folder_name)
    with open_file(folder_name + file_name + ".txt", "a+") as f:
        f.write(f"{str(best_data)}\n")

    data = []

    pickle_path = folder_name + file_name + ".pickle"
    if isfile(pickle_path):
        with open_file(pickle_path, "rb") as f:
            data = pickle.load(f)
    data.append(best_data)

    with open_file(pickle_path, "wb") as f:
        pickle.dump(data, f)

def log_event(event_name: str, folder_name="gui_log", file_name="/action_log") -> None:
    """Logs events like button presses."""
    log_time = time.time()
    folder_name = get_log_folder(folder_name)
    event_name = event_name.replace("\n", "") + "\n"
    with open_file(folder_name + file_name + ".txt", "a+") as f:
        try:
            f.write(f"{str(log_time)}| {event_name}")
        except Exception as e:
            print(f"Error logging event: {e}")

def log_last_run_data(last_run_data: BTData, folder_name, file_name) -> None:
    """Log the last run data."""
    last_run_data.time = time.time()
    folder_name = get_log_folder(folder_name)
    with open_file(folder_name + file_name + ".txt", "a+") as f:
        f.write(f"{str(last_run_data)}\n")

    data = []

    pickle_path = folder_name + file_name + ".pickle"
    if isfile(pickle_path):
        with open_file(pickle_path, "rb") as f:
            data = pickle.load(f)
    data.append(last_run_data)

    with open_file(pickle_path, "wb") as f:
        pickle.dump(data, f)
