# type: ignore
"""A simple simulation environment for running behavior trees on simulations."""

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

from dataclasses import dataclass
from typing import Any, List
import random
import numpy as np
import py_trees as pt
from behaviors.common_behaviors import ParameterizedNode, Goal
from interfaces.py_trees_interface import PyTree
from scenarios import fitness_function

@dataclass
class EnvParameters:
    """Data class for parameters for the environment."""

    seed: Any = None  # Random seed
    verbose: bool = False  # Extra prints
    py_tree_parameters: Any = None  # Parameters for executing the py tree
    sim_class: Any = None  # Simulation class
    sim_parameters: Any = None  # Parameters specific for the simulation
    goals: Any = None # List of user defined goals
    true_fitness: Any = None  # True fitness function pointer
    true_goals: Any = None  # True goals for the scenario
    fitness_coeff: Any = None  # Coefficients for the fitness function
    calculate_fitness_every_tick: bool = True # Whether to calculate fraction of fitness every tick, (makes fast solutions better)
    parallel_agents: bool = False  # Whether to run multiple agents in parallel in the same simulation environment
    physics_sim: bool = False  # Whether the environment uses physics simulation
    n_agents: int = 1  # Number of agents to run in parallel
    fitness_decimal_places: int = 10  # Number of decimal places to round the fitness to
    extrapolation_ticks: int = 200 # Extrapolate the fitness until this many ticks after the tree has finished
    scenario: str = ""  # Scenario name for the simulation


