import os
import sys
import requests
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtWidgets import QProgressBar, QLabel
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal


downfile = 'iLearnBackupTool.exe'
tempfile = '~$iLearnBackupTool.exe'


class UpdaterGUI(QWidget):

    class Downloader(QThread):
        gotchunk = pyqtSignal(float)
        finished = pyqtSignal()
        error = pyqtSignal(str)

        def __init__(self, url):
            super().__init__()
            self.url = url

        def run(self):
            try:
                binfile = open(tempfile, 'wb')
                dlink = requests.Session().get(self.url, stream=True)
                total_size = int(dlink.headers['Content-Length'])
                chunk_size = 512
                recived = 0

                for chunk in dlink.iter_content(chunk_size=chunk_size):
                    recived += binfile.write(chunk)
                    self.gotchunk.emit(recived / total_size)

                self.finished.emit()
                binfile.close()
                dlink.close()
            except Exception as e:
                self.error.emit(str(e))

    def __init__(self):
        super().__init__()
        self.durl = 'https://raw.githubusercontent.com/fcu-d0441320/iLearnBackupTool/master/iLearnBackupTool.exe'
        self.progressbar = QProgressBar(self)
        self.progresslabel = QLabel(self.progressbar)
        self.initGUI()

        self.downloader = self.Downloader(self.durl)
        self.downloader.gotchunk.connect(self.setProgressValue)
        self.downloader.error.connect(self.errorHandler)
        self.downloader.finished.connect(self.finished)

        self.show()
        self.downloader.start()

    def initGUI(self):
        self.setWindowTitle('iLearnBackupTool Updater')
        self.resize(975, 35)

        self.progressbar.setGeometry(5, 5, 1000, 25)
        self.progressbar.setValue(0)

        w = 50
        h = 30
        x = (self.progressbar.width() / 2 - w / 2)
        y = (self.progressbar.height() / 2 - h / 2)
        self.progresslabel.setGeometry(x, y, w, h)
        self.progresslabel.setText('{0:2d}%'.format(0))

    def setProgressValue(self, val):
        self.progressbar.setValue(round(val * 100, 2))
        self.progresslabel.setText('{0:.2f}%'.format(val * 100))

    def errorHandler(self, err_msg):
        QMessageBox.information(self, '噢奧!出錯了!', err_msg, QMessageBox.Ok)
        os.remove(tempfile)
        QCoreApplication.instance().quit()

    def finished(self):
        QMessageBox.information(self, '下載完成', '下載成功！', QMessageBox.Ok)
        os.remove(downfile)
        os.rename(tempfile, downfile)
        QCoreApplication.instance().quit()


if __name__ == '__main__':

    def str2bool(s):
        sl = s.lower()
        if sl in ("yes", "true", "t", "1"):
            return True
        elif sl in ('no', 'false', 'f', '0'):
            return False
        else:
            raise ValueError(s)

    args = {'check': True, 'restart': True}

    if len(sys.argv) > 1:

        try:
            for arg in sys.argv[1:]:
                pm = arg.lower()
                split = pm.split('=')
                if split[0] == 'check':
                    args['check'] = str2bool(split[1])
                elif split[0] == 'restart':
                    args['restart'] = str2bool(split[1])
                else:
                    raise ValueError(arg)
        except ValueError as ve:
            print('\'' + str(ve) + '\'' + ' is not a valid parameter')
            exit(1)

    # 主要執行部分
    if args['check']:
        app = QApplication(sys.argv)
        updater = UpdaterGUI()
        app.exec_()
    if args['restart']:
        subprocess.Popen(downfile)

    sys.exit(0)
