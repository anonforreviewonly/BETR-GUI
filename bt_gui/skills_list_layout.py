import py_trees as pt
from PyQt5 import QtCore, QtGui, QtWidgets
from typing import Any


class SkillWidgetItem(QtWidgets.QWidget):
    def __init__(self, icon_path: str, text, parent=None) -> None:
        super().__init__(parent)

        # Create the layout for the custom item
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Add the figure (icon)
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setPixmap(
            QtGui.QPixmap(icon_path).scaled(40, 40, QtCore.Qt.KeepAspectRatio)
        )
        layout.addWidget(self.icon_label)

        # Add the text label
        self.text_label = QtWidgets.QLabel(text)
        layout.addWidget(self.text_label)

        # # Add a horizontal spacer to push the checkbox to the right
        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        layout.addSpacerItem(spacer)

        # # Add the checkbox
        # self.checkbox = QtWidgets.QCheckBox()
        # self.checkbox.setChecked(True)
        # layout.addWidget(self.checkbox)

        # Set the layout
        self.setLayout(layout)


class SkillLibrary(QtWidgets.QListWidget):
    def __init__(self, backend: Any, parent=None) -> None:
        super().__init__(parent)

        self.backend = backend

        # Create the QListWidget
        self.setMinimumSize(100, 400)
        # Allow items in the list to be draggable
        self.setDragEnabled(True)

    def get_widget(self) -> QtWidgets.QListWidget:
        return self

    def add_items(self, items: Any, goal_definition: bool) -> None:
        """ Group items by type"""
        action_nodes = []
        condition_nodes = []
        control_nodes = []

        for item in items:
            if isinstance(item, str):
                item = self.backend.get_control_node(item)

            if hasattr(item, "condition") and item.condition:
                condition_nodes.append(item)
            elif isinstance(item, pt.composites.Composite):
                control_nodes.append(item)
            else:
                action_nodes.append(item)

        # Add grouped items to the list
        self._add_group("Control Nodes", control_nodes)
        if not goal_definition:
            self._add_group("Action Nodes", action_nodes)
        self._add_group("Condition Nodes", condition_nodes)

    def _add_group(self, group_name: str, items: list) -> None:
        # Add a header item for the group
        header_item = QtWidgets.QListWidgetItem(group_name)
        header_item.setFlags(
            header_item.flags() & ~QtCore.Qt.ItemIsSelectable & ~QtCore.Qt.ItemIsDragEnabled
        )
        # Set the font to italic
        font = header_item.font()
        font.setItalic(True)
        header_item.setFont(font)
        self.addItem(header_item)

        # Add the items in the group
        for item in items:
            # Determine the suffix
            if hasattr(item, "condition") and item.condition:
                suffix = "?"
            elif isinstance(item, pt.composites.Composite):
                suffix = ""
            else:
                suffix = "!"

            # Create the custom widget with the suffix in the name
            custom_item = SkillWidgetItem(self._icon_path_from_behavior(item), item.name + suffix)
            if hasattr(item, "get_tooltip"):
                custom_item.setToolTip(item.get_tooltip())
            list_item = QtWidgets.QListWidgetItem(self)
            list_item.setSizeHint(custom_item.sizeHint())
            self.setItemWidget(list_item, custom_item)

        # Add spacing after the last item in the group
        spacer_item = QtWidgets.QListWidgetItem(self)
        spacer_item.setSizeHint(QtCore.QSize(0, 10))  # Adjust height for spacing
        spacer_item.setFlags(
            spacer_item.flags() & ~QtCore.Qt.ItemIsSelectable & ~QtCore.Qt.ItemIsDragEnabled
        )
        self.addItem(spacer_item)

    def add_labels_layout(self) -> QtWidgets.QHBoxLayout:
        """Create a layout with labels for the skill library."""
        font = QtGui.QFont()
        font.setPointSize(8)
        skill_label_layout = QtWidgets.QHBoxLayout()
        skill_label = QtWidgets.QLabel("Skill Library", font=font)
        skill_label_layout.addWidget(skill_label)

        return skill_label_layout

    def startDrag(self, supportedActions) -> None:
        # Get the selected item from the list
        widget = self.itemWidget(self.currentItem())

        # Create a QDrag object for the drag operation
        drag = QtGui.QDrag(self)
        mime_data = QtCore.QMimeData()

        # Add the item label to the MIME data
        mime_data.setData(self.backend.behavior_name_mime_type, widget.text_label.text().encode())
        drag.setMimeData(mime_data)

        # Add the item AI-enabled to the MIME data
        # mime_data.setData(
        #     self.backend.behavior_ai_mime_type, str(widget.checkbox.isChecked()).encode()
        # )
        drag.setMimeData(mime_data)

        # Get the item icon
        pixmap = widget.icon_label.pixmap()
        # Scale the icon for the drag
        scaled_pixmap = pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio)
        # Set the icon to show during the drag
        drag.setPixmap(scaled_pixmap)
        # Set the drag hot spot at the center of the icon
        drag.setHotSpot(pixmap.rect().center())

        # Execute the drag operation
        drag.exec_(QtCore.Qt.MoveAction)

    def _icon_path_from_behavior(self, behavior: Any) -> str:
        import os

        # Add the parent directory manually
        dir_path = os.path.abspath(os.path.dirname(__file__))

        if type(behavior) is pt.composites.Selector:
            icon_path = os.path.join(dir_path, "icons/node_fallback.svg")
        elif type(behavior) is pt.composites.Sequence:
            icon_path = os.path.join(dir_path, "icons/node_sequence.svg")
        else:
            icon_path = os.path.join(dir_path, "icons/node_action.svg")

        return icon_path


class SkillLayout(QtWidgets.QVBoxLayout):
    def __init__(
        self, backend: Any, parent=None, goal_definition: bool = False, test: bool = False
    ) -> None:
        super().__init__(parent)

        self.sizeConstraint()

        self.library = SkillLibrary(backend)
        if backend:
            behavior_list = backend.get_behavior_list()
        elif test:
            import bt_gui.test_behavior_list as bt_lib

            behavior_list = bt_lib.get_behavior_list()
        else:
            print("ERROR: No backend provided for SkillLayout")
            return

        if goal_definition:
            items = behavior_list.condition_nodes + behavior_list.sequence_nodes
        else:
            items = behavior_list.leaf_nodes + behavior_list.control_nodes
        self.library.add_items(items, goal_definition)

        self.addLayout(self.library.add_labels_layout())
        # Add the list widget to the main layout
        self.addWidget(self.library.get_widget())


class TestWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Behavior Tree Editor")
        self.resize(1490, 800)

        self.centralwidget = QtWidgets.QWidget(self)

        # Skill Layout: where the robot skills are listed
        SkillLayout(self.centralwidget, test=True)

        self.setCentralWidget(self.centralwidget)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    test_window = TestWindow()
    test_window.show()
    test_window.raise_()
    sys.exit(app.exec_())
