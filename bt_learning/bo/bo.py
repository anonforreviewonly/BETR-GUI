"""
Main handler for running Bayesian Optimization
"""
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
import pickle
import time
from statistics import mean
from typing import List, Any
from dataclasses import dataclass
import random
import numpy as np

import pandas
from bt_learning.gp import logplot
from bt_learning.bo.hypermapper_integration import HypermapperOptimization
from behaviors.behavior_tree import BT
from behaviors.common_behaviors import ParameterizedNode, fast_copy

@dataclass
class HandlerSettings:
    """Data class for parameters for the BoHandler."""
    log_name: str = 'bo_test'             # Name of the log
    iterations: int = 100                 # Number of iterations to run
    runs_per_bt: int = 20                 # Maximum number of runs with different seeds per bt
    validation_runs: int = 20             # Number of validation to run
    hotstart: bool = False                # Hotstart from a previous run or start from scratch
    random_search: bool = False           # Use random step search instead of BO
    random_forest: bool = False           # Use random forest model instead of GP
    cascaded: bool = False                # Run subtrees sequentially in cascaded learning
    batch_size: int = 1                   # Number of data points to test in each iteration
    extra_settings: Any = None            # Extra settings to pass to hypermapper


class BoHandler():
    """ Class to handle Bayesian Optimization runs. Gets fitness and returns fitness and logs data """
    def __init__(self, environment, bt, settings):
        self.bt = fast_copy(bt)
        self.environment = environment
        self.behavior_lists = environment.par.py_tree_parameters.behavior_lists
        self.log_name = settings.log_name
        self.log_folder = logplot.get_log_folder(settings.log_name)
        self.csv_file_name = self.log_folder + "/bo_log.csv"
        self.extra_settings = settings.extra_settings
        self.iterations = settings.iterations
        self.current_iteration = 1
        self.parameter_values = []
        self.fitness = []
        self.net_fitness = []
        self.true_fitness = []
        self.true_successes = []
        self.steps = []
        self.time = []
        self.validation_fitness = []
        self.n_validation_successes = []
        self.cumulative_steps = []
        self.best_fitness = -9999999999
        self.best_net_fitness = -9999999999
        self.best_fitness_updated = False
        self.best_bt = fast_copy(bt)
        self.best_current_bt = fast_copy(bt)
        self.mask = []
        self.hotstart = settings.hotstart
        self.cascaded = settings.cascaded
        self.random_search = settings.random_search
        self.random_forest = settings.random_forest
        if settings.hotstart:
            self.parameter_values, self.fitness, self.net_fitness, self.true_fitness, self.true_successes, \
                self.validation_fitness, self.n_validation_successes, \
                self.steps, self.cumulative_steps, self.best_fitness, \
                self.best_net_fitness, self.best_bt, self.time = BoHandler.load_data(settings.log_name)
            self.bt = fast_copy(self.best_bt)
            self.best_current_bt = fast_copy(self.best_bt)
        else:
            logplot.clear_logs(settings.log_name)

        self.runs_per_bt = settings.runs_per_bt
        self.validation_runs = settings.validation_runs
        self.batch_size = settings.batch_size

        self.fix_set_categorical()
        self.current_bt = self.bt
        self.new_parameter_defaults = False

    def set_new_parameter_defaults(self, bt):
        """ Sets a new default that must be tested in next iteration """
        self.bt = bt
        self.current_bt = self.bt
        self.fix_set_categorical()
        self.new_parameter_defaults = True

    def fix_set_categorical(self):
        """
        Fixes the value of any categorical that already has a set value
        so that value doesn't change during learning
        """
        for node in self.bt:
            if isinstance(node, ParameterizedNode) and node.parameters is not None:
                for _, parameter in node.parameters.items():
                    if parameter.list_of_values != [] and parameter.value not in ['']:
                        parameter.list_of_values = [parameter.value]

    def fix_conditions(self, behavior_type=None, threshold=None, value=None):
        """ Fixes the values of any conditions of the given type """
        if behavior_type is not None:
            for node in self.bt:
                if isinstance(node, ParameterizedNode) and node.behavior is behavior_type:
                    self.fix_node(node, threshold, value)
        else:
            # Fix all nodes that are in the list of goals
            goals = self.environment.get_goals()
            if goals != []:
                for node in self.bt:
                    if isinstance(node, ParameterizedNode) and node in goals:
                        self.fix_node(node, threshold, value)

    def fix_mask(self, mask):
        """ Fixes the values of the nodes in the mask"""
        if isinstance(mask, list) and len(mask) == len(self.bt):
            self.mask = mask
            for i, node in enumerate(self.bt):
                if isinstance(node, ParameterizedNode) and mask[i] == True:
                    self.fix_node(node)
        else:
            self.mask = []

    def fix_node(self, node, threshold=None, value=None):
        """ Fixes the values of a specific node """
        if node.parameters is not None:
            if threshold is not None:
                node.parameters[-1].value = threshold
            for _, parameter in node.parameters.items():
                if value is not None and parameter.value in ['', 0.0]:
                    parameter.value = value
                parameter.min = parameter.value
                parameter.max = parameter.value
                if parameter.list_of_values != [] and parameter.value not in ['', 0.0]:
                    parameter.list_of_values = [parameter.value]

    def optimize_parameters(self,
                            param_nodes: List[ParameterizedNode],
                            func,  # : Callable[[list(ParameterizedNode)], float]
                            folder: str = None,  # Folder for the experiment
                            iterations: int = None,  # Number of iterations
                            add_priors: bool = False,  # Add priors to the parameters
                            exp_name: str = "",  # Name of the experiment
                            random_forest: bool = False,  # Use random forest instead of gaussian process
                            batch_size: int = 1,  # Batch size for the optimization
                            new_parameter_defaults: bool = False  # If we have new defaults to test, set to True
    ):
        """ Optimizes the parameters of the nodes using hypermapper """
        optimizer = HypermapperOptimization(
            func=func,
            param_nodes=param_nodes,
            folder=folder,
            iterations=iterations,
            add_priors=add_priors,
            exp_name=exp_name,
            random_forest=random_forest,
            batch_size=batch_size,
            new_parameter_defaults=new_parameter_defaults,
            extra_settings=self.extra_settings)
        if optimizer.valid:
            optimizer.optimize()
            return True
        else:
            if self.fitness == []:
                self.callback() # Optimizer not valid and we have no fitness yet, just run the callback function to get a fitness score
                return True
        return False # We did nothing

    def call_optimizer(self, bt, log_folder, iterations, add_priors=False):
        """ Call the optimization algorithm """
        if self.random_search:
            self.run_random_step_search(bt, iterations)
            return True
        else:
            return self.optimize_parameters(self.get_parameterized_nodes(bt),
                                            self.callback,
                                            log_folder,
                                            iterations=iterations,
                                            add_priors=add_priors,
                                            random_forest=self.random_forest,
                                            batch_size=self.batch_size,
                                            new_parameter_defaults=self.new_parameter_defaults)

    def run_optimization(self):
        """ Runs the actual optimization """
        if not self.cascaded:
            self.call_optimizer(self.bt, self.log_folder, self.iterations, add_priors=False)
        else:
            n = 1
            if self.hotstart:
                new_subtree = False
            else:
                new_subtree = True
            is_full_tree = False
            iterations = 0
            while not is_full_tree:
                self.best_fitness_updated = False
                bt = BT(self.bt, self.behavior_lists)
                if new_subtree:
                    self.best_fitness = -9999999999
                    iterations = 50

                self.current_bt, is_full_tree = bt.get_nth_subtree(n)

                if is_full_tree:
                    iterations = self.iterations
                    log_folder = self.log_folder
                else:
                    iterations += 50
                    log_folder = self.log_folder+"/subtree_"+str(n)
                    if new_subtree:
                        logplot.make_directory(log_folder)

                if n > 1:
                    self.call_optimizer(self.current_bt, log_folder, iterations, add_priors=True)
                else:
                    self.call_optimizer(self.current_bt, log_folder, iterations, add_priors=False)

                if not self.best_fitness_updated:
                    self.bt = fast_copy(self.best_bt)
                    if not is_full_tree:
                        # Use new values as priors in next subtree
                        bt = BT(self.bt, self.behavior_lists)
                        subtree, _ = bt.get_nth_subtree(n)
                        for node in subtree:
                            if isinstance(node, ParameterizedNode) and node.parameters is not None:
                                for _, parameter in node.parameters.items():
                                    # parameter.min = parameter.value
                                    # parameter.max = parameter.value
                                    parameter.use_prior = True
                    n += 1
                    new_subtree = True
                else:
                    new_subtree = False  # Not solved yet, redo subtree again

        self.plot()
        print("Best tree: \n" + str(self.best_bt))

    def step_optimization(self):
        """ Steps the actual optimization just one step, currently not implemented for cascaded """
        step_taken = self.call_optimizer(self.bt, self.log_folder, self.current_iteration, add_priors=False)
        if step_taken:
            self.current_iteration += self.batch_size
        self.new_parameter_defaults = False

    def run_parameters(self, parameters, seed=100, save_video=True, video_logdir="filmtest"):
        """ Run once with given set of parameters, save video and print fitness """
        parameter_index = 0
        for node in self.current_bt:
            if isinstance(node, ParameterizedNode) and node.parameters is not None:
                for _, parameter in node.parameters.items():
                    if parameter.min != parameter.max:
                        if isinstance(parameter.value, float):
                            parameter.value = round(parameters[parameter_index], 8)
                            parameter_index += 1
                        elif isinstance(parameter.value, tuple):
                            rounded_value = []
                            for _ in range(len(parameter.value)):
                                rounded_value.append(round(parameters[parameter_index], 8))
                                parameter_index += 1
                            parameter.value = tuple(rounded_value)

        fitness, net_fitness, steps, success = self.environment.get_fitness(self.current_bt, seed, save_video, video_logdir)

        print("Fitness:", fitness)
        print("Net fitness:", net_fitness)
        print("Steps:", steps)
        print("Success:", success)

    @staticmethod
    def get_parameterized_nodes(bt):
        """ Returns a list of only the parameterized nodes in the BT """
        parameterized_nodes = []
        for node in bt:
            if isinstance(node, ParameterizedNode):
                parameterized_nodes.append(node)
        return parameterized_nodes

    def callback(self):
        """
        Function for bo to callback to in order to get fitness
        Will also log the data
        """
        parameter_values = []
        for node in self.current_bt:
            if isinstance(node, ParameterizedNode) and node.parameters is not None:
                for _, parameter in node.parameters.items():
                    if isinstance(parameter.value, float):
                        parameter.value = round(parameter.value, 2)
                    elif isinstance(parameter.value, tuple):
                        rounded_value = []
                        for value in parameter.value:
                            rounded_value.append(round(value, 2))
                        parameter.value = tuple(rounded_value)
                parameters = node.get_parameters()
                if parameters is not None:
                    parameter_values += parameters

        cumulative_steps = 0
        fitnesses = []
        net_fitnesses = []
        true_fitnesses = []
        true_successes = []
        n_successes = 0
        for i in range(self.runs_per_bt):
            true_success = 0
            if self.environment.use_parallel_agents():
                fitness, net_fitness, true_fitness, true_success, success, steps = \
                    self.environment.get_fitnesses([self.current_bt], None, [0], 1)[0][0]
            else:
                fitness, net_fitness, true_fitness, success, steps = self.environment.get_fitness(self.current_bt, 100+i)
            fitnesses.append(fitness)
            net_fitnesses.append(net_fitness)
            true_fitnesses.append(true_fitness)
            true_successes.append(true_success)
            cumulative_steps += steps

            n_fitnesses = len(fitnesses)
            fitness_estimate = mean(fitnesses)
            margin = self.best_fitness - fitness_estimate
            std = np.std(fitnesses)
            if success is True or success > 0: #Handle multiple variants
                n_successes += 1

            df = pandas.DataFrame(data={"fitness": fitness,
                                        "mean fitness": fitness_estimate,
                                        "net_fitness": net_fitness,
                                        "true_fitness": true_fitness,
                                        "true_success": true_success,
                                        "margin": margin,
                                        "std": std,
                                        "steps": steps,
                                        "success": success,
                                        "n_successes": n_successes,
                                        "seed": str(i),
                                        "bt": str(logplot.strip_linebreaks(self.current_bt))},
                                  index=[0])
            df.to_csv(self.csv_file_name,
                      mode='a',
                      sep=';',
                      index=False,
                      header=not os.path.exists(self.csv_file_name))

            if n_fitnesses >= 3 and self.best_fitness > fitness_estimate:
                #z = 1.28155 # Corresponds to 80% confidence
                #z = 1.43953 # Corresponds to 85% confidence
                #z = 1.64485 # Corresponds to 90% confidence
                z = 1.95996 # Corresponds to 95% confidence
                #z = 2.57583 # Corresponds to 99% confidence
                if z ** 2 * std ** 2 < margin ** 2 * n_fitnesses:
                    break

        fitness = mean(fitnesses)
        net_fitness = mean(net_fitnesses)
        true_fitness = mean(true_fitnesses)
        true_success_mean = mean(true_successes)

        self.parameter_values.append(parameter_values)
        self.fitness.append(fitness)
        self.net_fitness.append(net_fitness)
        self.steps.append(cumulative_steps)
        self.time.append(time.time())
        if len(self.cumulative_steps) > 0:
            self.cumulative_steps.append(self.cumulative_steps[-1] + cumulative_steps)
        else:
            self.cumulative_steps.append(cumulative_steps)

        if fitness > self.best_fitness:
            self.best_fitness = fitness
            self.best_net_fitness = net_fitness
            self.true_fitness.append(true_fitness)
            self.true_successes.append(true_success_mean)
            self.best_fitness_updated = True
            self.best_bt = fast_copy(self.bt)
            self.best_current_bt = fast_copy(self.current_bt)
            if self.validation_runs > 0:
                validation_fitness, n_successes = self.run_validation()
            else:
                validation_fitness = fitness
            self.validation_fitness.append(validation_fitness)
            self.n_validation_successes.append(n_successes)
        else:
            self.validation_fitness.append(self.validation_fitness[-1])
            self.true_fitness.append(self.true_fitness[-1])
            self.true_successes.append(self.true_successes[-1])
            self.n_validation_successes.append(self.n_validation_successes[-1])
        self.log_data()

        print(fitness, net_fitness, cumulative_steps)

        return fitness

    def run_validation(self):
        """ Runs the current tree on new seeds for validation and plotting """
        net_fitnesses = []
        n_successes = 0
        if self.validation_runs > 0:
            for i in range(self.validation_runs):
                _, net_fitness, _, success = self.environment.get_fitness(self.current_bt, 1337+i)

                net_fitnesses.append(net_fitness)
                if success:
                    n_successes += 1
        else:
            return 0.0, 0.0

        return mean(net_fitnesses), n_successes

    def run_random_step_search(self, bt, iterations):
        """
        Random step search:
        Adds gaussian noise to all parameters
        If new tree not is better than best tree, revert to best tree again
        Repeat
        """
        n_parameters = 0
        for node in bt:
            if isinstance(node, ParameterizedNode) and node.parameters is not None:
                for _, parameter in node.parameters.items():
                    if isinstance(parameter.step, float):
                        parameter.step = 0.0000001
                        n_parameters += 1
                    elif isinstance(parameter.step, tuple):
                        parameter.step = (0.0000001, 0.0000001, 0.0000001)
                        n_parameters += 3
        if iterations is None:
            iterations = 20 * n_parameters

        for _ in range(iterations):
            # Need to save random state and reload because seed is fixed in callback
            randomstate = random.getstate()
            np_randomstate = np.random.get_state()
            fitness = self.callback()
            random.setstate(randomstate)
            np.random.set_state(np_randomstate)
            if fitness < self.best_fitness:
                # Reset
                for i, node in enumerate(bt):
                    if isinstance(node, ParameterizedNode) and node.parameters is not None:
                        for name, _ in node.parameters.items():
                            node.parameters[name].value = self.best_current_bt[i].parameters[name].value

            for node in bt:
                if isinstance(node, ParameterizedNode):
                    node.randomize_parameters()

    def log_data(self):
        """ Save the log data for later retrieval """
        with logplot.open_file(self.log_folder + '/bo_data.pickle', 'wb') as f:
            pickle.dump((self.parameter_values, self.fitness, self.net_fitness, self.true_fitness, self.true_successes,
                         self.validation_fitness, self.n_validation_successes,
                         self.steps, self.cumulative_steps, self.best_fitness, self.best_net_fitness,
                         self.best_bt, self.time), f)

    @staticmethod
    def load_data(log_name):
        """ Load saved data for using for plotting, hotstart etc """
        with logplot.open_file(logplot.get_log_folder(log_name) + '/bo_data.pickle', 'rb') as f:
            data = pickle.load(f)
        return data

    @staticmethod
    def get_bo_data(logs):
        """ Retrieve logged bo data """
        fitness = []
        steps = []
        n_successes = []
        time_logs = []
        for log_name in logs:
            data = BoHandler.load_data(log_name)
            fitness.append(data[4])
            steps.append(data[7])
            n_successes.append(data[5])
            time_logs.append(data[12])
            print(log_name + " fitness: " + str(data[4][-1]) + ", time: " + str(int(((data[12][-1] - data[12][0]) / 60.0))) + " minutes")

        return fitness, n_successes, steps, time_logs

    def get_best_individual(self):
        """ Returns the best bt, it's score and number of successes """
        return self.best_bt, self.best_fitness, self.best_net_fitness, self.true_fitness[-1], \
                self.true_successes[-1], self.n_validation_successes[-1]

    def plot(self):
        """ Plots the run"""
        plotpars = logplot.PlotParameters()
        plotpars.xlabel = 'Steps'
        plotpars.ylabel = 'Fitness'
        plotpars.x_step = 10
        plotpars.plot_horizontal = False
        plotpars.path = self.log_folder + '/fitness.pdf'

        fitness_logs, n_successes_logs, n_steps_logs, _ = BoHandler.get_bo_data([self.log_name])

        logplot.plot_learning_curves([], plotpars, n_steps_logs, fitness_logs)

        # Success rate plot
        plotpars.y_scale = 5.0
        plotpars.ylabel = 'Success rate (%)'
        plotpars.path = self.log_folder + '/success_rate.pdf'
        logplot.plot_learning_curves([], plotpars, n_steps_logs, n_successes_logs)
