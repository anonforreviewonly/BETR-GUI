""" Contains the class for defining the popup hint labels."""
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
import time
from PyQt5 import QtGui, QtWidgets

class PopupHint(QtWidgets.QLabel):
    """Widget for popup hint labels."""
    def __init__(self, parent, text, position, size) -> None: #pylint: disable=redefined-outer-name
        super().__init__(text, parent=parent)
        self.setFixedSize(size[0], size[1])
        self.setWordWrap(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.setFont(font)
        self.setMargin(5)
        self.move(position[0], position[1])
        # Make label have solid background and border
        self.setStyleSheet("background-color: lightyellow; border: 1px solid black;")
        self.enter_time = time.time()
        self.show_time = 0
        self.timeline = None
        self.hide()

    def enterEvent(self, event): # pylint: disable=unused-argument, invalid-name
        """Save time when mouse enters. If it has been more than 10 seconds since shown, hide directly"""
        self.enter_time = time.time()
        if self.enter_time > self.show_time + 10:
            self.hide()

    def leaveEvent(self, event): # pylint: disable=unused-argument, invalid-name
        """Hide the label when mouse leaves if it was there for more than half a second."""
        leave_time = time.time()
        if leave_time - self.enter_time > 0.5:
            self.hide()

    def showEvent(self, event): # pylint: disable=unused-argument, invalid-name
        """Save time when shown."""
        self.show_time = time.time()
        if self.timeline is not None:
            self.timeline.start()

    def mousePressEvent(self, event): # pylint: disable=unused-argument, invalid-name
        """Hide the label when clicked."""
        self.hide()

    def set_anim_number(self, num: int) -> None:
        """Set the number of dots in the animation based on the frame number."""
        if num % 2 == 0:
            self.setStyleSheet("background-color: lightyellow; border: 3px solid green;")
        else:
            self.setStyleSheet("background-color: lightyellow; border: 1px solid black;")
