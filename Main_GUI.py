import sys
import subprocess
import requests
import time
import _thread
from threading import Thread
from iLeanManager import iLearnManager
from functools import partial
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QMessageBox
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QGroupBox, QHBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QDesktopWidget,QWidget,QTableWidgetItem, QTabWidget, QPlainTextEdit, QAbstractItemView
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QTableWidget,QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
from multiprocessing.pool import ThreadPool
import img_qr


class myGUI(QMainWindow):
    signal_startDownload = QtCore.pyqtSignal()
    signal_loginSuccess = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.version = 0.1
        self.checkUpdate()
        self.host='https://ilearn2.fcu.edu.tw'
        self.statusbar = self.statusBar()
        self.initUI()
        self.web = iLearnManager(self.host)
        self.init_iLearn()
        self.signal_startDownload.connect(self.startDownload)
        self.signal_loginSuccess.connect(self.ShowResource)

    def init_iLearn(self):
        self.web.signal_finishDownload.connect(self.startDownload)
        self.web.signal_Log.connect(self.print)
        Thread(target=self.TestiLearnConnection())

    def checkUpdate(self):
        with open('version.ini', mode='w') as f:
            f.write(str(self.version))
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
        self.statusbar.addPermanentWidget(self.statusProcessBar)

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
        self.grid.setRowStretch(0, 10)
        self.grid.setRowStretch(1, 10)
        self.grid.setRowStretch(2, 10)
        self.web = iLearnManager()

        self.show()

    def createStatusTable(self):
        self.StatusTable = QTableWidget()
        self.StatusTable.setColumnCount(4)
        horizontal_header = ["檔案名稱","儲存路徑", "檔案模組", "下載進度"]
        self.StatusTable.setHorizontalHeaderLabels(horizontal_header)
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
        self.LogSpace.appendPlainText(time.strftime("[%H:%M:%S] ", time.localtime()) +msg)

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

        self.CourseTreeList = QTreeWidget()
        self.CourseTreeList.setHeaderHidden(True)
        self.CourseTreeList.setEnabled(False)
        self.CourseTreeListRoot = QTreeWidgetItem(self.CourseTreeList)
        self.CourseTreeListRoot.setText(0,"所有課程")
        self.CourseTreeListRoot.setFlags(self.CourseTreeListRoot.flags()|QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
        self.CourseTreeListRoot.setCheckState(0, QtCore.Qt.Unchecked)

        HLayout = QHBoxLayout()
        HLayout.addWidget(self.CourseTreeList)

        groupBox.setLayout(HLayout)

        return groupBox

    def selectAllAction(self,Check):
        items = [self.CourseListBox.itemAt(i).widget() for i in range(self.CourseListBox.count())]
        for idx in range(len(items)):
            checkbox = items[idx]
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(Check)

    def Login(self):
        Thread(target = self.__Login())

    def __Login(self):
        self.web.setUser(self.input_NID.text(),self.input_Pass.text())
        self.label_iLearn.setText('使用者 '+self.input_NID.text()+' 登入中...')
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
            self.signal_loginSuccess.emit()
        else:
            self.statusbar.showMessage('登入失敗')
            self.label_iLearn.setText('登入失敗')
            self.print(UserName + '登入失敗')

    def ShowResource(self):
        self.CourseTreeList.setEnabled(True)
        self.courseList = self.web.getCourseList()
        self.statusProcessBar.setMaximum(len(self.courseList))
        self.statusProcessBar.setValue(0)
        self.statusProcessBar.setFormat('正在獲取課程資源...(%v/' + str(len(self.courseList)) + ')')

        self.fileList = []
        for course in self.courseList:
            courseItem = QTreeWidgetItem(self.CourseTreeListRoot)
            self.CourseTreeListRoot.setExpanded(True)
            courseItem.setFlags(courseItem.flags()|QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
            courseItem.setText(0,course['title'])
            courseItem.setCheckState(0,QtCore.Qt.Unchecked)
            courseItem.setIcon(0,QIcon(':img/mod.course.jpg'))
        index = 0
        for course in self.courseList:
            t = Thread(target=self.ShowFileResource,args=(course,self.CourseTreeListRoot.child(index)))
            t.run()
            index += 1
            self.statusProcessBar.setValue(index)

    def ShowFileResource(self,course,courseItem):
        courseFileList = self.web.getCourseFileList(course)
        for section in courseFileList:
            sectionItem = QTreeWidgetItem(courseItem)
            sectionItem.setFlags(sectionItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            sectionItem.setText(0, section['section'])
            sectionItem.setCheckState(0, QtCore.Qt.Unchecked)
            sectionItem.setIcon(0,QIcon(":img/mod.folder.svg"))
            for recource in section['mods']:
                if recource['mod'] == 'forum':
                    forumItem = QTreeWidgetItem(sectionItem)
                    forumItem.setFlags(forumItem.flags() | QtCore.Qt.ItemIsUserCheckable)
                    forumItem.setText(0, recource['name'])
                    forumItem.setCheckState(0, QtCore.Qt.Unchecked)
                    forumItem.setIcon(0,QIcon(":img/mod.discuss.svg"))
                    for topic in recource['data']:
                        topicItem = QTreeWidgetItem(forumItem)
                        topicItem.setFlags(topicItem.flags() | QtCore.Qt.ItemIsUserCheckable)
                        topicItem.setText(0, topic['name'])
                        topicItem.setCheckState(0, QtCore.Qt.Unchecked)
                        topicItem.setIcon(0,QIcon(":img/mod.discuss.svg"))
                elif recource['mod'] in ['url', 'resource', 'assign', 'page', 'videos']:
                    recourceItem = QTreeWidgetItem(sectionItem)
                    recourceItem.setFlags(recourceItem.flags() | QtCore.Qt.ItemIsUserCheckable)
                    recourceItem.setText(0, recource['name'])
                    recourceItem.setCheckState(0, QtCore.Qt.Unchecked)
                    recourceItem.setIcon(0,QIcon(":img/mod."+recource['mod']+".svg"))
                elif recource['mod'] == 'folder':
                    pass

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