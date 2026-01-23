"""Code to process data and save in a csv file."""

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
import os.path
import re
import pickle
import pandas
from bt_learning.gp import logplot
from create_plots import normalize_score, get_log_data

variant_name_list = ['FULL', 'MANUAL_ONLY', 'NO_BO','NO_GP', 'NO_LLM', 'NO_PLANNER']
task_name_list = ['cubebowl', 'tableware', 'trashpicking']

def load_survey_results():
    """ Load survey results from csv file. """
    file_name = "logs/survey_results.csv"

    if not os.path.isfile(file_name):
        raise ValueError("File {} does not exist.".format(file_name))
    return pandas.read_csv(file_name, sep=',')

def load_experiment_data(user_id, task_index):
    """ Load experiment data for a given user and task. """
    folder_path = "logs/gui_logs/gui_log_{}_{}/".format(user_id, task_index)
    action_log_path = folder_path + "action_log.txt"
    editor_best_log_path = folder_path + "editor_best_log.pickle"
    ai_log_path = folder_path + "ai_log.pickle"
    log_info = {}
    if os.path.isfile(action_log_path):
        with open(action_log_path, 'r') as f:
            # Find start time
            start_time = 0.0
            for line in f:
                match = re.search(r"(\d+)\.\d+\| Fitness tab", line)
                if match:
                    start_time = float(match.group(1))
                    log_info["start_time"] = start_time
                    break

            # Find goal setting time
            for line in f:
                saved_goals = re.search(r"Saved goals: \[(.+?)\]", line)
                if saved_goals:
                    goal_time = re.search(r"(\d+\.\d+)\| Saved goals:", line)
                    log_info["goal_time"] = float(goal_time.group(1)) if goal_time else None
                    log_info["goal_setting_time"] = log_info["goal_time"] - start_time if goal_time else None

        # Start over to find LLM usage
        with open(action_log_path, 'r') as f:
            # Find whether LLM was used for goal generation
            for line in f:
                llm_used = re.search(r"LLM to tree", line)
                if llm_used:
                    log_info["llm_used"] = True
                    break

        # Start over to find locking usage
        last_time = log_info.get("start_time", 0.0)
        current_n_locks = 0
        time_locked_nodes = 0.0
        locked_nodes_sumprod = 0.0 # n locked nodes * time
        structure_checkbox = True
        optimizing_parameters_only = False
        time_optimizing_parameters_only = 0.0
        with open(action_log_path, 'r') as f:
            editor_tab_found = False
            for line in f:
                match = re.search(r"(\d+\.\d+)\| Editor tab", line)
                if match:
                    editor_tab_found = True
                    continue
                if editor_tab_found:
                    send_match = re.search(r"(\d+\.\d+)\| Sent BT to AI:", line)
                    if send_match:
                        log_info["sent_bt_at_least_once"] = True
                    load_match = re.search(r"(\d+\.\d+)\| Loaded BT to editor:", line)
                    if load_match:
                        log_info["loaded_bt_at_least_once"] = True
        with open(action_log_path, 'r') as f:
            # Find out how much the user locked nodes and structure
            for line in f:
                time_match = re.search(r"(\d+\.\d+)\| Sent BT to AI:", line)
                if time_match:
                    current_time = float(time_match.group(1))

                    if optimizing_parameters_only:
                        time_optimizing_parameters_only += (current_time - last_time)
                    if structure_checkbox:
                        optimizing_parameters_only = False
                    else:
                        optimizing_parameters_only = True
                        log_info["lock_structure_at_least_once"] = True

                    mask_match = re.search(r"Sent BT to AI:(.+)", line)
                    if mask_match:
                        # Count number of 'True' in the mask
                        true_count = len(re.findall(r"True", mask_match.group(1)))
                        if true_count > 0:
                            log_info["locked_nodes_at_least_once"] = True
                        if current_n_locks > 0:
                            time_locked_nodes += (current_time - last_time)
                            locked_nodes_sumprod += current_n_locks * (current_time - last_time)
                        current_n_locks = true_count
                        last_time = current_time

                structure_disabled_match = re.search(r"(\d+\.\d+)\| AI structure optimization disabled", line)
                if structure_disabled_match:
                    structure_checkbox = False
                else:
                    structure_enabled_match = re.search(r"(\d+\.\d+)\| AI structure optimization enabled", line)
                    if structure_enabled_match:
                        structure_checkbox = True

                experiment_completed = re.search(r"(\d+\.\d+)\| Experiment completed", line)
                if experiment_completed:
                    current_time = float(experiment_completed.group(1))
                    if optimizing_parameters_only:
                        time_optimizing_parameters_only += (current_time - last_time)
                    if current_n_locks > 0:
                        time_locked_nodes += (current_time - last_time)
                        locked_nodes_sumprod += current_n_locks * (current_time - last_time)

        log_info["time_locked_nodes"] = time_locked_nodes
        log_info["avg_locked_nodes"] = locked_nodes_sumprod / (15 * 60)  # Assuming max time is 15 minutes
        log_info["time_locked_structure"] = time_optimizing_parameters_only


    if os.path.isfile(editor_best_log_path):
        with logplot.open_file(editor_best_log_path, "rb") as f:
            best_log = []
            successes_log = []
            data = pickle.load(f)
            first_33_found = False
            first_67_found = False
            first_100_found = False

            for entry in data:
                best_log.append(entry.true_fitness)
                successes_log.append(entry.true_successes)
                if not first_33_found and entry.true_successes >= 1.0:
                    log_info["time_to_33_success"] = entry.time - log_info["start_time"]
                    first_33_found = True
                if not first_67_found and entry.true_successes >= 2.0:
                    log_info["time_to_67_success"] = entry.time - log_info["start_time"]
                    first_67_found = True
                if not first_100_found and entry.true_successes >= 3.0:
                    log_info["time_to_100_success"] = entry.time - log_info["start_time"]
                    first_100_found = True
            log_info["highest_score"] = best_log[-1] if best_log else None
            log_info["successful_subtasks"] = successes_log[-1] if successes_log else None

    if os.path.isfile(ai_log_path):
        with logplot.open_file(editor_best_log_path, "rb") as f:
            best_log = []
            successes_log = []
            data = pickle.load(f)

            for entry in data:
                best_log.append(entry.true_fitness)
                successes_log.append(entry.true_successes)
            log_info["highest_ai_score"] = best_log[-1] if best_log else None
            log_info["successful_ai_subtasks"] = successes_log[-1] if successes_log else None

    return log_info

