"""Behavior tree editor scene."""

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
from copy import copy
from functools import partial
import math
import os
from typing import Any
from PyQt5 import QtCore, QtGui, QtWidgets

from bt_gui.base_graphic_scene import BaseScene
from bt_gui.bt_editor_elements import ConnectionPoint, Edge, Node


class NodeInfoDialog(QtWidgets.QDialog):
    """Dialog to show and edit node parameters."""
    def __init__(self, node: Node, backend, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Node Parameters")
        self.setModal(True)  # Block other interactions
        self.backend = backend
        self.node = node
        self.param_inputs = {}  # Store input widgets
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        layout = QtWidgets.QFormLayout(self)

        # Node Name (read-only)
        name_label = QtWidgets.QLabel(node.label.toPlainText())
        layout.addRow("Name:", name_label)

        # Retrieve node parameters
        parameters = backend.qt_node_to_parameters(node)
        self.param_ranges = {}

        if parameters:
            for key, value in parameters.items():
                widget, add_text = self.backend.create_node_param_widget(value)
                self.param_ranges[key] = [value.min, value.max]

                if isinstance(widget, tuple):
                    sub_layout = QtWidgets.QHBoxLayout()
                    for i, sub_widget in enumerate(widget):
                        if isinstance(sub_widget, QtWidgets.QDoubleSpinBox):
                            sub_widget.valueChanged.connect(
                                partial(self.validate_spinbox_value, sub_widget, key, i)
                            )
                        sub_layout.addWidget(sub_widget)
                    layout.addRow(f"{key}{add_text}:", sub_layout)
                    self.param_inputs[key] = widget
                else:
                    if isinstance(widget, QtWidgets.QDoubleSpinBox):
                        widget.valueChanged.connect(
                            partial(self.validate_spinbox_value, widget, key, None)
                        )
                    layout.addRow(f"{key}{add_text}:", widget)
                    self.param_inputs[key] = widget  # Store input widget reference
        else:
            layout.addRow(QtWidgets.QLabel("This control node has no parameters."))

        # Load custom icons
        self.dir_path = os.path.abspath(os.path.dirname(__file__))
        self.icons_path = os.path.join(self.dir_path, "icons")

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.setIcon(QtGui.QIcon(os.path.join(self.icons_path, "disk--plus.png")))
        save_btn.clicked.connect(self.save_changes)
        btn_layout.addWidget(save_btn)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setIcon(QtGui.QIcon(os.path.join(self.icons_path, "cross.png")))
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addRow(btn_layout)

    def validate_spinbox_value(
        self, spinbox: QtWidgets.QDoubleSpinBox, key: str, index: int = None
    ) -> None:
        """Checks if the spinbox value is within range and displays a warning if not."""
        min_val = self.param_ranges[key][0] if index is None else self.param_ranges[key][0][index]
        max_val = self.param_ranges[key][1] if index is None else self.param_ranges[key][1][index]
        current_val = round(spinbox.value(), 2)

        if not min_val <= current_val <= max_val:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                f"Value must be between {min_val} and {max_val}.\n"
                f"Current input: {current_val}",
                QtWidgets.QMessageBox.Ok,
            )
            spinbox.setValue(min_val if current_val < min_val else max_val)  # Reset to limit

    def save_changes(self) -> None:
        """Saves updated parameters back to the node."""
        new_params = {}
        for key, widget in self.param_inputs.items():
            if isinstance(widget, QtWidgets.QCheckBox):
                new_params[key] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                new_params[key] = round(widget.value(), 2)
            elif isinstance(widget, tuple):
                new_params[key] = tuple(round(w.value(), 2) for w in widget)
            elif isinstance(widget, QtWidgets.QComboBox):
                new_params[key] = widget.currentText()
            elif isinstance(widget, QtWidgets.QLineEdit):
                new_params[key] = widget.text()

        self.backend.update_node_parameters(self.node, new_params)  # Update backend
        self.accept()
        self.backend.log_event(f"Node parameters updated: {self.node.label.toPlainText()}")


