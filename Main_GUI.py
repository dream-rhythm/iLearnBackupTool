import sys
import subprocess
import requests
import img_qr
from iLeanManager import iLearnManager
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QMessageBox
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout,QGroupBox,QDesktopWidget,QWidget
from PyQt5.QtWidgets import QLabel, QLineEdit,QPushButton,QRadioButton,QCheckBox,QTableWidget
from PyQt5.QtGui import QIcon

class myGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.version = 0.1
        with open('version.ini',mode='w') as f:
            f.write(str(self.version))
        self.checkUpdate()
        #self.grid = QGridLayout()

        self.web = iLearnManager()
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

    def moveToCenter(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
        (screen.height() - size.height()) / 2)

    def initUI(self):
        self.setFixedSize(800,600)
        self.moveToCenter()
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

        self.grid = QGridLayout()
        widget = QWidget()
        self.setCentralWidget(widget)
        widget.setLayout(self.grid)
        self.grid.addWidget(self.createLoginGroup(),0,0)
        self.grid.addWidget(self.createSaveGroup(),1,0)
        self.grid.addWidget(self.createCourseGroup(),0,1,2,1)
        self.grid.addWidget(self.createStatusTable(),2,0,1,2)

        self.grid.setColumnStretch(0,10)
        self.grid.setColumnStretch(1,20)
        self.grid.setRowMinimumHeight(2,200)
        self.grid.setRowStretch(0, 10)
        self.grid.setRowStretch(1, 10)
        self.grid.setRowStretch(2, 10)

        self.show()
        self.TestiLearnConnection()

    def createStatusTable(self):
        self.StatusTable = QTableWidget()
        self.StatusTable.setColumnCount(5)
        horizontalHeader = ["課程", "區塊", "檔案名稱", "檔案模組", "下載進度"]
        self.StatusTable.setHorizontalHeaderLabels(horizontalHeader)
        return self.StatusTable

    def createLoginGroup(self):
        groupBox = QGroupBox("Step 1:登入iLearn")
        form = QGridLayout()
        label_NID = QLabel("帳號:")
        self.input_NID = QLineEdit()
        label_Pass = QLabel("密碼:")
        self.input_Pass = QLineEdit()
        self.input_Pass.setEchoMode(QLineEdit.Password)
        form.addWidget(label_NID,0,0)
        form.addWidget(self.input_NID,0,1,1,2)
        form.addWidget(label_Pass,1,0)
        form.addWidget(self.input_Pass,1,1,1,2)

        self.btn_clean = QPushButton('清除', self)
        self.btn_clean.clicked[bool].connect(self.cleanLogin)
        form.addWidget(self.btn_clean, 2, 1)

        self.btn_login = QPushButton('登入', self)
        self.btn_login.clicked[bool].connect(self.Login)
        form.addWidget(self.btn_login, 2, 2)

        label_iLearnStatus = QLabel("iLearn狀態:")
        form.addWidget(label_iLearnStatus, 3, 0)

        self.label_iLearn = QLabel()
        form.addWidget(self.label_iLearn, 3, 1, 1, 2)

        vbox = QVBoxLayout()
        vbox.addLayout(form)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)

        return groupBox

    def cleanLogin(self):
        self.input_NID.setText("")
        self.input_Pass.setText("")

    def createSaveGroup(self):
        groupBox = QGroupBox("Step 3:選擇儲存類型")

        radio1 = QRadioButton("儲存成檔案")
        radio1.setChecked(True)
        radio2 = QRadioButton("儲存成網頁")
        radio2.setEnabled(False)

        self.btn_StartBackup = QPushButton('開始備份', self)
        self.btn_StartBackup.setEnabled(False)
        self.btn_StartBackup.clicked[bool].connect(self.StartBackup)

        vbox = QVBoxLayout()
        vbox.addWidget(radio1)
        vbox.addWidget(radio2)
        vbox.addWidget(self.btn_StartBackup)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)

        return groupBox

    def createCourseGroup(self):
        groupBox = QGroupBox("Step 2:選擇要備份的課程")

        self.CourseListBox = QVBoxLayout()
        self.CourseListBox.addStretch(1)
        groupBox.setLayout(self.CourseListBox)

        return groupBox

    def Login(self):
        self.web.setUser(self.input_NID.text(),self.input_Pass.text())
        status,UserName = self.web.Login()
        if status == True:
            self.statusbar.showMessage('登入成功')
            self.label_iLearn.setText(UserName+' 已成功登入')
            self.input_Pass.setEnabled(False)
            self.input_NID.setEnabled(False)
            self.btn_login.setEnabled(False)
            self.btn_clean.setEnabled(False)
            self.ShowCourseList()
        else:
            self.statusbar.showMessage('登入失敗')
            self.label_iLearn.setText('登入失敗')

    def ShowCourseList(self):
        courseList = self.web.getCourseList()
        for course in courseList:
            checkBox = QCheckBox(course['title'])
            checkBox.setChecked(True)
            self.CourseListBox.addWidget(checkBox)
        self.btn_StartBackup.setEnabled(True)

    def StartBackup(self):
        pass

    def showInformation(self):
        QMessageBox.about (self, '關於', 'iLearn備份工具\n工具版本：'+str(self.version))

    def TestiLearnConnection(self):
        self.statusbar.showMessage('正在測試iLearn2的連線...')
        self.label_iLearn.setText('連線中...')
        if self.web.TestConnection() == True:
            self.statusbar.showMessage('iLearn2連線成功!')
            self.label_iLearn.setText('連線成功!')
        else:
            self.statusbar.showMessage('iLearn2連線失敗!')
            self.label_iLearn.setText('連線失敗!')


if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainGUI = myGUI()

    sys.exit(app.exec_())