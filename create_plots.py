"""Code to generate plots."""

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
import pickle
import re
from bt_learning.gp import logplot
from bt_learning.bo.bo import BoHandler
import seaborn as sns

def get_average_blackbox_times(path):
    """ return average blackbox times from hypermapper logfile by using regex and store in a list"""
    blackbox_times = []
    # Load file
    with open("logs/" + path + "/hypermapper_logfile.log", 'r') as file:
        for line in file:
            match = re.search(r"Black box function time\s+([\d.]+)\s+sec", line)
            if match:
                blackbox_times.append(float(match.group(1)))
    if blackbox_times:
        return sum(blackbox_times[:5]) / len(blackbox_times[:5]), sum(blackbox_times[5:]) / len(blackbox_times[5:])
    return 0.0, 0.0

def get_gui_data(path, gui_rules):
    """ Retrieve GUI data from log if it follow the given rules. Rules should be a dictionary. """
    editor_best_log_path = "logs/" + path + "/editor_best_log.pickle"
    action_log_path = "logs/" + path + "/action_log.txt"
    start_time =  0.0
    allowed_user_ids = gui_rules.get("user_ids", range(1, 61))
    allowed_task_ordinals = gui_rules.get("task_ordinals", range(1, 4))
    allowed_variants = gui_rules.get("variant", ["FULL", "MANUAL_ONLY", "NO_BO", "NO_GP", "NO_LLM", "NO_PLANNER"])
    allowed_scenarios = gui_rules.get("scenario", ["trashpicking", "tableware", "cubebowl", "spheres"])
    if os.path.isfile(action_log_path):
        with open(action_log_path, 'r') as f:
            for line in f:
                ids = re.search(r"gui_log_(\d+)_(\d+)", line)
                if ids:
                    if int(ids.group(1)) not in allowed_user_ids:
                        return None, None
                    if int(ids.group(2)) not in allowed_task_ordinals:
                        return None, None

                    variant = re.search(r"variant: BackendVariants\.(\w+)", line)
                    if not variant or variant.group(1) not in allowed_variants:
                        return None, None

                    scenario = re.search(r"scenario: (\w+)", line)
                    if not scenario or scenario.group(1) not in allowed_scenarios:
                        return None, None
                    break
            for line in f:
                match = re.search(r"(\d+)\.\d+\| Fitness tab", line)
                if match:
                    start_time = float(match.group(1))
                    break
    if os.path.isfile(editor_best_log_path):
        with logplot.open_file(editor_best_log_path, "rb") as f:
            y_log = []
            processed_time = []
            data = pickle.load(f)
            for entry in data:
                y_log.append(entry.true_fitness)
                processed_time.append((entry.time - start_time) / 60.0) #Convert to minutes from start
        return processed_time, y_log
    else:
        return None, None

def get_log_data(path, bo_data=False, gui_data=False, gui_rules=None,
                 x_axis_steps=False, remove_average_blackbox_time=False, blackbox_time_factor=0.0):
    """ Retrieve our data """
    logs = []
    if not os.path.isdir("logs/" + path):
        raise ValueError("Path {} is not a directory. Working directory: {}".format(
            "logs/" + path, os.getcwd()))
    if path[-1] != '/':
        path += '/'

    if gui_data:
        for directory in os.listdir("logs/" + path):
            if os.path.isdir(os.path.join("logs/" + path, directory)):
                logs.append(path + directory)
    else: # Only get bottom directories
        for rootdir, dirs, files in os.walk("logs/" + path):
            if dirs == [] and not files == [] and len(rootdir) > 5 and not "subtree" in rootdir:
                logs.append(rootdir[5:])
    if len(logs) == 0:
        raise ValueError(
            "No subdirectories found in {}".format("logs/" + path))
    #print("Found " + str(len(logs)) + " logs for " + path)

    x_logs = []
    y_logs = []
    for log in logs:
        if gui_data:
            steps = None
            processed_time, y_log = get_gui_data(log, gui_rules)
            if y_log is None:
                continue
            else:
                y_logs.append(y_log)
        else:
            processed_time = []
            average_blackbox_time_early = 0.0
            average_blackbox_time_late = 0.0
            if bo_data:
                fitness, _, steps, raw_time = BoHandler.get_bo_data([log])
                y_logs.append(fitness[0])
                raw_time = raw_time[0]
                steps = steps[0]
                raw_time_start = 0
                if remove_average_blackbox_time:
                    average_blackbox_time_early, average_blackbox_time_late = get_average_blackbox_times(log)
                    average_blackbox_time_early *= blackbox_time_factor
                    average_blackbox_time_late *= blackbox_time_factor
            else:
                raw_time = logplot.get_time(log)
                y_logs.append(logplot.get_best_fitness(log))
                raw_time_start = 1
                if x_axis_steps:
                    steps = logplot.get_n_steps(log)
                print(log + " fitness: " + str(y_logs[-1][-1]) + ", time: " + str(int(((raw_time[-1] - raw_time[0]) / 60.0))) + " minutes")
            i = 1
            for t in raw_time[raw_time_start:]:
                average_blackbox_time = average_blackbox_time_late if i > 23 else average_blackbox_time_early
                processed_time.append((t - raw_time[0] - i * average_blackbox_time) / 60.0) #Convert to minutes from start
                i += 1
        if x_axis_steps:
            if steps is not None:
                x_logs.append(steps)
        else:
            if processed_time is not None:
                x_logs.append(processed_time)

    return x_logs, y_logs

