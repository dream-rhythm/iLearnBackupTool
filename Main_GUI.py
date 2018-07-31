import sys
from bs4 import BeautifulSoup
import subprocess
import requests
import img_qr
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QWidget,QMessageBox
from PyQt5.QtWidgets import  QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon


class myGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.version = 0.1
        with open('version.ini',mode='w') as f:
            f.write(str(self.version))
        self.checkUpdate()
        self.web = requests.Session()
        self.statusbar = self.statusBar()
        self.toolbar = self.addToolBar('toolBar')
        self.initUI()

    def checkUpdate(self):
        s = requests.Session()
        versionFile = s.get('https://raw.githubusercontent.com/fcu-d0441320/iLearnBackupTool/master/version.ini')
        version = float(versionFile.text)
        if version > self.version:
            subprocess.Popen('Updater.exe')
            sys.exit()

    def initUI(self):

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('iLearn備份工具')
        self.statusbar.showMessage('備份工具啟動中...')

        exitAct = QAction(QIcon(':img/exit.png'), '關閉工具', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('關閉工具')
        exitAct.triggered.connect(qApp.quit)
        self.toolbar.addAction(exitAct)

        infoAct = QAction(QIcon(':img/info.png'), '關於', self)
        infoAct.setShortcut('Ctrl+I')
        infoAct.setStatusTip('關於')
        infoAct.triggered.connect(self.showInformation)
        self.toolbar.addAction(infoAct)

        self.show()
        self.TestiLearnConnection()

    def showInformation(self):
        QMessageBox.about (self, '關於', 'iLearn備份工具\n工具版本：'+str(self.version)
                             )

    def TestiLearnConnection(self):
        self.statusbar.showMessage('正在測試iLearn2的連線...')
        page = self.web.get("https://ilearn2.fcu.edu.tw/login/index.php")
        html = BeautifulSoup(page.text, 'lxml')
        form_login = html.find('form', id='login')
        if form_login != None:
            self.statusbar.showMessage('iLearn2連線成功!')
        else:
            self.statusbar.showMessage('iLearn2連線失敗!')


if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainGUI = myGUI()

    sys.exit(app.exec_())