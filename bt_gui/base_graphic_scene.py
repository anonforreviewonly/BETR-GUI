"""Scene for showing behavior tree graph"""

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
import math
from typing import Any
import numpy as np
from PyQt5 import QtWidgets

from bt_gui.bt_editor_elements import Edge, Node


class BaseScene(QtWidgets.QGraphicsScene):
    """ Base scene for showing BT graph."""
    def __init__(self, backend: Any, parent=None, scene_update_callback=None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.scene_update_callback = scene_update_callback

    def get_nodes(self) -> list[Node]:
        """Get all nodes in the scene."""
        node_list = []
        for item in self.items():
            if isinstance(item, Node):
                node_list.append(item)
        return node_list

    def clear_scene(self):
        """ Delete all items in scene"""
        for item in self.items():
            if isinstance(item, Node):
                self.removeItem(item)
            elif isinstance(item, Edge):
                self.removeItem(item)

    def load_bt(self, string_tree: list[str], min_length=1) -> list[Node]:
        """Load the Behavior Tree to the editor."""
        try:
            node_list = self.backend.bt_to_qt(string_tree)
        except Exception as e:
            # If we can't load, also don't clear or update
            print("Error loading Behavior Tree: {}".format(e))
            return []
        if len(node_list) < min_length:
            return []
        x_offset = 400.0
        old_max_x = 300.0 - x_offset
        old_root_y = -300.0
        if len(self.items()) >= 1:
            for item in self.items():
                if isinstance(item, Node):
                    old_root = item.get_root_node()
                    if old_root is not None:
                        _, old_root_y = old_root.get_center()
                    break

            #find old_max_x
            for item in self.items():
                if isinstance(item, Node):
                    x, _ = item.get_center()
                    if x > old_max_x:
                        old_max_x = x
        x_tracker = 0.0 # Track the x position of the nodes since this determines the order of the nodes
        for i, node in enumerate(node_list):
            self.addItem(node)
            if i == 0:
                node.move_to(old_max_x + x_offset, old_root_y) # Position of the root node
            else:
                node.move_to(x_tracker, 0)  # Set the x position of the node
            x_tracker += 0.1 # Increment the x position for the next node
            for child in node.children:
                # Connect parent to child
                edge = Edge(node.bottom_connection, child.top_connection)
                self.addItem(edge)
                edge.update_line()  # Ensure line is finalized
                node.edges.append(edge)
                child.edges.append(edge)

        self.arrange_nodes_tree_structure(node_list[0], no_update_callback=True, force_auto_arrange=True)
        return node_list

    def arrange_nodes_tree_structure(self, node: Node, no_update_callback=False, force_auto_arrange=False) -> None:
        """
        Automatically arrange nodes in a tree layout.
        Do widest layer first.
        """
        if not self.backend.auto_arrange_tree and not force_auto_arrange:
            return
        if node is None:
            for item in self.items():
                if isinstance(item, Node):
                    node = item
                    break
        if node is None:
            return
        node_spacing = 10
        level_spacing = 100
        layer_widths = []

        def get_layer_widths(node: Node, depth: int) -> None:
            """
            Recursively get the width of each layer in the tree.
            This function also sorts the children of each node based on their x-coordinates.
            """
            if depth >= len(layer_widths):
                layer_widths.append(0)
            layer_widths[depth] += node_spacing + node.node_item.boundingRect().width()
            if node.children:
                # Sort children based on their current x-coordinates
                node.children.sort(key=lambda child: child.get_center()[0])

                for child in node.children:
                    get_layer_widths(child, depth + 1)

        try:
            # Start recursively from root
            while node.parent is not None:
                node = node.parent
        except AttributeError:
            pass

        depth = 0
        get_layer_widths(node, depth)
        for i, _ in enumerate(layer_widths):
            layer_widths[i] -= node_spacing  # Remove the last node spacing

        widest_depth = np.argmax(np.array(layer_widths))
        root_x, root_y = node.get_center()

        def get_widest_layer(node, depth, widest_layer):
            """ Recursively get a list of all nodes in the widest layer """
            if depth == widest_depth:
                widest_layer.append(node)
            else:
                for child in node.children:
                    get_widest_layer(child, depth + 1, widest_layer)

        def get_left_center_distance(nodes):
            """ Get the distance from the left edge of the nodes to the center """
            distance = 0
            n_nodes= len(nodes)
            if n_nodes % 2 == 0:
                l_c_idx = int(n_nodes / 2 - 1) # Get index of the left center node
                for node in nodes[:l_c_idx + 1]:
                    distance += node.node_item.boundingRect().width() + node_spacing
                distance -= node_spacing / 2  # Remove half the last node spacing
            else:
                mid_node = math.floor(n_nodes / 2)
                for node in nodes[:mid_node]:
                    distance += node.node_item.boundingRect().width() + node_spacing
                distance += nodes[mid_node].node_item.boundingRect().width() / 2
            return distance

        widest_layer = []
        get_widest_layer(node, 0, widest_layer)
        left_center_distance = get_left_center_distance(widest_layer)
        x_offsets = [root_x - left_center_distance] * len(layer_widths)

        # Set the positions of all the nodes in the widest layer
        for wide_node in widest_layer:
            node_width = wide_node.node_item.boundingRect().width()
            wide_node.move_to(x_offsets[widest_depth] + node_width / 2, root_y + level_spacing * widest_depth)
            x_offsets[widest_depth] += node_width + node_spacing

        def set_lower_layers(node, target_depth: int, depth: int) -> None:
            """ Set the positions of the nodes in the lower layers"""
            if depth == target_depth - 1:
                if node.children:
                    left_center_distance = get_left_center_distance(node.children)

                    x_offset = node.get_center()[0] - left_center_distance
                    if x_offset > x_offsets[target_depth]:
                        x_offsets[target_depth] = x_offset
                    for child in node.children:
                        # Set the position of the child node
                        child_width = child.node_item.boundingRect().width()
                        child.move_to(
                            x_offsets[target_depth] + child_width / 2,
                            root_y + level_spacing * target_depth)
                        x_offsets[target_depth] += child_width + node_spacing
            else:
                for child in node.children:
                    set_lower_layers(child, target_depth, depth + 1)

        # Set the lower layers
        if widest_depth < len(layer_widths) - 1:
            for i in range(widest_depth + 1, len(layer_widths)):
                set_lower_layers(node, i, 0)

        def get_average_child_x(node):
            """ 
            Returns the x of the center child, 
            or average of two center-most children if there is an even number of children
            """
            if node.children:
                n_children = len(node.children)
                if n_children % 2 == 0:
                    l_c_idx = int(n_children / 2 - 1) # Get index of the left center child
                    l_c_child = node.children[l_c_idx]
                    l_c_x = l_c_child.get_center()[0]
                    l_c_width = l_c_child.node_item.boundingRect().width()
                    r_c_child = node.children[l_c_idx + 1]
                    r_c_x = r_c_child.get_center()[0]
                    r_c_width = r_c_child.node_item.boundingRect().width()
                    average_child_x = (l_c_x + l_c_width / 2 + r_c_x - r_c_width / 2) / 2
                else:
                    mid_child = math.floor(n_children / 2)
                    average_child_x = node.children[mid_child].get_center()[0]
                return average_child_x
            else:
                return 0.0

        def set_upper_layers(node, target_depth: int, depth: int) -> None:
            """ Set the positions of the nodes in the upper layers """
            if depth == target_depth:
                # Set the position of the node
                node_width = node.node_item.boundingRect().width()
                if node.children:
                    average_child_x = get_average_child_x(node)

                    wanted_x = average_child_x - node_width / 2
                    if wanted_x > x_offsets[target_depth]:
                        x_offsets[target_depth] = wanted_x

                node.move_to(x_offsets[target_depth] + node_width / 2, root_y + level_spacing * target_depth)
                x_offsets[target_depth] += node_width + node_spacing
            else:
                for child in node.children:
                    set_upper_layers(child, target_depth, depth + 1)

                # Loop backwards to see if some children can be moved right after setting siblings
                for i in range(len(node.children) - 2, -1, -1):
                    child = node.children[i]
                    if not child.children: #Only move childless nodes
                        left_sibling = None
                        if i > 0:
                            left_sibling = node.children[i - 1]
                            if not left_sibling.children: #Left sibling not position locked, don't use
                                left_sibling = None
                        right_sibling = node.children[i + 1]
                        child_width = child.node_item.boundingRect().width()
                        right_sibling_width = right_sibling.node_item.boundingRect().width()
                        right_x, right_y = right_sibling.get_center()
                        if left_sibling:
                            left_sibling_width = left_sibling.node_item.boundingRect().width()
                            left_x = left_sibling.get_center()[0]
                            center = (left_x + right_x) / 2
                            center = min(center, left_x + left_sibling_width / 2 + node_spacing + child_width / 2)
                            center = max(center, right_x - right_sibling_width / 2 - node_spacing - child_width / 2)
                            child.move_to(center, right_y)
                        else:
                            child.move_to(right_x - right_sibling_width / 2 - node_spacing - child_width / 2, right_y)


        # Set the upper layers
        if widest_depth > 0:
            for i in range(widest_depth - 1, 0, -1):
                set_upper_layers(node, i, 0)

        # Update edge positions
        self.update_edges()

        if not no_update_callback and self.scene_update_callback is not None:
            self.scene_update_callback()

    def update_edges(self) -> None:
        """Update all edge positions after nodes move."""
        for item in self.items():
            if isinstance(item, Edge):
                item.update_line()