def process_data(survey_data):
    """ Process data to combine survey data and experiment data and return combined processed data. """
    processed_data = []
    for index, row in survey_data.iterrows():
        for task_index in range(1, 4):  # Assuming each participant has 3 entries to process
            processed_entry = {}
            processed_entry['id'] = row['ParticipantID']
            processed_entry['age'] = row['age']
            processed_entry['gender'] = row['gender']
            processed_entry['variant_id'] = row['VariantID{}'.format(task_index)]
            processed_entry['variant_name'] = variant_name_list[processed_entry['variant_id'] - 1]
            processed_entry['task_id'] = row['TaskID{}'.format(task_index)]
            processed_entry['task_name'] = task_name_list[processed_entry['task_id'] - 1]
            processed_entry['task_order_index'] = task_index
            processed_entry['fam_robpro'] = row['fam_robpro']
            processed_entry['oft_robpro'] = row['oft_robpro']
            processed_entry['exp_robpro'] = row['exp_robpro']
            processed_entry['fam_pro'] = row['fam_pro']
            processed_entry['oft_pro'] = row['oft_pro']
            processed_entry['exp_pro'] = row['exp_pro']
            processed_entry['fam_robots'] = row['fam_robots']
            processed_entry['oft_robots'] = row['oft_robots']
            processed_entry['exp_robots'] = row['exp_robots']
            processed_entry['fam_bt'] = row['fam_bt']
            processed_entry['oft_bt'] = row['oft_bt']
            processed_entry['exp_bt'] = row['exp_bt']
            processed_entry['sus_1'] = row['sus_{}_1'.format(task_index)]
            processed_entry['sus_2'] = row['sus_{}_2'.format(task_index)]
            processed_entry['sus_3'] = row['sus_{}_3'.format(task_index)]
            processed_entry['sus_4'] = row['sus_{}_4'.format(task_index)]
            processed_entry['sus_5'] = row['sus_{}_5'.format(task_index)]
            processed_entry['sus_6'] = row['sus_{}_6'.format(task_index)]
            processed_entry['sus_7'] = row['sus_{}_7'.format(task_index)]
            processed_entry['sus_8'] = row['sus_{}_8'.format(task_index)]
            processed_entry['sus_9'] = row['sus_{}_9'.format(task_index)]
            processed_entry['sus_10'] = row['sus_{}_10'.format(task_index)]

            found = False
            for rank_index in range(1, 4):
                if row['gui_{}'.format(rank_index)] == 'GUI {}'.format(task_index):
                    processed_entry['rank'] = rank_index
                    found = True
                    break
            if not found:
                processed_entry['rank'] = None
                print("Warning: No rank found for participant ID {}, task {}".format(row['ParticipantID'], task_index))

            log_info = load_experiment_data(row['ParticipantID'], task_index)
            processed_entry['time_to_set_goal'] = log_info['goal_setting_time']
            processed_entry['highest_score'] = normalize_score(processed_entry['task_name'], log_info['highest_score'])
            processed_entry['successful_subtasks'] = log_info['successful_subtasks']
            processed_entry['time_to_33_success'] = log_info.get('time_to_33_success', 'NA')
            processed_entry['time_to_67_success'] = log_info.get('time_to_67_success', 'NA')
            processed_entry['time_to_100_success'] = log_info.get('time_to_100_success', 'NA')
            processed_entry['llm_used'] = log_info.get('llm_used', False)
            processed_entry['locked_nodes_at_least_once'] = log_info.get('locked_nodes_at_least_once', False)
            processed_entry['time_locked_nodes'] = log_info.get('time_locked_nodes', 0.0)
            processed_entry['avg_locked_nodes'] = log_info.get('avg_locked_nodes', 0.0)
            processed_entry['lock_structure_at_least_once'] = log_info.get('lock_structure_at_least_once', False)
            processed_entry['time_locked_structure'] = log_info.get('time_locked_structure', 0.0)
            processed_entry['sent_bt_at_least_once'] = log_info.get('sent_bt_at_least_once', False)
            processed_entry['loaded_bt_at_least_once'] = log_info.get('loaded_bt_at_least_once', False)
            processed_entry['highest_ai_score'] = normalize_score(processed_entry['task_name'], log_info.get('highest_ai_score', -100000.0))
            processed_entry['successful_ai_subtasks'] = log_info.get('successful_ai_subtasks', 0)

            for seed in range(1, 6):
                processed_entry['ai_only_score_' + str(seed)] = 0.0
            if processed_entry['variant_name'] == 'FULL':
                try:
                    goal_setting_time = log_info["goal_setting_time"] / 60.0  # Convert to minutes
                    x_logs, y_logs = get_log_data("ai_only/user_" + str(processed_entry['id']))
                    if len(y_logs) != 5:
                        print("Warning: Expected 5 ai only runs for user_id {}, found {}".format(
                            processed_entry['id'], len(y_logs)))
                    else:
                        for seed in range(5):
                            # Remove anything found after time was up
                            while x_logs[seed][-1] + goal_setting_time > 15:
                                x_logs[seed] = x_logs[seed][:-1]
                                y_logs[seed] = y_logs[seed][:-1]

                            processed_entry['ai_only_score_' + str(seed + 1)] = normalize_score(
                                processed_entry['task_name'], y_logs[seed][-1])
                except Exception:
                    print("Could not load AI only for user_id: ", processed_entry['id'])
            processed_data.append(processed_entry)

    return processed_data

def save_processed_data(processed_data):
    """ Save data to csv file. """
    csv_file_name = "logs/processed_data.csv"
    df = pandas.DataFrame(data=processed_data)
    df.to_csv(csv_file_name,
                mode='w',
                sep=',',
                index=False)

    pickle_path = "logs/processed_data.pickle"
    with logplot.open_file(pickle_path, "wb") as f:
        pickle.dump(processed_data, f)

def load_processed_data():
    """ Load processed data from pickle file. """
    pickle_path = "logs/processed_data.pickle"
    with logplot.open_file(pickle_path, "rb") as f:
        df = pickle.load(f)
    return df

if __name__ == "__main__":
    survey_data = load_survey_results()
    processed_data = process_data(survey_data)
    save_processed_data(processed_data)
