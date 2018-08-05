import sys
import subprocess
import requests
import time
import _thread
from iLeanManager import iLearnManager
from functools import partial
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QMessageBox
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QGroupBox, QHBoxLayout
from PyQt5.QtWidgets import QDesktopWidget,QWidget,QTableWidgetItem, QTabWidget, QPlainTextEdit
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QTableWidget,QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
# import img_qr


class myGUI(QMainWindow):
    signal_startDownload = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.version = 0.1
        with open('version.ini',mode='w') as f:
            f.write(str(self.version))
        self.host='https://ilearn2.fcu.edu.tw'
        self.checkUpdate()
        self.statusbar = self.statusBar()
        self.toolbar = self.addToolBar('toolBar')
        self.initUI()
        self.signal_startDownload.connect(self.startDownload)

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
        self.statusProcessBar = QProgressBar()
        self.statusProcessBar.setValue(0)
        self.statusProcessBar.setFormat("就緒...")
        self.statusbar.addPermanentWidget(self.statusProcessBar,stretch=0)

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
        self.grid.addWidget(self.createStatusView(),2,0,1,2)

        self.grid.setColumnStretch(0,10)
        self.grid.setColumnStretch(1,20)
        self.grid.setRowMinimumHeight(2,200)
        self.grid.setRowStretch(0, 10)
        self.grid.setRowStretch(1, 10)
        self.grid.setRowStretch(2, 10)
        self.web = iLearnManager()
        self.web.setInformation(self.host, self.LogSpace)
        self.web.signal_finishDownload.connect(self.startDownload)
        self.web.signal_Log.connect(self.print)

        self.show()
        self.TestiLearnConnection()

    def createStatusTable(self):
        self.StatusTable = QTableWidget()
        self.StatusTable.setColumnCount(4)
        horizontalHeader = ["檔案名稱","儲存路徑", "檔案模組", "下載進度"]
        self.StatusTable.setHorizontalHeaderLabels(horizontalHeader)
        self.StatusTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.StatusTable.setColumnWidth(0, 140)
        self.StatusTable.setColumnWidth(1, 120)
        self.StatusTable.setColumnWidth(2, 120)
        self.StatusTable.setColumnWidth(3, 400)
        return self.StatusTable

    def createLogSpace(self):
        self.LogSpace = QPlainTextEdit()
        self.LogSpace.setReadOnly(True)
        return self.LogSpace

    def print(self, msg):
        self.LogSpace.appendPlainText(time.strftime("[%H:%M:%S]", time.localtime()) +msg)

    def createStatusView(self):
        tabs = QTabWidget()
        tabs.addTab(self.createStatusTable(), "備份狀態")
        tabs.addTab(self.createLogSpace(), "日誌")
        return tabs

    def createLoginGroup(self):
        groupBox = QGroupBox("Step 1:登入iLearn")
        form = QGridLayout()
        label_NID = QLabel("帳號:")
        self.input_NID = QLineEdit()
        label_Pass = QLabel("密碼:")
        self.input_Pass = QLineEdit()
        self.input_Pass.setEchoMode(QLineEdit.Password)
        form.addWidget(label_NID, 0, 0)
        form.addWidget(self.input_NID, 0, 1, 1, 2)
        form.addWidget(label_Pass, 1, 0)
        form.addWidget(self.input_Pass, 1, 1, 1, 2)

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
        self.btn_selectAll = QPushButton('全選',self)
        self.btn_selectAll.setEnabled(False)
        self.btn_selectAll.clicked[bool].connect(partial(self.selectAllAction,True))
        self.btn_selectNone = QPushButton('全不選', self)
        self.btn_selectNone.setEnabled(False)
        self.btn_selectNone.clicked[bool].connect(partial(self.selectAllAction, False))
        btnLayout = QVBoxLayout()
        btnLayout.addWidget(self.btn_selectAll)
        btnLayout.addWidget(self.btn_selectNone)
        btnLayout.addStretch(1)

        HLayout = QHBoxLayout()
        HLayout.addLayout(self.CourseListBox)
        HLayout.addItem(btnLayout)
        HLayout.setStretch(0,17)
        HLayout.setStretch(1,3)

        groupBox.setLayout(HLayout)

        return groupBox

    def selectAllAction(self,Check):
        items = [self.CourseListBox.itemAt(i).widget() for i in range(self.CourseListBox.count())]
        for idx in range(len(items)):
            checkbox = items[idx]
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(Check)

    def Login(self):
        self.web.setUser(self.input_NID.text(),self.input_Pass.text())
        self.print('使用者 '+self.input_NID.text()+' 登入中...')
        status, UserName = self.web.Login()
        if status:  # == True
            self.statusbar.showMessage('登入成功')
            self.label_iLearn.setText(UserName+' 已成功登入')
            self.print(UserName+' 已成功登入')
            self.input_Pass.setEnabled(False)
            self.input_NID.setEnabled(False)
            self.btn_login.setEnabled(False)
            self.btn_clean.setEnabled(False)
            self.btn_selectAll.setEnabled(True)
            self.btn_selectNone.setEnabled(True)
            self.ShowCourseList()
        else:
            self.statusbar.showMessage('登入失敗')
            self.label_iLearn.setText('登入失敗')
            self.print(UserName + '登入失敗')

    def ShowCourseList(self):
        self.courseList = self.web.getCourseList()
        self.NumOfSelect = 0
        for course in self.courseList:
            checkBox = QCheckBox(course['title'])
            checkBox.setChecked(True)
            checkBox.stateChanged.connect(partial(self.changeCheckedStatus))
            self.CourseListBox.insertWidget(self.NumOfSelect,checkBox)
            self.NumOfSelect+=1
        self.btn_StartBackup.setEnabled(True)

    def changeCheckedStatus(self,checked):
        if checked == QtCore.Qt.Unchecked:
            self.NumOfSelect -= 1
        elif checked == QtCore.Qt.Checked:
            self.NumOfSelect += 1

    def showFileList(self):
        backupList = []
        items = [self.CourseListBox.itemAt(i).widget() for i in range(self.CourseListBox.count())]
        for idx in range(len(items)):
            checkbox = items[idx]
            if isinstance(checkbox, QCheckBox):
                for ele in self.courseList:
                    if ele['title'] == checkbox.text():
                        course = ele
                        break
                if checkbox.isChecked():
                    backupList.append(course)
        self.fileList = []
        i = 1
        for course in backupList:
            coursefile = self.web.getCourseFileList(course)
            self.btn_StartBackup.setText('正在獲取檔案清單中,請稍後...('+str(i)+'/'+str(len(backupList))+')')
            i+=1
            self.fileList.extend(coursefile)
            for ele in coursefile:
                row_count = self.StatusTable.rowCount()
                self.StatusTable.insertRow(row_count)
                self.StatusTable.setItem(row_count, 0, QTableWidgetItem(ele['name']))
                self.StatusTable.setItem(row_count, 1, QTableWidgetItem(ele['path']))
                self.StatusTable.setItem(row_count, 2, QTableWidgetItem(ele['mod']))
                self.StatusTable.setItem(row_count, 3, QTableWidgetItem('等待中...'))
        self.nowDownload = 0
        self.signal_startDownload.emit()

    def startDownload(self):
        if self.nowDownload < len(self.fileList):
            self.web.DownloadFile(self.StatusTable,self.nowDownload,self.fileList[self.nowDownload])
            self.nowDownload += 1
            self.btn_StartBackup.setText('正在下載...('+str(self.nowDownload)+'/'+str(len(self.fileList))+')')
            self.print('nowDownload='+str(self.nowDownload))

    def StartBackup(self):
        if self.NumOfSelect == 0:
            self.btn_StartBackup.setText('請先選擇課程再按開始備份!')
        else:
            self.btn_selectAll.setEnabled(False)
            self.btn_selectNone.setEnabled(False)
            self.btn_StartBackup.setText('正在獲取檔案清單中,請稍後...')
            self.btn_StartBackup.setEnabled(False)
            items = [self.CourseListBox.itemAt(i).widget() for i in range(self.CourseListBox.count())]
            for idx in range(len(items)):
                checkbox = items[idx]
                if isinstance(checkbox, QCheckBox):
                    checkbox.setEnabled(False)
            _thread.start_new_thread(self.showFileList, ())

    def showInformation(self):
        QMessageBox.about(self, '關於', 'iLearn備份工具\n工具版本：'+str(self.version))

    def TestiLearnConnection(self):
        self.statusbar.showMessage('正在測試iLearn2的連線...')
        self.label_iLearn.setText('連線中...')
        if self.web.TestConnection():   # ==Ture
            self.statusbar.showMessage('iLearn2連線成功!')
            self.label_iLearn.setText('連線成功!')
        else:
            self.statusbar.showMessage('iLearn2連線失敗!')
            self.label_iLearn.setText('連線失敗!')


if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainGUI = myGUI()

    sys.exit(app.exec_())