"""Elements for behavior tree graph"""

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
from typing import Any

from PyQt5 import QtCore, QtGui, QtWidgets


class Edge(QtWidgets.QGraphicsLineItem):
    """Class representing an edge in the behavior tree graph."""
    def __init__(self, start_point, end_point=None) -> None:
        super().__init__()
        self.start_point = start_point
        self.end_point = end_point
        self.setPen(QtGui.QPen(QtCore.Qt.black, 2))  # Line style
        self.setZValue(-1)  # Draw behind other elements
        self.update_line()

    def get_root_node(self):
        """Get the root node of the tree this edge belongs to."""
        if self.start_point and self.start_point.parent_node:
            return self.start_point.parent_node.get_root_node()
        return None

    def update_line(self) -> None:
        """Update the edge's geometry to stay connected to the start and end points."""
        if self.scene():  # Ensure the edge is in a scene
            if self.start_point and self.end_point:
                # Update the line to connect start and end points
                self.setLine(
                    self.start_point.scenePos().x(),
                    self.start_point.scenePos().y(),
                    self.end_point.scenePos().x(),
                    self.end_point.scenePos().y(),
                )
            elif self.start_point:
                # If there's no end point, keep the line anchored to the start point
                self.setLine(
                    self.start_point.scenePos().x(),
                    self.start_point.scenePos().y(),
                    self.line().p2().x(),
                    self.line().p2().y(),
                )

    def set_selected(self) -> None:
        """Set the edge as selected."""
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setSelected(True)
        self.setPen(QtGui.QPen(QtCore.Qt.blue, 2))

    def toggle_selected(self) -> None:
        """Toggle the selection state of the edge."""
        if self.isSelected():
            self.set_movable()
        else:
            self.set_selected()

    def set_movable(self) -> None:
        """Set the edge as movable."""
        self.setSelected(False)
        self.setPen(QtGui.QPen(QtCore.Qt.black, 2))

    def paint(self, painter, option, widget):
        """Override paint to ensure no selection box is drawn."""
        option.state &= ~QtWidgets.QStyle.State_Selected
        super().paint(painter, option, widget)

    def set_locked(self, locked: bool = True) -> None:
        """ Just a dummy function to match Node interface """
        pass

class ConnectionPoint(QtWidgets.QGraphicsEllipseItem):
    """Class representing a connection point for edges in the behavior tree graph."""
    def __init__(self, parent_node) -> None:
        super().__init__(-6, -7, 12, 12)  # Small circle for the connection point
        self.setBrush(QtGui.QBrush(QtGui.QColor("gray")))  # gray fill
        self.setPen(QtGui.QPen(QtCore.Qt.black))  # Black outline
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)  # Non-movable
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)  # Non-selectable
        self.parent_node = parent_node  # Reference to the parent node

    def resize(self, width: float, height: float) -> None:
        """Resize the connection point."""
        self.setRect(-width / 2, -height / 2, width, height)
        self.setPos(-2, -2)

    def mousePressEvent(self, event) -> None: #pylint: disable=unused-argument, invalid-name
        """Start creating a new edge when this connection point is clicked."""
        self.parent_node.scene().start_edge(self)

    def mouseReleaseEvent(self, event) -> None: #pylint: disable=unused-argument, invalid-name
        """Try to connect the edge to another connection point on release."""
        self.parent_node.scene().finish_edge(self)

    def paint(self, painter, option, widget):
        """Override paint to ensure no selection box is drawn."""
        option.state &= ~QtWidgets.QStyle.State_Selected
        super().paint(painter, option, widget)


