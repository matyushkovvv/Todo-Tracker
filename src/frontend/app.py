import sys
from PyQt5.QtWidgets import QApplication
from tracker import TodoTracker
from username_dialog import UsernameDialog

class TodoApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.show_username_dialog()
        
    def show_username_dialog(self):
        self.username_dialog = UsernameDialog(self.start_tracker)
        self.username_dialog.show()
        
    def start_tracker(self, username):
        self.tracker_window = TodoTracker(username)
        self.tracker_window.show()
        self.username_dialog.close()
        
    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = TodoApp()
    app.run()