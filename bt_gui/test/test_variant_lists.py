""" Unit test for checking the variant lists for errors. The lists originally were created using experiment_randomizer.py """

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

from bt_gui.gui_main import get_variant_id, get_environment_from_task_id, get_variant_and_environment, get_variant_from_id, get_variant_seq_from_user_id
from bt_gui.pytrees_backend import BackendVariants

import scenarios.cubes_and_bowl
import scenarios.tableware
import scenarios.trashpicking

def test_samples():
    """ Tests a few samples to see that they are correct """
    user_id = 1
    experiment = 2
    variant, task = get_variant_and_environment(user_id, experiment)
    assert variant == BackendVariants.NO_BO
    assert task is scenarios.tableware.get_environment

    user_id = 36
    experiment = 3
    variant, task = get_variant_and_environment(user_id, experiment)
    assert variant == BackendVariants.MANUAL_ONLY
    assert task is scenarios.cubes_and_bowl.get_environment

    user_id = 12
    experiment = 2
    variant, task = get_variant_and_environment(user_id, experiment)
    assert variant == BackendVariants.FULL
    assert task is scenarios.cubes_and_bowl.get_environment

    user_id = 60
    experiment = 1
    variant, task = get_variant_and_environment(user_id, experiment)
    assert variant == BackendVariants.NO_PLANNER
    assert task is scenarios.cubes_and_bowl.get_environment

    user_id = 44
    experiment = 2
    variant, task = get_variant_and_environment(user_id, experiment)
    assert variant == BackendVariants.NO_PLANNER
    assert task is scenarios.trashpicking.get_environment


def test_sums():
    """ Tests a number of sums to make sure they are correct and that we have a correct distribution """
    task_counts = [0, 0, 0]
    variant_counts = [0, 0, 0, 0, 0, 0]
    for user_id in range(1, 61):
        for experiment in range(1, 4):
            variant, task = get_variant_and_environment(user_id, experiment)
            assert variant in [BackendVariants.FULL, BackendVariants.NO_BO, BackendVariants.NO_GP,
                               BackendVariants.NO_LLM, BackendVariants.NO_PLANNER, BackendVariants.MANUAL_ONLY]
            assert task in [scenarios.cubes_and_bowl.get_environment,
                            scenarios.tableware.get_environment,
                            scenarios.trashpicking.get_environment]
            if task is scenarios.cubes_and_bowl.get_environment:
                task_counts[0] += 1
            elif task is scenarios.tableware.get_environment:
                task_counts[1] += 1
            elif task is scenarios.trashpicking.get_environment:
                task_counts[2] += 1
            if variant is BackendVariants.FULL:
                variant_counts[0] += 1
            elif variant is BackendVariants.MANUAL_ONLY:
                variant_counts[1] += 1
            elif variant is BackendVariants.NO_BO:
                variant_counts[2] += 1
            elif variant is BackendVariants.NO_GP:
                variant_counts[3] += 1
            elif variant is BackendVariants.NO_LLM:
                variant_counts[4] += 1
            elif variant is BackendVariants.NO_PLANNER:
                variant_counts[5] += 1

    assert task_counts == [60, 60, 60]
    assert variant_counts == [60, 60, 15, 15, 15, 15]

if __name__ == "__main__":
    test_samples()
    test_sums()