def get_variant_averages():
    """ Get and print averages for different variants """
    for scenario in ["trashpicking", "tableware", "cubebowl"]:
        for variant in ["FULL", "MANUAL_ONLY", "NO_BO", "NO_GP", "NO_LLM", "NO_PLANNER"]:
            gui_rules = {}
            gui_rules["variant"] = [variant]
            gui_rules["scenario"] = [scenario]
            _, y_logs = get_log_data("gui_logs", bo_data=False, gui_data=True, gui_rules=gui_rules, x_axis_steps=False)
            final_fitnesses = []
            for y_log in y_logs:
                final_fitnesses.append(y_log[-1])
            if len(final_fitnesses) > 0:
                average_fitness = sum(final_fitnesses) / len(final_fitnesses)
                average_fitness = normalize_score(scenario, average_fitness)
                print("Scenario: {}, Variant: {}, runs: {}, average final fitness: {:.1f}".format(
                    scenario, variant, len(final_fitnesses), average_fitness))
            else:
                print("Scenario: {}, Variant: {}, runs: 0".format(scenario, variant))

def get_variant_bests():
    """ Get and print bests for different variants """
    for scenario in ["trashpicking", "tableware", "cubebowl"]:
        gui_rules = {}
        gui_rules["variant"] = ["FULL", "MANUAL_ONLY", "NO_BO", "NO_GP", "NO_LLM", "NO_PLANNER"]
        gui_rules["scenario"] = [scenario]
        _, y_logs = get_log_data("gui_logs", bo_data=False, gui_data=True, gui_rules=gui_rules, x_axis_steps=False)
        best_fitness = -float('inf')
        for y_log in y_logs:
            if y_log[-1] > best_fitness:
                best_fitness = y_log[-1]
        if best_fitness > -float('inf'):
            print("Scenario: {}, best fitness: {}".format(
                scenario, best_fitness))
        else:
            print("WARNING: Scenario: {}, found no decent fitness".format(scenario))

def get_ai_only_averages():
    """ Get and print averages for AI only runs"""
    pickle_path = "logs/ai_only/full_runs.pickle"
    if os.path.isfile(pickle_path):
        with logplot.open_file(pickle_path, "rb") as f:
            full_runs = pickle.load(f)
        for scenario in ["trashpicking", "tableware", "cubebowl"]:
            sum_fitnesses = 0
            n_fitnesses = 0
            for run in full_runs:
                try:
                    if run["scenario"] == scenario:
                        user_id = run["user_id"]
                        goal_setting_time = run["goal_setting_time"] / 60.0
                        x_logs, y_logs = get_log_data("ai_only/user_" + user_id)

                        # Remove anything found after time was up
                        for i in range(len(x_logs)):
                            while x_logs[i][-1] + goal_setting_time > 15:
                                x_logs[i] = x_logs[i][:-1]
                                y_logs[i] = y_logs[i][:-1]

                        for y_log in y_logs:
                            sum_fitnesses += y_log[-1]
                            n_fitnesses += 1
                            print("User: {}, scenario: {}, goal setting time: {}, final fitness: {}".format(
                                user_id, scenario, goal_setting_time, y_log[-1]))
                        for x_log in x_logs:
                            print("Total times: {}".format(x_log[-1] + goal_setting_time))
                except Exception:
                    print("Could not load for user_id: ", run["user_id"])
            if n_fitnesses > 0:
                normalized_average = normalize_score(scenario, sum_fitnesses / n_fitnesses)
                print("Scenario: {}, runs: {}, average final fitness: {:.1f}".format(
                    scenario, n_fitnesses, normalized_average))

def normalize_y_logs(y_logs):
    """ 
    Normalize y logs to be between 0 and 100.
    Best values are found by running get_variant_bests
    Worst values are found by testing a tree of size 2 that fails directly and does nothing.
    """
    best = {}
    best["trashpicking"] = -9717
    best["tableware"] = -9795
    best["cubebowl"] = -4492
    worst = {}
    worst["trashpicking"] = -15000
    worst["tableware"] = -15000
    worst["cubebowl"] = -7000

def normalize_score(scenario, score):
    """
    Normalize a single score to be between 0 and 100. 
    Best values are found by running get_variant_bests to scan the logs
    Worst values are found by testing a tree of size 2 that fails directly and does nothing.
    """
    best = {}
    best["trashpicking"] = -9717.450424161509
    best["tableware"] = -7906.11451650018
    best["cubebowl"] = -4394.173969891566

    worst = {}
    worst["trashpicking"] = -24994.42352222
    worst["tableware"] = -33808.71956986
    worst["cubebowl"] = -21950.87782906
    normalized = (score - worst[scenario]) / (best[scenario] - worst[scenario]) * 100.0
    return normalized