class Environment:
    """Class defining the environment in which the individual operates."""

    def __init__(self, parameters: Any):
        self.par = parameters
        if self.par.fitness_coeff is None:
            self.par.fitness_coeff = fitness_function.Coefficients()
        self.sim_class = self.par.sim_class
        self.true_fitness = self.par.true_fitness
        self.fitnesses = None
        self.last_fitness = None
        self.individuals_to_eval = None
        self.status_ok = None
        self.references = None
        self.n_population = 0
        self.world_interface = None
        self.pytree = None
        self.sim_handle = None
        self.sim_client = None
        self.agent_indices = list(range(0, self.par.n_agents))
        self.paused = False
        self.randomstate = None
        self.np_randomstate = None

    def __exit__(self, *args, **kwargs):
        self.delete_sim()

    def __del__(self):
        self.delete_sim()

    def delete_sim(self):
        """ Delete the pool """
        if self.sim_handle is not None:
            self.sim_handle.terminate()
            self.sim_handle = None
            self.sim_client = None

    def get_goals(self) -> List[Goal]:
        """Get the goals defined in the environment."""
        if self.par.goals is None:
            return []
        return self.par.goals

    def get_paused(self) -> bool:
        """Get the paused state of the environment."""
        return self.paused

    def set_paused(self, paused: bool):
        """Set the paused state of the environment."""
        if not isinstance(paused, bool):
            raise TypeError("Paused must be a boolean value.")
        self.paused = paused

    def set_goals(self, goals: List[Goal]):
        """Set the goals for the environment."""
        if not isinstance(goals, list):
            raise TypeError("Goals must be a list of Goal objects.")
        self.par.goals = goals

        if len(goals) > 1:
            self.par.py_tree_parameters.behavior_lists.root_nodes = ['s(']
        else:
            self.par.py_tree_parameters.behavior_lists.root_nodes = ['s(', 'f(']

    def set_goals_from_behavior_tree(self, behavior_tree: List):
        """ Set all the goals by looking at the behavior tree and extracting all the conditions"""
        goals = []
        for node in behavior_tree:
            if isinstance(node, ParameterizedNode) and node.condition:
                goals.append(Goal(node.behavior, node.get_parameters()))

        self.set_goals(goals)

    def get_goal_status(self, index):
        """ Check the status of the goals, return 1 if all are satisfied, 0 otherwise """
        if self.par.goals is None:
            return 0.0
        else:
            for goal in self.par.goals:
                if goal.behavior.check_success(goal.parameters, self.world_interface[index]) != pt.common.Status.SUCCESS:
                    return 0.0
            return 1.0

    def get_true_goal_successes(self, index):
        """ 
        Check the number of successes of the true goals, i.e. not the user defined ones.
        Count how many are satisfied and return sum
        """
        sum_goals = 0
        if self.par.true_goals is not None:
            for goal in self.par.true_goals:
                if goal.behavior.check_success(goal.parameters, self.world_interface[index]) == pt.common.Status.SUCCESS:
                    sum_goals += 1
        return sum_goals

    def start_simulation(self, channel=50010, timescale=1, steps_per_tick=10, headless=False, hide_window=True, unity_log_file="unity.log"):
        """Start the simulation and save the handle."""
        self.sim_handle = self.sim_class.start_unity_process(n_agents=self.par.n_agents,
                                                             channel=channel,
                                                             timescale=timescale,
                                                             steps_per_tick=steps_per_tick,
                                                             headless=headless,
                                                             hide_window=hide_window,
                                                             unity_log_file=unity_log_file,
                                                             scenario=self.par.scenario)
        self.sim_client = self.sim_class.get_sim_client(channel)

    def get_screenshot(self, camera_position):
        """Get a screenshot from the simulation."""
        if self.sim_client is not None:
            # Works with "-headless", "-batchmode" but not with "-nographics"
            return self.sim_client.get_screenshot(camera_position)
        return None

    def set_seeds(self, seed):
        """Set the random seeds and saves random state."""
        self.randomstate = random.getstate()
        self.np_randomstate = np.random.get_state()
        random.seed(seed)
        np.random.seed(seed)

    def restore_random_state(self):
        """Restore the random states."""
        if self.randomstate is not None:
            random.setstate(self.randomstate)
        if self.np_randomstate is not None:
            np.random.set_state(self.np_randomstate)

    def reset_world(self,
        population: List[List[ParameterizedNode]],
        individuals_to_eval: List[int],
        object_positions: Any,
        object_yaws: Any = None,
        seed: int = 0,
    ):
        """Reset the world."""
        self.world_interface = []
        self.pytree = []

        if isinstance(object_positions, dict):
            object_positions = self.par.sim_parameters.object_positions | object_positions
        else:
            object_positions = self.par.sim_parameters.object_positions
        if isinstance(object_yaws, dict):
            object_yaws = self.par.sim_parameters.object_yaws | object_yaws
        else:
            object_yaws = self.par.sim_parameters.object_yaws

        if self.use_parallel_agents():
            obs = self.sim_class.custom_reset(self.sim_client, self.agent_indices, object_positions, object_yaws,
                                              self.par.scenario) #Reset the simulation
            for i, observation in enumerate(obs.agents):
                if i < len(individuals_to_eval):
                    self.world_interface.append(self.sim_class(self.par.sim_parameters, seed))
                    self.world_interface[i].set_observation(observation)
                    if len(population) > individuals_to_eval[i]:
                        self.pytree.append(PyTree(
                            population[individuals_to_eval[i]][:],
                            parameters=self.par.py_tree_parameters,
                            world_interface=self.world_interface[i]))
        else:
            for i in range(self.n_population):
                self.world_interface.append(self.sim_class(self.par.sim_parameters, seed))
                self.pytree.append(PyTree(
                    population[individuals_to_eval[i]][:],
                    parameters=self.par.py_tree_parameters,
                    world_interface=self.world_interface[i]))

    def use_parallel_agents(self):
        """ Returns True if environment uses parallel agents """
        return self.par.parallel_agents

    def compute_fitness(self, world_interface, pytree):
        """ Computes and returns fitness """

        # First calculate general fitness
        fitness, net_fitness, n_steps = fitness_function.compute_fitness(world_interface, pytree, self.par.fitness_coeff, self.par.verbose)

        #Calculate ground truth scenario specific fitness
        true_fitness = fitness + self.true_fitness(world_interface, self.par.fitness_coeff)


        #Calculate fitness of user defined goals
        if self.par.goals is not None:
            user_fitness = 0.0
            for goal in self.par.goals:
                # Calculate fitness for each goal that the user defined
                user_fitness += goal.behavior.compute_fitness(goal.parameters, world_interface, self.par.fitness_coeff)
            fitness += user_fitness
            net_fitness += user_fitness

        return (round(fitness, self.par.fitness_decimal_places), net_fitness, true_fitness, n_steps)

    def reset(self, population, fitness_list=None, individuals_to_eval=None, seed=0, object_positions=None, object_yaws=None):
        """ Reset the environment """
        if fitness_list is None:
            self.fitnesses = [None] * len(population)
        else:
            self.fitnesses = fitness_list[:]
        if individuals_to_eval is None:
            self.individuals_to_eval = list(range(len(population)))
        else:
            self.individuals_to_eval = individuals_to_eval
        self.n_population = len(self.individuals_to_eval)
        if self.n_population > self.par.n_agents:
            raise ValueError("Population size is larger than number of agents")
        for i in self.individuals_to_eval:
            self.fitnesses[i] = [0.0, 0.0, 0.0, 0]

        if self.par.calculate_fitness_every_tick:
            self.status_ok = [True] * self.n_population
            self.last_fitness = [[0.0, 0.0, 0.0, 0]] * self.n_population
            self.reset_world(population, self.individuals_to_eval, object_positions, object_yaws, seed)
            self.references = [None] * self.par.n_agents
            for i in range(self.par.n_agents):
                self.references[i] = self.par.sim_class.get_default_reference(self.agent_indices[i])
        else:
            raise NotImplementedError("Not implemented")

    def step(self):
        """ Step the environment one control step,
            returns False if the simulation is done """
        obs = None
        if any(self.status_ok) and not self.paused:
            old_status_ok = self.status_ok[:]
            for i in range(self.n_population):
                if self.status_ok[i]:
                    self.status_ok[i] = self.pytree[i].step_bt()
                    self.references[i] = self.world_interface[i].get_references()
            if self.use_parallel_agents():
                obs = self.par.sim_class.send_parallel_references(self.sim_client, self.references)

                for i, observation in enumerate(obs.agents):
                    if i < self.n_population and old_status_ok[i]: #Only update if the agent was still active
                        self.world_interface[i].set_observation(observation)
                        self.last_fitness[i] = self.compute_fitness(self.world_interface[i], self.pytree[i])
                        self.fitnesses[self.individuals_to_eval[i]] = tuple(map(sum, zip(self.fitnesses[self.individuals_to_eval[i]],
                                                                                        self.last_fitness[i])))
            else:
                for i in range(self.n_population):
                    self.last_fitness[i] = self.compute_fitness(self.world_interface[i], self.pytree[i])
                    self.fitnesses[self.individuals_to_eval[i]] = tuple(map(sum, zip(self.fitnesses[self.individuals_to_eval[i]],
                                                                                    self.last_fitness[i])))
            if any(self.status_ok):
                return True
            else:
                for i in range(self.n_population):
                    if self.pytree[i].ticks < self.par.extrapolation_ticks:
                        # If we have ticks left, calculate as if the last fitness was the same for all remaining ticks
                        ticks_left = self.par.extrapolation_ticks - self.pytree[i].ticks
                        self.last_fitness[i] = list(self.last_fitness[i]) #Make it editable
                        self.last_fitness[i][3] = 0 # Do not count any more steps
                        self.fitnesses[self.individuals_to_eval[i]] = tuple(map(sum, zip(self.fitnesses[self.individuals_to_eval[i]],
                                                                                        [ticks_left*x for x in self.last_fitness[i]])))
        return False


    def compile_fitnesses(self):
        """ Compiles and returns the fitnesses of the individuals """
        try:
            fitnesses = self.fitnesses[:]

            # Need to store whether tree ended up in success state, put it second to last
            for i in range(self.n_population):
                if self.par.goals is not None:
                    success = self.get_goal_status(i)
                else:
                    success = float(self.pytree[i].success)
                true_goal_successes = self.get_true_goal_successes(i)
                fitnesses[self.individuals_to_eval[i]] = fitnesses[self.individuals_to_eval[i]][:-1] + \
                                                        (true_goal_successes,) + \
                                                        (success,) + \
                                                        fitnesses[self.individuals_to_eval[i]][-1:]
            return fitnesses
        except TypeError as exc:
            if self.paused:
                return fitnesses # If the environment is paused, we can safely return the fitnesses as they are not used
            else:
                raise TypeError("Fitnesses are not computed yet") from exc


    def get_fitnesses(self, population, fitness_list, individuals_to_eval, min_episodes):
        """ 
        Runs a simulation and returns the fitness of multiple individuals 
        Note that the seed setting currently doesn't work properly if 
        the simulation uses random numbers from random and numpy
        and there is more than one individual as they will affect each other.
        """
        if fitness_list is None:
            fitnesses = [None] * len(population)
        else:
            fitnesses = fitness_list
        if len(individuals_to_eval) > 0:
            for i in individuals_to_eval:
                fitnesses[i] = [[0.0, 0.0, 0.0, 0]] * min_episodes
            for seed in range(min_episodes):
                self.set_seeds(seed)
                self.reset(population, fitnesses, individuals_to_eval, seed)
                status_ok = True
                while status_ok:
                    status_ok = self.step()
                compiled_fitnesses = self.compile_fitnesses()
                for i in individuals_to_eval:
                    fitnesses[i][seed] = compiled_fitnesses[i]
                self.restore_random_state()

        return fitnesses

    def get_fitness(
        self,
        individual: List,
        seed: int = 0
    ) -> tuple[float, float, float, int]:
        """Run the simulation and return the fitness."""
        if seed is not None:
            self.par.seed = seed
        self.set_seeds(self.par.seed)

        self.world_interface = self.sim_class(
            self.par.sim_parameters, self.par.seed)
        pytree = PyTree(
            individual[:],
            parameters=self.par.py_tree_parameters,
            world_interface=self.world_interface
        )
        if self.par.calculate_fitness_every_tick:
            status_ok = pytree.step_bt()
            fitness = self.compute_fitness(self.world_interface, pytree)
            last_fitness = fitness
            while status_ok:
                status_ok = pytree.step_bt()
                last_fitness = self.compute_fitness(self.world_interface, pytree)
                fitness = tuple(map(sum, zip(fitness, last_fitness)))
            if pytree.ticks < self.par.py_tree_parameters.max_ticks:
                # If we have ticks left, calculate as if the last fitness was the same for all remaining ticks
                ticks_left = self.par.py_tree_parameters.max_ticks - pytree.ticks
                fitness = tuple(map(sum, zip(fitness, [ticks_left*x for x in last_fitness])))

            if self.par.verbose:
                print('Total episode ticks: ', pytree.ticks)
        else:
            # run the Behavior Tree
            pytree.run_bt()
            fitness = self.compute_fitness(self.world_interface, pytree)
        # Need to store whether tree ended up in success state, put it second to last
        fitness = fitness[:-1] + (float(pytree.success),) + fitness[-1:]

        self.restore_random_state()
        return fitness

    def get_last_pytree(self) -> PyTree:
        """Get the last PyTree used in the environment."""
        if isinstance(self.pytree, list) and len(self.pytree) > 0:
            return self.pytree[0]
        return None

    def plot_individual(
        self,
        path: str,
        plot_name: str,
        individual: List[ParameterizedNode]
    ):
        """Save a graphical representation of the individual."""
        if self.world_interface is None or isinstance(self.world_interface, list):
            self.world_interface = self.sim_class(self.par.sim_parameters, self.par.seed)

        pytree = PyTree(individual[:], parameters=self.par.py_tree_parameters, world_interface=self.world_interface)
        pytree.save_fig(path, name=plot_name)
