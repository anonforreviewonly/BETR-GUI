"""First info screen."""

# Copyright (c) 2025, ABB
# All rights reserved.
#
# Redistribution and use in source and binary forms, with
# or without modification, are permitted provided that
# the following conditions are met:
#
#   * Redistributions of source code must retain thea
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
import os
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg


class InfoWindow(QtWidgets.QWidget):
    """Info window class."""
    def __init__(self, scenario) -> None:
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        goal_view = GoalView(scenario)
        self.layout.addWidget(goal_view)

        # self.set_goal_image()
        self.play_video_button = QtWidgets.QPushButton("Watch instruction video")
        self.play_video_button.setMinimumHeight(150)
        self.play_video_button.clicked.connect(self.open_vlc_player)
        self.play_video_button.setFont(QtGui.QFont("Helvetica", 32))

        self.layout.addWidget(self.play_video_button)
        self.setLayout(self.layout)

    def set_goal_image(self) -> None:
        """Display the goal state."""
        self.layout.addWidget(QtWidgets.QLabel("\n\n"))

        img = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_figures/demo_goal.svg")
        image_widget = QtWidgets.QLabel()
        image_widget.setAlignment(QtCore.Qt.AlignCenter)
        pixmap = QtGui.QPixmap(img)
        pixmap = pixmap.scaledToWidth(self.frameGeometry().width())
        image_widget.setPixmap(pixmap)
        self.layout.addWidget(image_widget)

    def open_vlc_player(self):
        """Open VLC player to show video."""
        video_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_figures/instructions.mp4")
        subprocess.Popen(["C:/Program Files/VideoLAN/VLC/vlc.exe", video_path])

class GoalView(QtWidgets.QGraphicsView):
    """
    Graphics view to desired goal state from an svg image.
    """
    def __init__(self, scenario) -> None:
        super().__init__()

        # Create a scene
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)

        self.renderer = QtSvg.QSvgRenderer()

        # Create an SVG item and add it to the scene
        self.svg_item = QtSvg.QGraphicsSvgItem()

        self.scene.addItem(self.svg_item)

        if scenario == "spheres":
            svg_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_figures/demo_goal.svg")
        elif scenario == "cubebowl":
            svg_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_figures/cubebowl_goal.svg")
        elif scenario == "trashpicking":
            svg_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_figures/trashpicking_goal.svg")
        elif scenario == "tableware":
            svg_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_figures/tableware_goal.svg")
        else:
            print("ERROR: Unknown scenario " + scenario)
            raise ValueError("Unknown scenario " + scenario)
        self.renderer.load(svg_path)  # Update the renderer
        self.svg_item.setSharedRenderer(self.renderer)

        self.setAcceptDrops(False)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = InfoWindow("spheres")
    main_window.show()
    main_window.raise_()

    sys.exit(app.exec_())
