import sys
import time
import subprocess
import win32gui
import win32con
import win32api
import win32process
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QWindow
from PyQt5.QtCore import Qt, QSize

qt_to_vk = {
    Qt.Key_W: ord('W'),
    Qt.Key_S: ord('S'),
    Qt.Key_A: ord('A'),
    Qt.Key_D: ord('D'),
    Qt.Key_Space: win32con.VK_SPACE,
  #  Qt.Key_Escape: win32con.VK_ESCAPE,  # Dont want this, kills the unity window separately
    Qt.Key_Up: win32con.VK_UP,
    Qt.Key_Down: win32con.VK_DOWN,
}

def find_window(title):
    # In linux, this needs to be replaced with something like: Xlib (python-xlib) -> Need to interact with X11 server to get the window handle. Not sure though, have not tested.
    hwnd = win32gui.FindWindow(None, title)
    return hwnd


class UnityEmbedder(QWidget):
    def __init__(self, unity_hwnd, unity_process, parent=None):
        super().__init__(parent)
        self.unity_hwnd = unity_hwnd
        self.unity_process = unity_process

        self.setWindowTitle('Unity Embedded in PyQt')
        self.resize(1024, 768)

        # Wrap Unity window
        self.unity_window = QWindow.fromWinId(unity_hwnd)
        self.unity_window.setFlags(Qt.FramelessWindowHint)

        # Embed Unity window into PyQt
        self.container = self.createWindowContainer(self.unity_window, self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.container)
        layout.setContentsMargins(0, 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = event.size()
        if self.unity_hwnd:
            # Resize Unity window manually
            win32gui.MoveWindow(self.unity_hwnd, 0, 0, size.width(), size.height(), True)

    def closeEvent(self, event):
        super().closeEvent(event)
        if self.unity_process:
            self.unity_process.terminate()
            self.unity_process.wait()
            print("Unity process terminated.")

    def keyPressEvent(self, event):
        key = event.key()
        self.forward_key_to_unity(key, down=True)

    def keyReleaseEvent(self, event):
        key = event.key()
        self.forward_key_to_unity(key, down=False)

    def forward_key_to_unity(self, qt_key, down=True):
        vk_code = qt_to_vk.get(qt_key)

        print(f"{down} : {vk_code}")
        if not vk_code:
            return

        win32gui.SetFocus(self.unity_hwnd)
        if down:
            win32api.PostMessage(self.unity_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
        else:
            win32api.PostMessage(self.unity_hwnd, win32con.WM_KEYUP, vk_code, 0)

def launch_unity_app(path):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = win32con.SW_HIDE  # Hidden start
    process = subprocess.Popen([path], startupinfo=startupinfo)
    return process


def wait_for_unity_window(title, timeout=15):
    hwnd = None
    for _ in range(timeout):
        hwnd = find_window(title)
        if hwnd:
            break
        time.sleep(1)
    return hwnd


def main():
    app = QApplication(sys.argv)

    # 1. Launch Unity app
    unity_process = launch_unity_app("C:/Users/Mart9/Workspace/gui-bt/generated/Builds/Win/SimExample.exe")

    # 2. Wait for Unity window to appear
    unity_hwnd = wait_for_unity_window("SimExample")
    if not unity_hwnd:
        print("Unity window not found. Exiting...")
        unity_process.terminate()
        sys.exit(1)

    # 3. Embed Unity window
    window = UnityEmbedder(unity_hwnd, unity_process)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()