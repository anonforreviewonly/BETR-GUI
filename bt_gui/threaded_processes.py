"""Classes for containing threaded processes."""

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
import os
import debugpy


from PyQt5 import QtCore


class SimulationWorker(QtCore.QThread):
    """Worker thread for running processes without blocking the GUI."""
    update_signal = QtCore.pyqtSignal(tuple)  # Signal to send updates to the GUI

    def __init__(self, interface: Any) -> None:
        super().__init__()
        self.interface = interface

        self.running = False  # Control flag for stopping

    def run(self) -> None:
        """Run the processes in a loop without blocking the GUI."""
        if os.environ.get('TERM_PROGRAM', None) == 'vscode':
            try:
                debugpy.debug_this_thread()
            except ConnectionRefusedError:
                print("Debugging available only when running the app in debug mode.")
        self.running = True
        while self.running:
            result = self.interface.run_iterative_process()
            if result is not None:
                self.update_signal.emit(result)  # Send data to GUI

    def stop(self) -> None:
        """Stop simulation."""
        self.running = False
