"""Script to create a random unbiased list of experiments with rejection sampling."""

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
import random
import math


def check_validity(gui_variant_order, gui_combinations, task_combination_order, task_combinations, new_task_combination):
    """Check if the new_task_combination is valid to add to the list."""

    #First check that we don't have too many already
    current_count = 0
    for task_combination in task_combination_order:
        if task_combination == new_task_combination:
            current_count += 1
    if current_count >= len(gui_variant_order) / len(task_combinations):
        return False

    #Next check that we don't have the same task combination already for the same gui_variant_order
    next_gui_variant = gui_variant_order[len(task_combination_order)]
    for index, gui_variant in enumerate(gui_variant_order):
        if index >= len(task_combination_order):
            break
        if gui_variant == next_gui_variant:
            if task_combination_order[index] == new_task_combination:
                return False

    #Finally check that we don't have too many of the combinations of tasks and gui variants
    for experiment_number in range(len(task_combinations[0])): #pylint: disable=consider-using-enumerate
        gui_variant = gui_combinations[next_gui_variant][experiment_number]
        task = task_combinations[new_task_combination][experiment_number]
        combination_count = 0
        for i in range(len(gui_variant_order)): #pylint: disable=consider-using-enumerate
            if i >= len(task_combination_order):
                break
            if gui_combinations[gui_variant_order[i]][experiment_number] == gui_variant and \
                task_combinations[task_combination_order[i]][experiment_number] == task:
                combination_count += 1
        if gui_variant == 1 or gui_variant == 2:  # Full and Manual
            if combination_count >= math.ceil(len(gui_variant_order) / 3 / 3):
                return False
        else:
            if combination_count >= math.ceil(len(gui_variant_order) / 3 / 4 / 3):
                return False

    return True

if __name__ == "__main__":
    gui_variants = [1, 2, 3, 4, 5, 6] # Full, Manual, Ablation1, Ablation2, Ablation3, Ablation4
    gui_combinations = [[1, 3, 2],
                        [1, 4, 2],
                        [1, 5, 2],
                        [1, 6, 2],
                        [1, 2, 3],
                        [1, 2, 4],
                        [1, 2, 5],
                        [1, 2, 6],
                        [3, 1, 2],
                        [4, 1, 2],
                        [5, 1, 2],
                        [6, 1, 2],
                        [3, 2, 1],
                        [4, 2, 1],
                        [5, 2, 1],
                        [6, 2, 1],
                        [2, 3, 1],
                        [2, 4, 1],
                        [2, 5, 1],
                        [2, 6, 1],
                        [2, 1, 3],
                        [2, 1, 4],
                        [2, 1, 5],
                        [2, 1, 6]]

    # Check that we have equal number of each variant in the combinations
    for variant in gui_variants:
        count = 0 #pylint: disable=invalid-name
        for combination in gui_combinations:
            if variant in combination:
                count += 1

        if variant == 1 or variant == 2:
            assert count == len(gui_combinations), f"Variant {variant} does not have equal distribution."
        else:
            assert count == len(gui_combinations) / 4, f"Variant {variant} does not have correct distribution."

    gui_variant_order = []
    for _ in range(2):
        for j in range(len(gui_combinations)):
            gui_variant_order.append(j)
    gui_variant_order.append(20)
    gui_variant_order.append(21)
    gui_variant_order.append(18)
    gui_variant_order.append(19)
    gui_variant_order.append(6)
    gui_variant_order.append(7)
    gui_variant_order.append(0)
    gui_variant_order.append(1)
    gui_variant_order.append(12)
    gui_variant_order.append(13)
    gui_variant_order.append(10)
    gui_variant_order.append(11)

    gui_counts = [0] * len(gui_combinations)
    for combination in gui_variant_order:
        gui_counts[combination] += 1
    assert max(gui_counts) <= 3
    start_counts = [0] * len(gui_variants)
    mid_counts = [0] * len(gui_variants)
    end_counts = [0] * len(gui_variants)
    for combination in gui_variant_order:
        start_counts[gui_combinations[combination][0] - 1] += 1
        mid_counts[gui_combinations[combination][1] - 1] += 1
        end_counts[gui_combinations[combination][2] - 1] += 1
    for variant in gui_variants:
        if variant <= 2:  # Full and Manual
            assert start_counts[variant - 1] == len(gui_variant_order) / 3, f"Variant {variant} does not have correct start distribution."
            assert mid_counts[variant - 1] == len(gui_variant_order) / 3, f"Variant {variant} does not have correct mid distribution."
            assert end_counts[variant - 1] == len(gui_variant_order) / 3, f"Variant {variant} does not have correct end distribution."
        else:
            assert start_counts[variant - 1] == len(gui_variant_order) / 12, f"Variant {variant} does not have correct start distribution."
            assert mid_counts[variant - 1] == len(gui_variant_order) / 12, f"Variant {variant} does not have correct mid distribution."
            assert end_counts[variant - 1] == len(gui_variant_order) / 12, f"Variant {variant} does not have correct end distribution."

    task_combinations = [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 2, 1], [3, 1, 2]]
    overall_attempts = 0
    all_valid = False
    while not all_valid and overall_attempts < 100:
        task_combination_order = []
        for _ in range(len(gui_variant_order)):
            valid = False
            attempts = 0
            while not valid and attempts < 10000:
                new_task_combination = random.choice(range(len(task_combinations)))
                valid = check_validity(gui_variant_order, gui_combinations, task_combination_order, task_combinations, new_task_combination)
                attempts += 1
            if not valid:
                print("Failed to find a valid task combination after 10000 attempts.")
                break
            else:
                task_combination_order.append(new_task_combination)
        if valid:
            all_valid = True
        overall_attempts += 1
    if not all_valid:
        print("Failed to find a valid task combination after 100 overall attempts.")
    print("Task combinations: ", len(task_combination_order))
    print("Task combination order: \n", task_combination_order)
