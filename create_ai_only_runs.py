"""Code to generate ai only runs."""

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
import re
import pickle
import time
from bt_learning.gp.logplot import open_file
import scenarios.cubes_and_bowl
import scenarios.tableware
import scenarios.trashpicking
from bt_gui.pytrees_backend import PytreesBackend, BackendVariants
from interfaces.py_trees_interface import PyTree

def get_full_runs():
    """ Returns a list of full runs and some data associated with them"""
    path = "gui_logs/"
    logs = []
    if not os.path.isdir("logs/" + path):
        raise ValueError("Path {} is not a directory. Working directory: {}".format(
            "logs/" + path, os.getcwd()))
    if path[-1] != '/':
        path += '/'

    for directory in os.listdir("logs/" + path):
        if os.path.isdir(os.path.join("logs/" + path, directory)):
            logs.append(path + directory)

    full_runs = []
    for log in logs:
        action_log_path = "logs/" + log + "/action_log.txt"
        if os.path.isfile(action_log_path):
            with open(action_log_path, 'r') as f:
                user_id = 0
                start_time = 0.0
                log_info = {}
                for line in f:
                    ids = re.search(r"gui_log_(\d+)_(\d+)", line)
                    if ids:
                        user_id = ids.group(1)
                    else:
                        continue

                    variant = re.search(r"variant: BackendVariants\.(\w+)", line)
                    if variant:
                        if variant.group(1) == "FULL":
                            log_info["user_id"] = user_id
                            log_info["path"] = log
                            scenario = re.search(r"scenario: (\w+)", line)
                            if scenario:
                                log_info["scenario"] = scenario.group(1)
                        break
                if log_info:
                    for line in f:
                        match = re.search(r"(\d+)\.\d+\| Fitness tab", line)
                        if match:
                            start_time = float(match.group(1))
                            log_info["start_time"] = start_time
                            break
                    for line in f:
                        saved_goals = re.search(r"Saved goals: \[(.+?)\]", line)
                        if saved_goals:
                            goals_str = saved_goals.group(1)

                            # Ugly solution for splitting string into list of goals while keeping some commas for offsets
                            goal_tree = goals_str.split(', "',)
                            for i in range(len(goal_tree)):
                                if not goal_tree[i].startswith('"'):
                                    goal_tree[i] = '"' + goal_tree[i]
                                goal_tree[i] = goal_tree[i].replace("\"'s('", 's(').replace("'f('", 'f(').replace(", ')'", '')
                            goal_tree.append(')')

                            log_info["goals"] = goal_tree
                            goal_time = re.search(r"(\d+\.\d+)|Saved goals:", line)
                            log_info["goal_time"] = float(goal_time.group(1)) if goal_time else None
                            log_info["goal_setting_time"] = log_info["goal_time"] - start_time if goal_time else None

                    full_runs.append(log_info)

    return full_runs

def create_ai_only_runs(full_runs):
    """ Makes sure we have ai only runs for all full runs."""
    n_runs_per_full = 5
    if not os.path.isdir("logs/ai_only"):
        os.mkdir("logs/ai_only")

    pickle_path = "logs/ai_only/full_runs.pickle"
    with open_file(pickle_path, "wb") as f:
        pickle.dump(full_runs, f)

    # Create and start environments
    learning_environments = {}
    planner_environments = {}
    learning_environments["cubebowl"] = scenarios.cubes_and_bowl.get_environment(planner_environment=False,
                                                                                 n_agents=32, preplan_subtrees=True)
    learning_environments["cubebowl"].start_simulation(channel=50021, headless=True, timescale=10, unity_log_file="learning_unity.log")
    planner_environments["cubebowl"] = scenarios.cubes_and_bowl.get_environment(planner_environment=True)
    learning_environments["tableware"] = scenarios.tableware.get_environment(planner_environment=False,
                                                                             n_agents=32, preplan_subtrees=True)
    learning_environments["tableware"].start_simulation(channel=50031, headless=True, timescale=10, unity_log_file="learning_unity.log")
    planner_environments["tableware"] = scenarios.tableware.get_environment(planner_environment=True)
    learning_environments["trashpicking"] = scenarios.trashpicking.get_environment(planner_environment=False,
                                                                                   n_agents=32, preplan_subtrees=True)
    learning_environments["trashpicking"].start_simulation(channel=50041, headless=True, timescale=10, unity_log_file="learning_unity.log")
    planner_environments["trashpicking"] = scenarios.trashpicking.get_environment(planner_environment=True)

    for run in full_runs:
        if not os.path.isdir("logs/ai_only/user_" + run["user_id"]):
            os.mkdir("logs/ai_only/user_" + run["user_id"])
            for i in range(n_runs_per_full):
                os.mkdir("logs/ai_only/user_" + run["user_id"] + "/run_" + str(i))
                create_ai_only_run(learning_environments[run["scenario"]], planner_environments[run["scenario"]], run, i)

def create_ai_only_run(learning_environment, planner_environment, run_info, run_index):
    """ Creates a single ai only run based on the full run info provided."""
    experiment_name = "ai_only/user_" + run_info["user_id"] + "/run_" + str(run_index)
    print("Creating ai only run at: {}".format(experiment_name))
    learning_environment.set_seeds(int(run_index))
    backend = PytreesBackend(None,
                             learning_environment,
                             planner_environment,
                             backend_variant=BackendVariants.FULL,
                             experiment_name=experiment_name,
                             minimal_backend=True)  # Use minimal backend to avoid starting simulations

    # Set goal in env
    goals = run_info["goals"][:]
    backend.parameters.behavior_lists.convert_from_string(goals)
    backend.set_goals_from_tree(goals)

    # Set baseline
    world_interface = planner_environment.sim_class(planner_environment.par.sim_parameters)
    pytree = PyTree(goals, backend.parameters, world_interface)
    backend.set_baseline(pytree, [])

    start_time = time.time()

    # Step through the learning
    while backend.gp_instance.is_runnable() and time.time() - start_time + run_info["goal_setting_time"] < 15 * 60:
        backend.gp_instance.step_gp()
    backend.gp_instance.get_final_info()

if __name__ == "__main__":
    full_runs = get_full_runs()
    create_ai_only_runs(full_runs)
