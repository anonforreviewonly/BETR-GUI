import os
import py_trees as pt
from typing import List

from behaviors.behavior_lists import BehaviorLists
from behaviors.common_behaviors import Behavior, NodeParameter, ParameterizedNode
from py_trees.common import Status

behavior_name_mime_type = "behavior/name-data"
behavior_ai_mime_type = "behavior/name-ai"


class DummyAction(Behavior):
    def __init__(self, name, parameters, world_interface, _verbose=False) -> None:
        self.parameters = parameters
        super().__init__(name, parameters, world_interface)

    def __eq__(self, other) -> bool:
        if not isinstance(other, DummyAction):
            # don't attempt to compare against unrelated types
            return False
        return super().__eq__(other)

    @staticmethod
    def to_string(parameters) -> str:
        """Creates a string"""
        node_string = parameters["target_object"]
        node_string += "!"
        return node_string

    def get_parameters(self) -> dict:
        return self.parameters

    def update(self) -> Status.SUCCESS:
        return Status.SUCCESS


class DummyCondition(Behavior):
    def __init__(self, name, parameters, world_interface, _verbose=False) -> None:
        self.parameters = parameters
        super().__init__(name, parameters, world_interface)

    def __eq__(self, other) -> bool:
        if not isinstance(other, DummyCondition):
            # don't attempt to compare against unrelated types
            return False
        return super().__eq__(other)

    @staticmethod
    def to_string(parameters) -> str:
        """Creates a string"""
        node_string = parameters["target_object"]
        node_string += "?"
        return node_string

    def get_parameters(self) -> dict:
        return self.parameters

    def update(self) -> Status.FAILURE:
        return Status.FAILURE


fallback = pt.composites.Selector("Fallback", memory=False)
sequence = pt.composites.Sequence("Sequence", memory=False)
pick_cube = ParameterizedNode(
    name="pick cube!",
    behavior=DummyAction,
    parameters={"target_object": NodeParameter(['"cube"'])},
    condition=False,
)
cube_picked = ParameterizedNode(
    name="cube picked?",
    behavior=DummyCondition,
    parameters={"target_object": NodeParameter(['"cube"'])},
    condition=True,
)
moveto_table = ParameterizedNode(
    name="moveTo table!",
    behavior=DummyAction,
    parameters={"target_object": NodeParameter(['"table"'])},
    condition=False,
)
atpos_table = ParameterizedNode(
    name="atPos table?",
    behavior=DummyCondition,
    parameters={"target_object": NodeParameter(['"table"'])},
    condition=True,
)

behavior_list = [sequence, fallback, pick_cube, cube_picked, moveto_table, atpos_table]


def get_behavior_list() -> BehaviorLists:
    """Return the behavior list."""
    condition_nodes = [cube_picked, atpos_table]
    action_nodes = [pick_cube, moveto_table]

    fallback_nodes = [sequence]
    sequence_nodes = [fallback]

    root_nodes = fallback_nodes + sequence_nodes

    behavior_list = BehaviorLists(
        fallback_nodes=fallback_nodes,
        sequence_nodes=sequence_nodes,
        condition_nodes=condition_nodes,
        action_nodes=action_nodes,
        root_nodes=root_nodes,
    )

    return behavior_list


def get_behavior_from_name(name: str) -> tuple[ParameterizedNode, bool]:
    if name == "Fallback" or name == "f(":
        return fallback, True
    elif name == "Sequence" or name == "s(":
        return sequence, True
    elif name == "pick cube!":
        return pick_cube, False
    elif name == "cube picked?":
        return cube_picked, False
    elif name == "moveTo table!":
        return moveto_table, False
    elif name == "atPos table?":
        return atpos_table, False
    else:
        return None, False


def create_from_list(
    node_list: List[str], node: pt.composites.Composite
) -> pt.composites.Composite:
    """Recursive function to generate the tree from a list."""
    while len(node_list) > 0:
        if node_list[0] == ")":
            node_list.pop(0)
            return node

        newnode, has_children = get_behavior_from_name(node_list[0])
        node_list.pop(0)
        if has_children:
            # Node is a control node or decorator with children.
            # Add subtree via string and then add to parent
            newnode = create_from_list(node_list, newnode)
            node.add_child(newnode)
        else:
            # Node is a leaf/action node - add to parent, then keep looking for siblings
            node.add_child(newnode.behavior(newnode.name, newnode.parameters, None))

    # This return is only reached if there are too few up nodes
    return node


def build_bt(tree: List[str], name: str = None) -> pt.trees.BehaviourTree:
    """Build a dummy BT from its string representation."""
    # Target directory
    dir_path = os.path.abspath(os.path.dirname(__file__))
    figures_path = os.path.join(dir_path, "test_figures")

    root, _ = get_behavior_from_name(tree[0])
    root.remove_all_children()
    tree.pop(0)
    root = create_from_list(tree, root)

    bt = pt.trees.BehaviourTree(root)

    if name is not None:
        pt.display.render_dot_tree(
            bt.root,
            name=name,
            target_directory=figures_path,
        )

    return bt
