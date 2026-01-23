""" Display the goal state as a screenshot from the simulation"""
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
from PyQt5 import QtWidgets, QtGui, QtCore

class GoalState(QtWidgets.QGraphicsView):
    """Graphics view to display the goal state as a screenshot from the simulation"""
    def __init__(self, backend: Any, parent=None) -> None:
        super().__init__(parent)

        self.setScene(QtWidgets.QGraphicsScene(self))
        self.pixmap_item = self.scene().addPixmap(QtGui.QPixmap())
        self.setAlignment(QtCore.Qt.AlignCenter)

        # Connect worker signal to update GUI
        backend.set_goal_result_callback(self.update_image)

    def resizeEvent(self, event): #pylint: disable=invalid-name
        """ Make sure the image fits in the view when resized """
        super().resizeEvent(event)
        self.fitInView(self.pixmap_item, QtCore.Qt.KeepAspectRatio)

    @staticmethod
    def pillow_to_qpixmap(pil_image):
        """ Convert a Pillow Image to QPixmap """
        # Convert Pillow Image to RGB if it's not
        if pil_image is None:
            return None

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Crop the image to fit better in the GUI
        width, height = pil_image.size
        pil_image = pil_image.crop((500, 0, width-500, height))

        # Get image data and size
        width, height = pil_image.size
        data = pil_image.tobytes("raw", "RGB")
        # Create QImage from raw dat
        qimage = QtGui.QImage(data, width, height, QtGui.QImage.Format_RGB888)

        return QtGui.QPixmap.fromImage(qimage)

    def update_image(self, goal_image):
        """ Update image in GUI to reflect goal state """
        if goal_image is not None:
            pixmap = self.pillow_to_qpixmap(goal_image)
            self.pixmap_item.setPixmap(pixmap)