class BTEditorScene(BaseScene):
    """Behavior Tree Editor Scene."""
    def __init__(self, backend: Any, parent=None, scene_update_callback=None, save_bt_callback=None) -> None:
        super().__init__(backend, parent, scene_update_callback)
        self.save_bt_callback = save_bt_callback
        # settings
        self.gridSize = 20 #pylint: disable=invalid-name
        self.gridSquares = 5 #pylint: disable=invalid-name
        self._color_background = QtGui.QColor("#A0A0A0")
        self._color_light = QtGui.QColor("#5F5F5F")
        self._color_dark = QtGui.QColor("#4A4A4A")
        self._pen_light = QtGui.QPen(QtGui.QColor("#B0B0B0"))
        self._pen_light.setWidth(1)
        self._pen_dark = QtGui.QPen(QtGui.QColor("#8A8A8A"))
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_background)

        # Selection rectangle
        self.selection_rect = None  # Graphics item for selection box
        self.origin = QtCore.QPointF()
        self.selecting_mode = False

        self.current_edge = None  # Edge currently being drawn
        self.edge_origin_item = None  # Keep track what is the item the edge originates from
        self.cutting_mode = False  # Flag for cutting edges
        self.highlighted_edges = set()  # Store edges that are highlighted

        self.clipboard_items = []  # Store copied items for pasting
        self.times_pasted = 0 # Count how many times pasted to offset position

        # Load custom icons
        self.dir_path = os.path.abspath(os.path.dirname(__file__))
        self.icons_path = os.path.join(self.dir_path, "icons")

        # Debug
        self.debug = False

    def load_bt_from_LLM(self, input_text: str) -> None: #pylint: disable=invalid-name
        """Load the Behavior Tree from a string tree generated by the LLM."""
        loaded_tree = []
        try:
            string_tree = self.backend.get_behavior_from_LLM(input_text)
        except Exception as e:
            print("Error generating tree from LLM:", e)
        # Check if there is a tree in editor already, if so ask to clear
        if string_tree:
            if self.is_empty() is False:
                reply = QtWidgets.QMessageBox.question(
                    self.parent(),
                    "Clear existing tree?",
                    "There is a behavior tree in the editor already. Do you want to it cleared before loading?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    self.clear_scene()
            loaded_tree = self.load_bt(string_tree, min_length=2)
        if not loaded_tree:
            QtWidgets.QMessageBox.warning(
                self.parent(),
                "No behavior tree",
                "The LLM could not generate a valid behavior tree from the provided input.\n"
                "Please check the input and try again.",
            )

    def is_empty(self) -> bool:
        """Check if the scene is empty."""
        for node in self.items():
            # Ignore all items that are not Nodes
            if isinstance(node, Node):
                return False
        return True

    def build_bt(self) -> tuple[Any, list[bool], list[Node]]:
        """Build the Behavior Tree."""
        # Parse the items to store only Node items
        node_list = []
        for node in self.items():
            # Ignore all items that are not Nodes
            if not isinstance(node, Node):
                continue

            node_list.append(node)

        # Identify the BT by searching for a root node
        root = None
        # Keep a list of other disconnected BTs whose root are below the main root in the editor
        # In this way the BT with the highest root in the editor is the only valid one
        other_nodes = []
        for node in node_list:
            if node.is_root_node():
                # This might be a root node
                try:
                    if root.get_center()[1] > node.get_center()[1]:
                        other_nodes += root.get_subtree_recursive()
                        root = node
                    else:
                        other_nodes += node.get_subtree_recursive()
                except AttributeError:
                    # root is still None, so assign the node as new root
                    root = node
            elif len(node_list) == 1:
                # If there's only one node, it must be the root
                root = node
            # Insert in other nodes to be removed also disconnected nodes
            elif not node.parent and not node.children:
                other_nodes.append(node)
        if node_list:
            tree, mask = self.backend.qt_root_to_behavior_tree(root)
        else:
            QtWidgets.QMessageBox.warning(
                None,
                "No behavior tree",
                "The behavior tree is empty or missing. This operation requires a valid behavior tree.\n",
            )
            return None, [], []

        return tree, mask, other_nodes

    def save_bt(self):
        """ Save the Behavior Tree to a string tree."""
        if self.save_bt_callback:
            self.save_bt_callback()

    def delete_unused_nodes(self, unused_nodes: list[Node]) -> None:
        """ Delete the nodes connected to the detached BT """
        for node in unused_nodes:
            if node.children:
                for _, child in enumerate(copy(node.children)):
                    if child in unused_nodes:
                        unused_nodes.remove(child)
                    self._delete_node(child)

            self._delete_node(node)

    def delete_subtree(self, subtree_root: Node) -> None:
        """Delete the subtree starting from the given root node."""
        if subtree_root is None:
            return
        try:
            # Recursively delete all children
            for child in copy(subtree_root.children):
                self.delete_subtree(child)

            # Delete the root node itself
            self._delete_node(subtree_root)
        except ValueError:
            print("Warning: Could not delete item, it might be already removed.")

    def drawBackground(self, painter, rect) -> None: #pylint: disable=invalid-name
        """Draw the background grid."""
        super().drawBackground(painter, rect)

        # Create the grid
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))
        first_left = left - (left % self.gridSize)
        first_top = top - (top % self.gridSize)

        lines_light, lines_dark = [], []
        for x in range(first_left, right, self.gridSize):
            if x % (self.gridSize * self.gridSquares) != 0:
                lines_light.append(QtCore.QLineF(x, top, x, bottom))
            else:
                lines_dark.append(QtCore.QLineF(x, top, x, bottom))

        for y in range(first_top, bottom, self.gridSize):
            if y % (self.gridSize * self.gridSquares) != 0:
                lines_light.append(QtCore.QLineF(left, y, right, y))
            else:
                lines_dark.append(QtCore.QLineF(left, y, right, y))

        # Draw the grid
        painter.setPen(self._pen_light)
        painter.drawLines(lines_light)

        painter.setPen(self._pen_dark)
        painter.drawLines(lines_dark)

    def keyPressEvent(self, event) -> None: #pylint: disable=invalid-name
        """Handles DEL key to delete selected items."""
        if event.key() == QtCore.Qt.Key_Delete:
            selected_items = self.selectedItems()
            if selected_items:
                root = selected_items[0].get_root_node()
                for item in selected_items:
                    if isinstance(item, Node):
                        self._delete_node(item)
                for item in selected_items:
                    if isinstance(item, Edge):
                        self._delete_edge(item)
                if root not in selected_items:
                    self.arrange_nodes_tree_structure(root)
                self.backend.log_event("Delete selected nodes with DEL key")
        elif event.key() == QtCore.Qt.Key_Escape:
            self.selecting_mode = False
            for node_item in self.items():
                if isinstance(node_item, Node) or isinstance(node_item, Edge):
                    node_item.set_movable()
        elif event.key() == QtCore.Qt.Key_C and event.modifiers() & QtCore.Qt.ControlModifier:
            self.clipboard_items = self.selectedItems()
            self.times_pasted = 0
            self.backend.log_event("Copied nodes to clipboard")
        elif event.key() == QtCore.Qt.Key_V and event.modifiers() & QtCore.Qt.ControlModifier:
            self.backend.log_event("Pasting nodes from clipboard")
            self.times_pasted += 1
            self.paste_nodes()
        elif event.key() == QtCore.Qt.Key_A and event.modifiers() & QtCore.Qt.ControlModifier:
            for item in self.items():
                if isinstance(item, Node) or isinstance(item, Edge):
                    item.set_selected()
        elif event.key() == QtCore.Qt.Key_Z and event.modifiers() & QtCore.Qt.ControlModifier:
            # Not implemented, throw a warning popup
            text = "Undo functionality is not implemented. No regrets!\nSave your tree to not lose your work."
            QtWidgets.QMessageBox.warning(self.parent(), "Warning", text, QtWidgets.QMessageBox.Ok)
        elif event.key() == QtCore.Qt.Key_S and event.modifiers() & QtCore.Qt.ControlModifier:
            self.backend.log_event("Saving behavior tree with Ctrl+S")
            self.save_bt()

        # Pass the event to the base class (to avoid blocking other key events)
        super().keyPressEvent(event)

    def paste_nodes(self) -> None:
        """Paste nodes from clipboard."""
        items_to_paste = []
        clipboard_indices = []
        for index, item in enumerate(self.clipboard_items):
            try:
                if isinstance(item, Node):
                    node_item = self.backend.copy_py_tree_node_item(item.node_item)
                    items_to_paste.append(item.clone(node_item, x_offset=100.0*self.times_pasted, y_offset=50.0*self.times_pasted))
                    clipboard_indices.append(index)
            except Exception as e:
                print("Error copying item for paste:", e)
        if len(items_to_paste) < 1:
            return

        for item in items_to_paste:
            try:
                self.addItem(item)

                for i, child in reversed(list(enumerate(item.children))):
                    # Connect parent to children if they are also being pasted
                    if child in self.clipboard_items:
                        child_clipboard_index = self.clipboard_items.index(child)
                        if child_clipboard_index in clipboard_indices:
                            child = items_to_paste[clipboard_indices.index(child_clipboard_index)]
                            item.children[i] = child
                            child.set_parent(item)
                            edge = Edge(item.bottom_connection, child.top_connection)
                            self.addItem(edge)
                            edge.update_line()  # Ensure line is finalized
                            item.edges.append(edge)
                            child.edges.append(edge)
                            continue
                        else:
                            print("Warning: Child node not found in clipboard indices during paste.")
                    item.children.remove(child) # Remove child if not being pasted
            except Exception as e:
                print("Error pasting item:", e)


    def mouseDoubleClickEvent(self, event) -> None: #pylint: disable=invalid-name
        """Show node information on double-click."""
        item = self.itemAt(event.scenePos(), QtGui.QTransform())

        # Find Node item
        while item and not isinstance(item, Node):
            item = item.parentItem()

        if isinstance(item, Node):
            self._show_node_info(item)
            self.arrange_nodes_tree_structure(item.get_root_node())
        else:
            super().mouseDoubleClickEvent(event)  # Pass event to default handler

    def mousePressEvent(self, event) -> None: #pylint: disable=invalid-name
        """Mouse click actions."""
        item = self.itemAt(event.scenePos(), QtGui.QTransform())
        # Clear selection if not Ctrl is not pressed and not item in selection
        if event.button() == QtCore.Qt.LeftButton and not (
            event.modifiers() & QtCore.Qt.ControlModifier
        ):
            item_in_selected = False
            # Find Node item
            parent_item = item
            while parent_item and not isinstance(parent_item, Node):
                parent_item = parent_item.parentItem()
            if isinstance(parent_item, Node):  # Check if clicked on a node
                if parent_item in self.selectedItems():
                    item_in_selected = True
            if not item_in_selected:
                self.clearSelection()  # Clear selection on mouse press
                for selectable_item in self.items():
                    if isinstance(selectable_item, Node) or isinstance(selectable_item, Edge):
                        selectable_item.set_movable()

        if event.button() == QtCore.Qt.RightButton:
            # Find Node item
            while item and not isinstance(item, Node):
                item = item.parentItem()
            if isinstance(item, Node):  # Check if clicked on a node
                selected_items = self.selectedItems()
                n_selected_nodes = 0
                all_selected_locked = True  # Assume all nodes are locked initially
                all_selected_unlocked = True  # Assume all nodes are unlocked initially
                for selected_item in selected_items:
                    if isinstance(selected_item, Node):
                        n_selected_nodes += 1
                        all_selected_locked = all_selected_locked and selected_item.locked
                        all_selected_unlocked = all_selected_unlocked and not selected_item.locked
                        if not all_selected_locked and not all_selected_unlocked:
                            break
                    elif not isinstance(selected_item, Edge):
                        selected_items.remove(selected_item)  # Remove non-Node/Edge items

                menu = QtWidgets.QMenu()
                delete_action = menu.addAction("Delete Node")
                delete_all_action = -1
                if len(selected_items) > 1:
                    delete_all_action = menu.addAction("Delete All Selected Items")

                parameters_action = -1
                if self.backend.qt_node_to_parameters(item):
                    parameters_action = menu.addAction("Change Node Parameters")

                set_locked = True
                if item.locked:
                    lock_action = menu.addAction("Unlock Node")
                    set_locked = False
                else:
                    lock_action = menu.addAction("Lock Node")
                lock_all = -1
                unlock_all = -1
                if n_selected_nodes > 1:
                    if not all_selected_locked:
                        lock_all = menu.addAction("Lock All Selected Nodes")
                    if not all_selected_unlocked:
                        unlock_all = menu.addAction("Unlock All Selected Nodes")

                action = menu.exec_(event.screenPos())  # Show menu at mouse position
                if action == delete_action:
                    root = item.get_root_node()
                    self._delete_node(item)
                    if root != item:
                        self.arrange_nodes_tree_structure(root)
                    self.backend.log_event("Delete node")
                elif action == delete_all_action:
                    root = item.get_root_node()
                    for selected_item in selected_items:
                        if isinstance(selected_item, Node):
                            self._delete_node(selected_item)
                    for selected_item in selected_items:
                        if isinstance(selected_item, Edge):
                            self._delete_edge(selected_item)
                    if root not in selected_items:
                        self.arrange_nodes_tree_structure(root)
                    self.backend.log_event("Delete all items")
                elif action == parameters_action:
                    self._show_node_info(item)
                    self.arrange_nodes_tree_structure(item.get_root_node())
                elif action == lock_action:
                    item.set_locked(set_locked)
                    self.backend.log_event("Set locked node: " + str(set_locked))
                elif action == lock_all:
                    for item in selected_items:
                        item.set_locked(True)
                    self.backend.log_event("Lock selected nodes")
                elif action == unlock_all:
                    for item in selected_items:
                        item.set_locked(False)
                    self.backend.log_event("Unlock selected nodes")
        elif event.button() == QtCore.Qt.LeftButton:
            if item is not None and not isinstance(item, ConnectionPoint):
                while item and not isinstance(item, Node):
                    item = item.parentItem()

            if item is None and not self.selecting_mode:
                self.origin = event.scenePos()  # Store start position in scene coordinates
                self.selection_rect = QtWidgets.QGraphicsRectItem()
                self.selection_rect.setBrush(
                    QtGui.QColor(100, 100, 255, 50)
                )  # Semi-transparent blue
                self.selection_rect.setPen(
                    QtGui.QPen(QtGui.QColor(0, 0, 255), 1, QtCore.Qt.DashLine)
                )
                self.addItem(self.selection_rect)  # Add to scene
                self.selecting_mode = True
            elif isinstance(item, ConnectionPoint):
                # Start drawing a new edge
                self.current_edge = Edge(item)  # Pass the connection point as the start
                self.edge_origin_item = item.parentItem()
                self.addItem(self.current_edge)
            elif (
                item
                and event.button() == QtCore.Qt.LeftButton
            ):
                # Find Node item
                while item and not isinstance(item, Node):
                    item = item.parentItem()
                if isinstance(item, Node):
                    if event.modifiers() & QtCore.Qt.ControlModifier:
                        item.toggle_selected()
                    else:
                        item.set_selected()
                        super().mousePressEvent(event)

            else:
                # Pass the event to the parent item for dragging
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None: #pylint: disable=invalid-name
        """ Mouse move actions."""
        if self.current_edge:
            cursor_pos = event.scenePos()
            self.current_edge.setLine(
                self.current_edge.start_point.scenePos().x(),
                self.current_edge.start_point.scenePos().y(),
                cursor_pos.x(),
                cursor_pos.y(),
            )
        elif self.cutting_mode:
            self._highlight_edges(event.scenePos())  # Highlight edges being crossed
        elif self.selecting_mode:
            if self.selection_rect:
                rect = QtCore.QRectF(self.origin, event.scenePos()).normalized()
                self.selection_rect.setRect(rect)  # Update rectangle dimensions
        else:
            # Allow nodes to be dragged
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None: #pylint: disable=invalid-name
        """ Mouse release actions."""
        if event.button() == QtCore.Qt.MiddleButton and self.cutting_mode:
            self._remove_highlighted_edges()
            self.cutting_mode = False
            QtWidgets.QApplication.restoreOverrideCursor()  # Restore normal cursor
        elif self.current_edge:
            items_under_cursor = self.items(event.scenePos())
            for item in items_under_cursor:
                if isinstance(item, ConnectionPoint) and item != self.current_edge.start_point:
                    # If touching a connection point, then that is the closest point
                    closest_point = item
                    self._draw_edge_if_legal(item.parent_node, closest_point)
                    break
                # This logic allows to connect the edge to a node if you are over the node itself
                elif isinstance(item.parentItem(), Node):
                    # If the origin of the current edge is above the node,
                    # the connection point is the top one
                    if (
                        self.current_edge.start_point.scenePos().y()
                        > item.parentItem().get_center()[1]
                    ):
                        closest_point = item.parentItem().bottom_connection
                    else:
                        closest_point = item.parentItem().top_connection

                    self._draw_edge_if_legal(item.parentItem(), closest_point)
                    break
                else:
                    continue
            else:
                # Remove invalid edge
                self.removeItem(self.current_edge)
                self.current_edge = None
        elif self.selecting_mode:
            rect = self.selection_rect.rect()
            if rect.height() < 2:
                rect.setHeight(2) # Minimum height makes selection easier when drawing horizontally
            for item in self.items(rect):
                if isinstance(item, Node) or isinstance(item, Edge):
                    item.set_selected()  # Mark items as selected
            self.removeItem(self.selection_rect)  # Remove selection rectangle
            self.selection_rect = None  # Reset for next selection
            self.selecting_mode = False
        else:
            # Pass the event to the parent item for dragging
            super().mouseReleaseEvent(event)
            dragged_item = self.itemAt(event.scenePos(), QtGui.QTransform())
            # Ensure we get the parent Node, not just a child item
            while dragged_item and not isinstance(dragged_item, Node):
                dragged_item = dragged_item.parentItem()  # Move up to the group item

            # Automatically arrange nodes into a tree
            if isinstance(dragged_item, Node):
                self.arrange_nodes_tree_structure(dragged_item)

    def dragEnterEvent(self, event) -> None: #pylint: disable=invalid-name
        """ Handle drag-and-drop events."""
        # Get the MIME data from the event
        mime_data = event.mimeData()

        # Accept drag if it contains the expected MIME type
        if mime_data.hasFormat(self.backend.behavior_name_mime_type):
            event.accept()  # Accept the drag action to allow the drop

    def dragMoveEvent(self, event) -> None: #pylint: disable=invalid-name
        """ Handle the drag move event."""
        event.accept()

    def dropEvent(self, event) -> None: #pylint: disable=invalid-name
        """ Handle the drop event """
        mime_data = event.mimeData()
        event.setDropAction(QtCore.Qt.MoveAction)

        if mime_data.hasFormat(self.backend.behavior_name_mime_type):
            # Retrieve the dragged data
            item_name = mime_data.data(self.backend.behavior_name_mime_type).data().decode()
            behavior, _ = self.backend.get_behavior_from_name(item_name)
            qt_node = self.backend.behavior_to_qt(behavior, event.scenePos())
            if qt_node is not None:
                self.addItem(qt_node)

            # You can add the item to the scene, or any other desired behavior
            event.acceptProposedAction()  # Accept the drop action

    def _delete_node(self, node: Node) -> None:
        try:
            for edge in node.edges:
                self.removeItem(edge)
                if node.parent:
                    if edge in node.parent.edges:
                        node.parent.edges.remove(edge)
                for child in node.children:
                    if edge in child.edges:
                        child.edges.remove(edge)
                del edge
            if node.parent:
                node.parent.children.remove(node)
            if node.children:
                for child in node.children:
                    child.parent = None

            self.removeItem(node)
            del node
        except ValueError:
            print("Warning: Could not delete item, it might be already removed.")

    def _delete_edge(self, edge: Edge) -> None:
        try:
            start_point_node = None
            end_point_node = None
            if edge.start_point:
                start_point_node = edge.start_point.parent_node
            if edge.end_point:
                end_point_node = edge.end_point.parent_node
                if start_point_node and end_point_node:
                    if start_point_node.top_connection == edge.start_point:
                        start_point_node.parent = None
                        end_point_node.children.remove(start_point_node)
                    elif end_point_node.top_connection == edge.end_point:
                        end_point_node.parent = None
                        start_point_node.children.remove(end_point_node)
                    if edge in start_point_node.edges:
                        start_point_node.edges.remove(edge)
                    if edge in end_point_node.edges:
                        end_point_node.edges.remove(edge)
            self.removeItem(edge)
            del edge
        except ValueError:
            # Most likely just already removed
            pass

    def _show_node_info(self, node: Node) -> None:
        """Show node info in an editable dialog with dropdown menus."""
        dialog = NodeInfoDialog(node, self.backend)

        node_x, node_y = node.get_center()  # Get the node's position in the scene
        view = self.views()[0]  # Get the first QGraphicsView
        global_pos = view.mapToGlobal(view.mapFromScene(node_x, node_y))

        # Move the message box near the clicked node
        dialog.move(global_pos.x(), global_pos.y())
        dialog.exec_()

    def _draw_edge_if_legal(
        self,
        end_node: QtWidgets.QGraphicsItemGroup,
        closest_point: ConnectionPoint,
    ) -> None:
        """Draw an edge between two nodes if it is allowed."""
        origin_type = type(self.edge_origin_item.node_item)
        end_type = type(end_node.node_item)
        if self.debug:
            print(
                f"Attempting connecting <{self.edge_origin_item.to_string()}> "
                + f"with <{end_node.to_string()}>:"
            )
        # Remove edge in six cases:
        # 1. the connected nodes are of the same type
        case_1 = origin_type is end_type
        if case_1 and self.debug:
            print("\tERROR: the two nodes have the same type!")

        # 2: if the node is a leaf node (ellipse), it cannot have more than 1 edge
        if origin_type is QtWidgets.QGraphicsEllipseItem:
            leaf = self.edge_origin_item
        elif end_type is QtWidgets.QGraphicsEllipseItem:
            leaf = end_node
        else:
            leaf = None
        case_2 = leaf is not None and len(leaf.edges) >= 1
        if case_2 and self.debug:
            print(f"\tERROR: {leaf.to_string()} is a leaf node and it already has an edge!")

        # 3. there already exists an edge between the two nodes
        case_3 = (
            end_node.parent is self.edge_origin_item or self.edge_origin_item in end_node.children
        )
        if case_3 and self.debug:
            print("\tERROR: there already exist an edge between the two nodes!")

        # 4. attempting to connect two TOP connection points or two BOTTOM connection points
        case_4 = (
            self.current_edge.start_point is self.edge_origin_item.top_connection
            and closest_point is end_node.top_connection
        ) or (
            self.current_edge.start_point is not self.edge_origin_item.top_connection
            and closest_point is not end_node.top_connection
        )
        if case_4 and self.debug:
            print("\tERROR: attempting connecting two TOP or two BOTTOM connection points!")

        # 5. attempting to connect a node as a child that already has a parent
        case_5 = (end_node.parent is not None and closest_point is end_node.top_connection) or \
                 (self.edge_origin_item.parent is not None and self.current_edge.start_point is self.edge_origin_item.top_connection)
        if case_5 and self.debug:
            print(
                f"\tERROR: {self.edge_origin_item.to_string()} already has a parent "
                + "and cannot have another one!"
            )

        # 6. Connecting a root node as a child to its own descendant
        case_6 = (self.current_edge.start_point is self.edge_origin_item.top_connection and end_node.get_root_node() is self.edge_origin_item) or \
                  (closest_point is end_node.top_connection and self.edge_origin_item.get_root_node() is end_node)
        if case_6 and self.debug:
            print(
                f"\tERROR: {self.edge_origin_item.to_string()} is a root node and cannot be "
                + "connected as a child to its own descendant!"
            )

        # Remove invalid edge
        if case_1 or case_2 or case_3 or case_4 or case_5 or case_6:
            # Remove the edge if it is there
            try:
                self.current_edge.start_point.parent_node.edges.remove(self.current_edge)
            except ValueError:
                pass
            self.removeItem(self.current_edge)

        else:
            if self.debug:
                print("\tthe connection is valid!")
            self.current_edge.end_point = closest_point
            self.current_edge.update_line()  # Ensure line is finalized
            self.current_edge.start_point.parent_node.edges.append(self.current_edge)
            self.current_edge.end_point.parent_node.edges.append(self.current_edge)

            # Determine parent-child relationship based on top and bottom connection points
            # If the edge is drawn from the top connection point, the parent is the end node
            # Otherwise, the parent is the edge origin item
            if self.current_edge.end_point is end_node.top_connection:
                parent_node = self.edge_origin_item
                child_node = end_node
            else:
                parent_node = end_node
                child_node = self.edge_origin_item

            parent_node.add_child(child_node)
            child_node.set_parent(parent_node)
            if self.debug:
                print(
                    f"Added connection from parent <{child_node.parent.to_string()}>"
                    + f" to child <{parent_node.children[-1].to_string()}>."
                )

            # Automatically arrange nodes into a tree
            self.arrange_nodes_tree_structure(parent_node)

        self.current_edge = None
        self.edge_origin_item = None

    def _highlight_edges(self, cursor_pos: QtCore.QPointF) -> None:
        """Highlight edges when the cursor moves over them in cutting mode."""
        items_under_cursor = self.items(cursor_pos)

        for item in items_under_cursor:
            if isinstance(item, Edge) and item not in self.highlighted_edges:
                item.setPen(QtGui.QPen(QtCore.Qt.red, 2))  # Highlight in red
                self.highlighted_edges.add(item)

    def _remove_highlighted_edges(self) -> None:
        """Delete all highlighted edges."""
        for edge in self.highlighted_edges:
            # Remove parent/child relationship between nodes
            origin_node = edge.start_point.parent_node
            end_node = edge.end_point.parent_node
            if origin_node in end_node.children:
                if self.debug:
                    print(
                        f"Removing edge from parent <{end_node.to_string()}> "
                        + f"to child <{origin_node.to_string()}>"
                    )
                origin_node.parent = None
                end_node.remove_child(origin_node)
                # Automatically arrange nodes into a tree
                self.arrange_nodes_tree_structure(end_node)
            else:
                if self.debug:
                    print(
                        f"Removing edge from parent <{origin_node.to_string()}> "
                        + f"to child <{end_node.to_string()}>"
                    )
                end_node.parent = None
                origin_node.remove_child(end_node)
                # Automatically arrange nodes into a tree
                self.arrange_nodes_tree_structure(origin_node)

            # Remove the edge
            edge.start_point.parent_node.edges.remove(edge)
            edge.end_point.parent_node.edges.remove(edge)
            self.removeItem(edge)
        self.highlighted_edges.clear()