class Node(QtWidgets.QGraphicsItemGroup):
    """Class representing a node in the behavior tree graph."""
    def __init__(
        self,
        node_item: QtWidgets.QGraphicsItem,
        name: str,
        n_points: int,
        scalable: bool,
    ) -> None:
        super().__init__()

        self.node_item = node_item

        # Style the node
        self.node_item.setPen(QtGui.QPen(QtCore.Qt.black, 2))
        self.addToGroup(self.node_item)

        # Add label
        self.scalable = scalable
        self.set_label(name)

        # Add connection points
        self.connection_points = []
        self.top_connection = ConnectionPoint(self)
        self.connection_points.append(self.top_connection)

        self.bottom_connection = None
        if n_points == 2:
            self.bottom_connection = ConnectionPoint(self)
            self.connection_points.append(self.bottom_connection)

        self._position_connection_points(n_points)
        for point in self.connection_points:
            self.addToGroup(point)

        # Make the node movable
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)

        # Store node connectivity information
        self.edges = []  # Store edges connected to this node
        self.parent = None
        self.children = []
        self.locked = False  # Indicates if the node is locked

    def clone(self, node_item, x_offset: float = 0.0, y_offset: float = 0.0) -> "Node":
        """Create a copy of this node. Doesn't copy parent reference or locked status."""
        cloned_node = Node(
            node_item=node_item,
            name=self.label.toPlainText(),
            n_points=len(self.connection_points),
            scalable=self.scalable,
        )
        cloned_node.move_to(self.x() + x_offset, self.y() + y_offset)
        cloned_node.children = self.children[:]
        return cloned_node

    def paint(self, painter, option, widget):
        """Override paint to ensure no selection box is drawn."""
        option.state &= ~QtWidgets.QStyle.State_Selected
        super().paint(painter, option, widget)

    def set_label(self, text: str) -> None:
        """Updates the node label, removing the old one first."""
        if hasattr(self, "label") and self.label:  # Check if label exists #pylint: disable=access-member-before-definition
            self.scene().removeItem(self.label)  # Remove old label from scene #pylint: disable=access-member-before-definition

        # Create and set the new label
        self.label = QtWidgets.QGraphicsTextItem(text)
        self.label.setParentItem(self.node_item)
        self.label.setDefaultTextColor(QtCore.Qt.black)
        option = self.label.document().defaultTextOption()
        option.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter) #pylint: disable=no-member
        self.label.document().setDefaultTextOption(option)

        # Dynamically reshape the shape
        self._adjust_node_to_label(self.scalable)
        self.label.setTextWidth(self.label.boundingRect().width())

    def set_selected(self) -> None:
        """Set the node as selected."""
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setSelected(True)
        self.node_item.setPen(QtGui.QPen(QtCore.Qt.blue, 2))

    def toggle_selected(self) -> None:
        """Toggle the selection state of the node."""
        if self.isSelected():
            self.set_movable()
        else:
            self.set_selected()

    def set_movable(self) -> None:
        """Set the node as movable."""
        self.setSelected(False)
        color = QtCore.Qt.darkGreen if self.locked else QtCore.Qt.black
        self.node_item.setPen(QtGui.QPen(color, 2))

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)

    def move_to(self, x: float, y: float) -> None:
        """Move the node to a specific position."""
        old_x, old_y = self.get_center()
        offset_x = x - old_x
        offset_y = y - old_y
        # This is done because the setPos method depends on the shape of the node
        self.moveBy(offset_x, offset_y)

    def set_locked(self, locked: bool = True) -> None:
        color = QtCore.Qt.darkGreen if locked else QtCore.Qt.black
        self.node_item.setPen(QtGui.QPen(color, 2))
        self.locked = locked

    def set_parent(self, parent: QtWidgets.QGraphicsItemGroup = None) -> None:
        self.parent = parent

    def add_child(self, child: QtWidgets.QGraphicsItemGroup) -> None:
        self.children.append(child)

    def remove_child(self, child: QtWidgets.QGraphicsItemGroup) -> None:
        self.children.remove(child)

    def is_root_node(self) -> bool:
        return self.parent is None and self.children

    def is_leaf_node(self) -> bool:
        return self.parent is not None and not self.children

    def get_root_node(self) -> "Node":
        if self.is_root_node():
            return self
        elif self.parent is None:
            return None
        else:
            return self.parent.get_root_node()

    def get_subtree_recursive(self) -> list["Node"]:
        node_list = [self]
        if self.children:
            for child in self.children:
                node_list += child.get_subtree_recursive()

        return node_list

    def get_center(self) -> tuple[float, float]:
        node_rect = self.node_item.boundingRect()
        center = self.node_item.mapToScene(node_rect.center())
        return center.x(), center.y()

    def to_string(self) -> str:
        return self.label.toPlainText()

    def itemChange(self, change, value) -> Any:
        """Update edges when the node moves."""
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            for edge in self.edges:
                edge.update_line()
        return super().itemChange(change, value)

    def _adjust_node_to_label(self, scalable: bool) -> None:
        label_rect = self.label.boundingRect()
        node_rect = self.node_item.boundingRect()
        if scalable:
            padding = 20  # Add some padding around the text
            self.node_item.setRect(
                -label_rect.width() / 2 - padding / 2,
                -label_rect.height() / 2 - padding / 2,
                label_rect.width() + padding,
                label_rect.height() + padding,
            )

        self.label.setPos(
            node_rect.center().x() - label_rect.width() / 2,
            node_rect.center().y() - label_rect.height() / 2,
        )

    def _position_connection_points(self, n_points: int) -> None:
        """Position the connection points around the node."""
        rect = self.node_item.boundingRect()
        offsets = [
            (rect.center().x(), rect.top() + 3.5),  # Top
            (rect.center().x(), rect.bottom()),  # Bottom)
        ]
        for point, (x, y) in zip(self.connection_points, offsets[:n_points]):
            point.setPos(x, y)
