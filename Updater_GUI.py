import sys, os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QProgressBar


class UpdaterGUI(QWidget):

    def __init__(self, restart=False):
        super().__init__()
        self.restart = restart
        self.initGUI()

    def initGUI(self):
        self.progressbar = QProgressBar(self)
        self.progressbar.setGeometry(5, 5, 1000, 25)
        self.progressbar.setFormat(' 0%')

        self.resize(980, 35)
        self.setWindowTitle('iLearnBackupTool Updater')
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    updater = UpdaterGUI()
    sys.exit(app.exec_())