class QBTGraphicsView(QtWidgets.QGraphicsView):
    """Custom QGraphicsView to handle zooming with the mouse wheel."""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:  #pylint: disable=invalid-name
        """Zoom in/out when Ctrl is held, otherwise allow normal scrolling."""
        if event.modifiers() == QtCore.Qt.ControlModifier:  # Check if Ctrl is held
            zoom_factor = 1.2
            min_zoom = 0.1
            max_zoom = 5.0

            current_scale = self.transform().m11()  # Get current zoom level
            if event.angleDelta().y() > 0 and current_scale < max_zoom:  # Zoom in
                self.scale(zoom_factor, zoom_factor)
            elif event.angleDelta().y() < 0 and current_scale > min_zoom:  # Zoom out
                self.scale(1 / zoom_factor, 1 / zoom_factor)

            event.accept()  # Prevent normal scrolling when zooming
        else:
            super().wheelEvent(event)  # Default behavior (scrolling)

    def mousePressEvent(self, event) -> None: #pylint: disable=invalid-name
        """Mouse click actions."""
        if event.button() == QtCore.Qt.MiddleButton:
            # Enable panning mode when middle mouse button is pressed
            # Need to fake pressing left button for the drag to work
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            fake_event = QtGui.QMouseEvent(event.type(), event.localPos(), QtCore.Qt.LeftButton, event.buttons(), event.modifiers())
            super().mousePressEvent(fake_event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None: #pylint: disable=invalid-name
        """ Mouse release actions."""
        if event.button() == QtCore.Qt.MiddleButton:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        super().mouseReleaseEvent(event)

class EditorSceneWindow(QtWidgets.QWidget):
    """Main widget for the Behavior Tree Editor Scene."""
    def __init__(self, backend: Any, parent=None, scene_update_callback=None, save_bt_callback=None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.scene_update_callback = scene_update_callback
        self.save_bt_callback = save_bt_callback

        # Initialize the scene with the backend and callback
        self.grScene = BTEditorScene(backend, self, scene_update_callback=scene_update_callback,
                                     save_bt_callback=save_bt_callback)  #pylint: disable=invalid-name

        # create graphics view
        self.view = QBTGraphicsView(self)
        self.view.setScene(self.grScene)

    def get_widget(self) -> QtWidgets.QWidget:
        """ Return the main widget containing the graphics view."""
        return self.view

    def get_scene(self) -> BTEditorScene:
        """ Return the graphics scene."""
        return self.grScene

    def clear_scene(self) -> None:
        """Completely reload the scene."""
        self.grScene = BTEditorScene(self.backend, self, scene_update_callback=self.scene_update_callback,
                                     save_bt_callback=self.save_bt_callback)  #pylint: disable=invalid-name
        self.view.setScene(self.grScene)

    def get_backend(self) -> Any:
        """ Return the backend associated with the scene."""
        return self.grScene.backend

    def load_bt(self, string_tree: list[str], min_length=1):
        """Load the Behavior Tree from a string tree."""
        self.grScene.load_bt(string_tree, min_length)

    def load_bt_from_LLM(self, input_text: str):  #pylint: disable=invalid-name
        """Load the Behavior Tree from a string tree generated by the LLM."""
        self.grScene.load_bt_from_LLM(input_text)

    def is_empty(self) -> bool:
        """Check if the scene is empty."""
        return self.get_scene().is_empty()

    def get_current_tree(self) -> Any:
        """Get the current behavior tree from the editor without cleaning."""
        return self.get_scene().build_bt()

    def get_and_clean_current_bt(self):
        """ Get current bt and clean up unused nodes """
        try:
            py_tree, mask, unused_nodes = self.get_scene().build_bt()

            if unused_nodes:
                deleted_nodes_text = "Some nodes are unconnected and must be deleted before continuing. "
                deleted_nodes_text += "The following unconnected nodes are about to be automatically deleted:\n"
                for node in unused_nodes:
                    deleted_nodes_text += "    - " + node.to_string().replace("\n", "") + "\n"
                deleted_nodes_text += "Are you sure you want to proceed?"
                confirmation = QtWidgets.QMessageBox.question(
                    self.parentWidget(),
                    "Unconnected nodes",
                    deleted_nodes_text,
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,  # Default selection is "No"
                )
                if confirmation == QtWidgets.QMessageBox.Yes:
                    # QtWidgets.QMessageBox.information(self, "Confirmed", "You clicked Yes!")
                    self.get_scene().delete_unused_nodes(unused_nodes)
                else:
                    # QtWidgets.QMessageBox.warning(self, "Cancelled", "You clicked No.")
                    return None, None
            return py_tree, mask
        except ValueError as e:
            QtWidgets.QMessageBox.warning(
                self.parentWidget(),
                "Invalid Behavior Tree",
                str(e),
            )
            return None, None
