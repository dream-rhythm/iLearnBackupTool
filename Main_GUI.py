import sys
import subprocess
import requests
import time
from threading import Thread
from iLeanManager import iLearnManager
from functools import partial
from os.path import exists
from os import system, makedirs
import language
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QMessageBox
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QGroupBox, QHBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QDesktopWidget,QWidget,QTableWidgetItem, QTabWidget, QPlainTextEdit, QComboBox
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QTableWidget,QProgressBar
from PyQt5.QtGui import QIcon
from Updater_GUI import UpdaterGUI
from PyQt5 import QtCore
from configparser import ConfigParser
import threadpool
import img_qr

string = language.string()

class myGUI(QMainWindow):
    signal_loginSuccess = QtCore.pyqtSignal()
    signal_startShowTree = QtCore.pyqtSignal()
    signal_setStartBackupBtn = QtCore.pyqtSignal(str,bool)
    signal_showUserOptionWindow = QtCore.pyqtSignal()
    signal_showDevOptionWindow = QtCore.pyqtSignal()
    signal_close = QtCore.pyqtSignal()
    signal_appendDownloadList = QtCore.pyqtSignal(dict)
    signal_processbar_value = QtCore.pyqtSignal(int)
    signal_startUpdate = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config = ConfigParser()
        self.pool = threadpool.ThreadPool(4)
        self.DownloadPool= threadpool.ThreadPool(1)
        self.readSetting()
        string.setLanguage(self.config['User']['language'])
        self.version = 0.1
        self.host='https://ilearn2.fcu.edu.tw'
        self.statusbar = self.statusBar()
        self.initUI()
        self.web = iLearnManager(self.host)
        self.init_iLearn()
        self.FileTree={}
        self.success = 0
        self.failed = 0
        self.fileList=[]
        self.retryList=[]
        self.failedList=[]
        self.retryTimes=0
        self.nowLoad = 0
        self.retryAfter = 0
        self.initCheckUpdate = False
        self.retryTimer = QtCore.QTimer()
        self.retryTimer.timeout.connect(self.startRetry)
        self.signal_loginSuccess.connect(self.ShowResource)
        self.signal_appendDownloadList.connect(self.appendItemToDownloadList)
        self.signal_processbar_value.connect(self.setProcessBarValue)
        self.signal_startShowTree.connect(self.startShowTree)
        self.signal_setStartBackupBtn.connect(self.setStartBackupBtn)
        self.timer_checkUpdate = QtCore.QTimer()
        self.timer_checkUpdate.timeout.connect(self.checkUpdate)
        self.timer_checkUpdate.start(1000)
        if self.config['dev'].getboolean('autologin')==True:
            self.btn_login.click()

    def closeEvent(self, event):
        self.signal_close.emit()
        self.close()

    def setStatusBarText(self,str):
        self.statusbar.showMessage(str)

    def init_iLearn(self):
        self.web.signal_finishDownload.connect(self.startDownload)
        self.web.signal_setStatusProcessBar.connect(self.setStatusProcessBar)
        self.web.signal_Log.connect(self.print)
        self.web.signal_setStatusBarText.connect(self.setStatusBarText)
        t = Thread(target=self.TestiLearnConnection)
        t.run()

    def setStartBackupBtn(self,text,enabled):
        self.btn_StartBackup.setEnabled(enabled)
        self.btn_StartBackup.setText(text)

    def setStatusProcessBar(self,idx,value):
        if value==-1:
            ProcessBar = QProgressBar()
            self.StatusTable.setCellWidget(idx,3,ProcessBar)
        elif value==-2:
            if self.retryTimes==0:
                self.failed +=1
            self.failedList.append(idx)
            self.StatusTable.removeCellWidget(idx, 3)       # 移除進度條之控件
            ErrorIcon = QIcon(":img/DownloadFailed.png")    # 開啟下載失敗之圖案
            item = QTableWidgetItem(ErrorIcon, string._('Download Falied'))  # 新增顯示失敗的元件
            self.StatusTable.setItem(idx, 3, item)          # 將新元件設定到表格內
            if idx==len(self.fileList)-1:
                self.signal_processbar_value.emit(idx+1)
            self.finishDownloadCheck(idx)
        elif value==101:
            if self.retryTimes!=0:
                self.failed -=1
            self.success +=1
            self.print(string._('Download file %d finish!')%(idx+1))
            self.StatusTable.removeCellWidget(idx, 3)
            OkIcon = QIcon(":img/FinishDownload.png")  # 開啟下載完成之圖案
            item = QTableWidgetItem(OkIcon, "OK")  # 新增顯示OK的元件
            self.StatusTable.setItem(idx, 3, item)  # 將新元件設定到表格內
            self.finishDownloadCheck(idx)
        else:
            ProcessBar = self.StatusTable.cellWidget(idx, 3)
            if ProcessBar == None:
                ProcessBar = QProgressBar()
                self.StatusTable.setCellWidget(idx, 3, ProcessBar)
            ProcessBar.setValue(value)

    def finishDownloadCheck(self,idx):
        def checkIsEndElement(idx):
            if self.retryTimes==0:
                return idx==len(self.fileList)-1
            else:
                return idx==self.retryList[-1]
        def backupFinish():
            self.signal_processbar_value.emit(self.statusProcessBar.maximum())
            self.signal_setStartBackupBtn.emit(string._('Start Backup'), True)
            QMessageBox.information(self, string._("Download finish!"),
                                    string._("Success:%d\nFailed:%d") % (self.success, self.failed))
        if checkIsEndElement(idx):
            if self.retryTimes==self.config['User'].getint('retrytimes'):
                backupFinish()
            else:
                self.signal_processbar_value.emit(self.statusProcessBar.maximum())
                if self.failed==0:
                    backupFinish()
                else:
                    self.retryAfter = self.config['User'].getint('secondbetweenretry')
                    self.retryTimer.start(1000)

    def checkUpdate(self):
        try:
            self.timer_checkUpdate.stop()
        except:
            pass
        with open('version.ini', mode='w') as f:
            f.write(str(self.version))
        s = requests.Session()
        versionFile = s.get('https://raw.githubusercontent.com/fcu-d0441320/iLearnBackupTool/master/version.ini')
        version = float(versionFile.text)
        if version > self.version:
            reply = QMessageBox.question(self, string._('Find New version'), string._('Find New Version:%.1f\nNow Vsrsion:%.1f\nDo you want to update?')%(version,self.version),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply== QMessageBox.Yes:
                self.setVisible(False)
                self.signal_startUpdate.emit(self.config['User']['language'])
        else:
            if self.initCheckUpdate==False:
                self.initCheckUpdate=True
            else:
                QMessageBox.information(self,string._('This is the latest version'),string._('This is the latest version'))
                #QMessageBox().information(self,"有更新版本!","發現有新版本，請前往官網更新，或檢查是否與Updater_GUI.exe放置於相同資料夾!")

    def moveToCenter(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
        (screen.height() - size.height()) / 2)

    def initUI(self):
        self.resize(800,600)
        self.setWindowIcon(QIcon(':img/Main_Icon.png'))
        self.moveToCenter()
        self.setWindowTitle(string._('iLearn Backup Tool'))
        self.statusbar.showMessage(string._('Starting Backup Tool...'))
        self.createMenu()
        self.statusProcessBar = QProgressBar()
        self.statusProcessBar.setValue(0)
        self.statusProcessBar.setFormat(string._("Ready..."))
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
        self.grid.setRowStretch(0, 6)
        self.grid.setRowStretch(1, 6)
        self.grid.setRowStretch(2, 10)
        self.web = iLearnManager()

        self.show()

    def createStatusTable(self):
        self.StatusTable = QTableWidget()
        self.StatusTable.setColumnCount(4)
        horizontal_header = [string._('File name'),string._('Path'),string._('iLearn mod'),string._('Download status')]
        self.StatusTable.setHorizontalHeaderLabels(horizontal_header)
        self.StatusTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.StatusTable.setColumnWidth(0, 140)
        self.StatusTable.setColumnWidth(1, 120)
        self.StatusTable.setColumnWidth(2, 120)
        self.StatusTable.setColumnWidth(3, 380)
        return self.StatusTable

    def createLogSpace(self):
        self.LogSpace = QPlainTextEdit()
        self.LogSpace.setReadOnly(True)
        return self.LogSpace

    def print(self, msg):
        self.LogSpace.appendPlainText(time.strftime("[%H:%M:%S] ", time.localtime()) +msg)

    def createStatusView(self):
        tabs = QTabWidget()
        tabs.addTab(self.createStatusTable(), string._('Backup status'))
        tabs.addTab(self.createLogSpace(), string._('Log'))
        return tabs

    def createLoginGroup(self):
        groupBox = QGroupBox(string._('Step 1: Login'))
        form = QGridLayout()
        label_NID = QLabel(string._('NID:'))
        self.input_NID = QLineEdit()
        self.input_NID.setText(self.config['dev']['nid'])
        label_Pass = QLabel(string._('Password:'))
        self.input_Pass = QLineEdit()
        self.input_Pass.setText(self.config['dev']['pass'])
        self.input_Pass.setEchoMode(QLineEdit.Password)
        form.addWidget(label_NID, 0, 0)
        form.addWidget(self.input_NID, 0, 1, 1, 2)
        form.addWidget(label_Pass, 1, 0)
        form.addWidget(self.input_Pass, 1, 1, 1, 2)

        self.btn_clean = QPushButton(string._('Clean'), self)
        self.btn_clean.clicked[bool].connect(self.cleanLogin)
        form.addWidget(self.btn_clean, 2, 1)

        self.btn_login = QPushButton(string._('Login'), self)
        self.btn_login.clicked[bool].connect(self.Login)
        form.addWidget(self.btn_login, 2, 2)

        label_iLearnStatus = QLabel(string._('iLearn status:'))
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
        groupBox = QGroupBox(string._('Step 3:Select save option'))

        radio1 = QRadioButton(string._('Save as file'))
        radio1.setChecked(True)
        radio2 = QRadioButton(string._('Save as web page'))
        radio2.setEnabled(False)

        self.btn_StartBackup = QPushButton(string._('Start Backup'), self)
        self.btn_StartBackup.setEnabled(False)
        self.btn_StartBackup.clicked[bool].connect(self.StartBackup)
        self.btn_OpenFolder = QPushButton(string._('Open Folder'), self)
        self.btn_OpenFolder.clicked[bool].connect(self.OpenFolder)

        vbox = QVBoxLayout()
        vbox.addWidget(radio1)
        vbox.addWidget(radio2)
        vbox.addWidget(self.btn_StartBackup)
        vbox.addWidget(self.btn_OpenFolder)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)

        if not exists('iLearn'):
            makedirs('iLearn')

        return groupBox

    def OpenFolder(self):
        system("explorer iLearn")

    def createCourseGroup(self):
        groupBox = QGroupBox(string._('Step 2:Select sourse resource to backup'))

        self.CourseListBox = QVBoxLayout()
        self.CourseListBox.addStretch(1)

        self.CourseTreeList = QTreeWidget()
        self.CourseTreeList.setHeaderHidden(True)
        self.CourseTreeList.setEnabled(False)
        self.CourseTreeList.itemExpanded.connect(self.ExpandCourse)
        self.CourseTreeListRoot = QTreeWidgetItem(self.CourseTreeList)
        self.CourseTreeListRoot.setText(0,string._("All course"))
        self.CourseTreeListRoot.setFlags(self.CourseTreeListRoot.flags()|QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
        self.CourseTreeListRoot.setCheckState(0, QtCore.Qt.Unchecked)

        HLayout = QHBoxLayout()
        HLayout.addWidget(self.CourseTreeList)

        groupBox.setLayout(HLayout)

        return groupBox

    def createMenu(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu(string._('File'))
        closeAct = QAction(QIcon(':img/Close_Icon.png'),string._('Quit'), self)
        closeAct.triggered.connect(qApp.quit)
        fileMenu.addAction(closeAct)

        optMenu = menubar.addMenu(string._('Option'))
        DevOptAct = QAction(QIcon(':img/Settings_Icon.png'),string._('Developer options'),self)
        DevOptAct.triggered.connect(self.showDevOption)
        UserOptionAction = QAction(QIcon(':img/Settings_Icon.png'),string._('Preferences'),self)
        UserOptionAction.triggered.connect(self.showUserOption)
        optMenu.addAction(UserOptionAction)
        optMenu.addAction(DevOptAct)

        helpMenu = menubar.addMenu(string._('Help'))
        helpAct = QAction(QIcon(':img/Help_Icon.png'),string._('Help'), self)
        helpAct.triggered.connect(self.showHelp)
        aboutAct = QAction(QIcon(':img/About_Icon.png'),string._('About'), self)
        aboutAct.triggered.connect(self.showInformation)
        checkUpdateAct = QAction(QIcon(':img/Update_Icon.png'),string._('Check update'), self)
        checkUpdateAct.triggered.connect(self.checkUpdate)
        helpMenu.addAction(helpAct)
        helpMenu.addAction(checkUpdateAct)
        helpMenu.addAction(aboutAct)

    def showHelp(self):
        system("explorer http://github.com/fcu-d0441320/iLearnBackupTool")

    def showUserOption(self):
        self.signal_showUserOptionWindow.emit()

    def showDevOption(self):
        self.signal_showDevOptionWindow.emit()

    def Login(self):
        t = Thread(target = self.__Login)
        t.run()

    def __Login(self):
        self.web.setUser(self.input_NID.text(),self.input_Pass.text())
        self.label_iLearn.setText(string._('User %s is signing in...')%self.input_NID.text())
        self.print(string._('User %s is signing in...')%self.input_NID.text())
        status, UserName = self.web.Login()
        if status:  # == True
            self.statusbar.showMessage(string._('Sign in success'))
            self.label_iLearn.setText(string._('%s sign in sucess')%(UserName))
            self.print(string._('%s sign in sucess')%(UserName))
            self.input_Pass.setEnabled(False)
            self.input_NID.setEnabled(False)
            self.btn_login.setEnabled(False)
            self.btn_clean.setEnabled(False)
            self.signal_loginSuccess.emit()
        else:
            self.statusbar.showMessage(string._('Sign in failed'))
            self.label_iLearn.setText(string._('Sign in failed'))
            self.print(UserName + string._('Sign in failed'))
        self.nowLoad = 0

    def ShowResource(self):
        self.CourseTreeList.setEnabled(True)
        self.courseList = self.web.getCourseList()

        for course in self.courseList:
            courseItem = QTreeWidgetItem(self.CourseTreeListRoot)
            self.CourseTreeListRoot.setExpanded(True)
            courseItem.setFlags(courseItem.flags()|QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
            courseItem.setText(0,course['title'])
            courseItem.setCheckState(0,QtCore.Qt.Unchecked)
            courseItem.setIcon(0,QIcon(':img/mod.course.jpg'))

            child = QTreeWidgetItem(courseItem)
            child.setFlags(courseItem.flags()|QtCore.Qt.ItemIsUserCheckable)
            child.setText(0,string._('Loading...'))
            child.setCheckState(0, QtCore.Qt.Unchecked)
        self.startBackgroundLoad()

    def ExpandCourse(self,courseItem):
        if courseItem.child(0).text(0)==string._('Loading...'):
            i = 0
            for ele in self.courseList:
                if ele['title'] == courseItem.text(0):
                    break
                else:
                    i += 1
            self.timer = QtCore.QTimer()  # 计时器
            self.timer.timeout.connect(partial(self.appedResourceToTree, i, courseItem))
            self.timer.start(10)

    def startBackgroundLoad(self):
        if self.nowLoad<len(self.courseList):
            self.statusProcessBar.setMaximum(len(self.courseList))
            self.statusProcessBar.setFormat(string._('Loding course resource')+'(%v/'+'%d)'%(len(self.courseList)))

            reqs = threadpool.makeRequests(self.loadFileTreeBackground, range(len(self.courseList)))
            for req in reqs:
                self.pool.putRequest(req)

    def setProcessBarValue(self,value):
        if value ==self.statusProcessBar.maximum():
            self.statusProcessBar.setFormat(string._('Ready...'))
            self.statusProcessBar.setMaximum(100)
            self.statusProcessBar.setValue(0)
        else:
            self.statusProcessBar.setValue(value)

    def startShowTree(self):
        for i, courseItem in [(i, self.CourseTreeListRoot.child(i)) for i in
                              range(self.CourseTreeListRoot.childCount())]:
            if courseItem.child(0).text(0) == string._('Loading...'):
                self.appedResourceToTree(i, courseItem)

    def loadFileTreeBackground(self,index):
        self.signal_processbar_value.emit(index)
        if self.courseList[index]['title'] not in self.FileTree:
            FileList = self.web.getCourseFileList(self.courseList[index]
                                                  ,useRealFileName=self.config['User'].getboolean('userealfilename')
                                                  ,showTime=self.config['dev'].getboolean('showloadtime'))
            if self.courseList[index]['title'] not in self.FileTree:
                self.FileTree[self.courseList[index]['title']] = FileList
        if index == len(self.courseList)-1:
            self.signal_processbar_value.emit(len(self.courseList))
            self.signal_setStartBackupBtn.emit(string._('Start Backup'),True)
            self.signal_startShowTree.emit()

    def appedResourceToTree(self,i,courseItem):
        course = self.courseList[i]
        try:
            self.timer.stop()
        except:
            pass
        tStart = time.time()
        if course['title'] not in self.FileTree:
            courseFileList = self.web.getCourseFileList(course,useRealFileName=self.config['User'].getboolean('userealfilename')
                                                  ,showTime=self.config['dev'].getboolean('showloadtime'))
            if course['title'] not in self.FileTree:
                self.FileTree[course['title']] = courseFileList
                self.nowLoad += 1
        else:
            courseFileList = self.FileTree[course['title']]
        checkStatus = courseItem.checkState(0)
        totalFiles = 0
        if len(courseFileList)==0:
            sectionItem = QTreeWidgetItem(courseItem)
            sectionItem.setFlags(sectionItem.flags() |QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
            sectionItem.setText(0, string._('There has no resource to download.'))
            sectionItem.setCheckState(0, checkStatus)
        for section in courseFileList:
            sectionItem = QTreeWidgetItem(courseItem)
            sectionItem.setFlags(sectionItem.flags() |QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
            sectionItem.setText(0, section['section'])
            sectionItem.setCheckState(0, checkStatus)
            sectionItem.setIcon(0,QIcon(":img/mod.folder.svg"))
            for recource in section['mods']:
                if recource['mod'] == 'forum':
                    forumItem = QTreeWidgetItem(sectionItem)
                    forumItem.setFlags(forumItem.flags() |QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
                    forumItem.setText(0, recource['name'])
                    forumItem.setCheckState(0, checkStatus)
                    forumItem.setIcon(0,QIcon(":img/mod.discuss.svg"))
                    for topic in recource['data']:
                        topicItem = QTreeWidgetItem(forumItem)
                        topicItem.setFlags(topicItem.flags() |QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
                        topicItem.setText(0, topic['name'])
                        topicItem.setCheckState(0,checkStatus)
                        topicItem.setIcon(0,QIcon(":img/mod.discuss.svg"))
                        totalFiles += 1
                elif recource['mod'] in ['url', 'resource', 'assign', 'page', 'videos']:
                    recourceItem = QTreeWidgetItem(sectionItem)
                    recourceItem.setFlags(recourceItem.flags() |QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
                    recourceItem.setText(0, recource['name'])
                    recourceItem.setCheckState(0, checkStatus)
                    recourceItem.setIcon(0,QIcon(":img/mod."+recource['mod']+".svg"))
                    totalFiles += 1
                elif recource['mod'] == 'folder':
                    folderItem = QTreeWidgetItem(sectionItem)
                    folderItem.setFlags(folderItem.flags() |QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
                    folderItem.setText(0, recource['name'])
                    folderItem.setCheckState(0, checkStatus)
                    folderItem.setIcon(0, QIcon(":img/mod.folder.svg"))
                    for file in recource['data']:
                        fileItem = QTreeWidgetItem(folderItem)
                        fileItem.setFlags(fileItem.flags() |QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
                        fileItem.setText(0, file['name'])
                        fileItem.setCheckState(0, checkStatus)
                        fileItem.setIcon(0, QIcon(":img/mod.resource.svg"))
                        totalFiles += 1
        courseItem.removeChild(courseItem.child(0))
        tStop = time.time()
        if self.config['dev'].getboolean('showloadtime'):
            self.print(string._('Load course %s in %.3f sec, total has %d resource(s)')%(courseItem.text(0),tStop-tStart,totalFiles))

    def showFileList(self):
        self.btn_StartBackup.setEnabled(False)
        courseIndex = 0
        for courseItem in [self.CourseTreeListRoot.child(i) for i in range(self.CourseTreeListRoot.childCount())]:
            courseIndex += 1
            self.signal_processbar_value.emit(courseIndex)
            courseData = self.FileTree[courseItem.text(0)]
            if courseItem.checkState(0)!=QtCore.Qt.Unchecked:
                for sectionItem in [courseItem.child(i) for i in range(courseItem.childCount())]:
                    sectionItemName = sectionItem.text(0)
                    if sectionItemName==string._('There has no resource to download.'):
                        continue
                    sectionData = [courseData[i] for i in range(len(courseData)) if courseData[i]['section']==sectionItemName][0]
                    if sectionItem.checkState(0)!=QtCore.Qt.Unchecked:
                        for modItem in [sectionItem.child(i)for i in range(sectionItem.childCount())]:
                            modItemName = modItem.text(0)
                            modData = [sectionData['mods'][i] for i in range(len(sectionData['mods'])) if sectionData['mods'][i]['name']==modItemName][0]
                            if modItem.checkState(0)!=QtCore.Qt.Unchecked:
                                if modData['mod']=='forum':
                                    for topicItem in [modItem.child(i) for i in range(modItem.childCount())]:
                                        if topicItem.checkState(0)==QtCore.Qt.Checked:
                                            topicName = topicItem.text(0)
                                            resource = [modData['data'][i]for i in range(len(modData['data'])) if modData['data'][i]['name']==topicName][0]
                                            self.signal_appendDownloadList.emit(resource)
                                elif  modData['mod']in ['resource','url', 'assign', 'page', 'videos']:
                                    if modItem.checkState(0)==QtCore.Qt.Checked:
                                        self.signal_appendDownloadList.emit(modData)
                                elif modData['mod']=='folder':
                                    for fileItem in [modItem.child(i)for i in range(modItem.childCount())]:
                                        if fileItem.checkState(0)==QtCore.Qt.Checked:
                                            fileName = fileItem.text(0)
                                            resource = [modData['data'][i] for i in range(len(modData['data'])) if  modData['data'][i]['name'] == fileName][0]
                                            self.signal_appendDownloadList.emit(resource)
        self.retryTimes = 0
        self.failedList=[]
        self.retryList=[]
        self.success = 0
        self.failed = 0
        time.sleep(0.5)
        reqs = threadpool.makeRequests(self.startDownload, range(len(self.fileList)))
        for req in reqs:
            self.DownloadPool.putRequest(req)
        if len(self.fileList) == 0:
            self.btn_StartBackup.setEnabled(True)
        else:
            self.statusProcessBar.setFormat(string._('Downloading...')+"(%v/" + "%d)" % len(self.fileList))
            self.statusProcessBar.setMaximum(len(self.fileList))

    def startRetry(self):
        if self.retryAfter==0:
            self.retryTimes+=1
            self.retryTimer.stop()
            self.retryList = self.failedList
            self.failedList=[]
            reqs = threadpool.makeRequests(self.startDownload, self.retryList)
            for req in reqs:
                self.DownloadPool.putRequest(req)
            self.statusProcessBar.setFormat(string._('Downloading...') + "(%v/" + "%d)" % len(self.retryList))
            self.statusProcessBar.setMaximum(len(self.retryList))
        else:
            self.retryAfter-=1
            self.signal_setStartBackupBtn.emit(string._('Download will retry after %d sec.') % self.retryAfter, False)

    def appendItemToDownloadList(self,Item):
        self.fileList.append(Item)
        mod = Item['mod']
        if  '/' in mod:
            mod = mod.split('/')[1]
        row_count = self.StatusTable.rowCount()
        self.StatusTable.insertRow(row_count)
        self.StatusTable.setItem(row_count, 0, QTableWidgetItem(Item['name']))
        self.StatusTable.setItem(row_count, 1, QTableWidgetItem(Item['path']))
        self.StatusTable.setItem(row_count, 2, QTableWidgetItem(QIcon(':img/mod.%s.svg'%mod),Item['mod']))
        self.StatusTable.setItem(row_count, 3, QTableWidgetItem('等待中...'))

    def startDownload(self,idx):
        if idx < len(self.fileList):
            self.btn_StartBackup.setText(string._('Downloading...(%d/%d)')%(idx,len(self.fileList)))
            if self.retryTimes != 0:
                self.btn_StartBackup.setText(string._('Downloading...(%d/%d)') % (idx, len(self.retryList)))
            self.signal_processbar_value.emit(idx)
            self.print(string._('Start to download %dth file')%(idx+1))
            self.web.DownloadFile(idx, self.fileList[idx])
            time.sleep(0.5)

    def StartBackup(self):
        self.fileList=[]
        self.StatusTable.setRowCount(0)
        self.statusProcessBar.setFormat(string._('Loading file list')+"(%v" +"/%d)" % self.CourseTreeListRoot.childCount())
        self.statusProcessBar.setMaximum(self.CourseTreeListRoot.childCount())
        self.showFileList()

    def showInformation(self):
        QMessageBox.about(self, string._('About'), string._('tool Information')%self.version)

    def TestiLearnConnection(self):
        self.statusbar.showMessage(string._('Testing connection with iLearn2...'))
        self.label_iLearn.setText(string._('Connecting...'))
        if self.web.TestConnection():   # ==Ture
            self.statusbar.showMessage(string._('Connect to iLearn2 success!'))
            self.label_iLearn.setText(string._('Connect success!'))
        else:
            self.statusbar.showMessage(string._('Can not connect to iLearn2!'))
            self.label_iLearn.setText(string._('Connect failed!'))

    def readSetting(self):
        try:
            self.config.read('setting.ini',encoding='utf-8')
            OPTION = self.config.get('User', 'userealfilename')
            OPTION = self.config.get('User', 'language')
            OPTION = self.config.get('User', 'retrytimes')
            OPTION = self.config.get('User', 'secondbetweenretry')
            OPTION = self.config.get('dev', 'nid')
            OPTION = self.config.get('dev', 'pass')
            OPTION = self.config.get('dev', 'showloadtime')
        except:
            self.config['User']={}
            self.config['User']['userealfilename']='False'
            self.config['User']['language'] = '繁體中文'
            self.config['dev']={}
            self.config['dev']['nid']=''
            self.config['dev']['pass']=''
            self.config['dev']['autologin']='False'
            self.config['dev']['showloadtime']='False'
            self.config['User']['retrytimes'] = '3'
            self.config['User']['secondbetweenretry'] = '5'
            with open('setting.ini','w',encoding='utf-8') as configfile:
                self.config.write(configfile)

    def restart(self):
        system('start iLearnBackupTool')
        self.close()

class DevOptionWindow(QWidget):
    signal_restart = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon(':img/Settings_Icon.png'))
        self.resize(300, 200)
        self.setWindowTitle(string._('Developer options'))
        self.vbox = QVBoxLayout()

        hbox_nid = QHBoxLayout()
        hbox_nid.addWidget(QLabel(string._('NID:')))
        self.inp_nid = QLineEdit()
        hbox_nid.addWidget(self.inp_nid)
        self.vbox.addLayout(hbox_nid)

        hbox_pass = QHBoxLayout()
        hbox_pass.addWidget(QLabel(string._('Password:')))
        self.inp_pass = QLineEdit()
        self.inp_pass.setEchoMode(QLineEdit.Password)
        hbox_pass.addWidget(self.inp_pass)
        self.vbox.addLayout(hbox_pass)

        self.autoLogin = QCheckBox(string._('Auto login'))
        self.vbox.addWidget(self.autoLogin)
        self.showTime = QCheckBox(string._('Show load time'))
        self.vbox.addWidget(self.showTime)
        btn_saveButton = QPushButton(string._('Save and Restart'))
        btn_saveButton.clicked[bool].connect(self.write)
        hbox2 = QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(btn_saveButton)
        hbox2.addStretch(1)

        self.vbox.addLayout(hbox2)
        self.setLayout(self.vbox)
        self.config = ConfigParser()


    def handle_show(self):
        if self.isVisible()==False:
            self.readSetting()
            self.show()

    def readSetting(self):
        self.config.read('setting.ini',encoding='utf-8')
        self.inp_nid.setText(self.config['dev']['nid'])
        self.inp_pass.setText(self.config['dev']['pass'])
        self.autoLogin.setChecked(self.config['dev'].getboolean('autologin'))
        self.showTime.setChecked(self.config['dev'].getboolean('showloadtime'))

    def write(self):
        self.config['dev']['nid'] = self.inp_nid.text()
        self.config['dev']['pass'] = self.inp_pass.text()
        self.config['dev']['autologin'] = str(self.autoLogin.isChecked())
        self.config['dev']['showloadtime'] = str(self.showTime.isChecked())
        with open('setting.ini', 'w',encoding='utf-8') as configfile:
            self.config.write(configfile)
        self.signal_restart.emit()
        self.close()

    def closeWindow(self):
        self.close()

class UserOptionWindow(QWidget):
    signal_restart = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon(':img/Settings_Icon.png'))
        self.config = ConfigParser()
        self.resize(300, 200)
        self.setWindowTitle(string._('Preferences'))
        main_vbox = QVBoxLayout()

        btn_saveButton = QPushButton(string._('Save and Restart'))
        btn_saveButton.clicked[bool].connect(self.write)
        save_hbox = QHBoxLayout()
        save_hbox.addStretch(1)
        save_hbox.addWidget(btn_saveButton)
        save_hbox.addStretch(1)

        main_vbox.addWidget(self.createNormalSettingGroup())
        main_vbox.addWidget(self.createReDownloadSettingGroup())
        main_vbox.addWidget(QLabel(string._('New setting will be use on restart.')))
        main_vbox.addLayout(save_hbox)
        main_vbox.addStretch(1)
        self.setLayout(main_vbox)

    def createNormalSettingGroup(self):
        groupBox = QGroupBox(string._('General setting'))
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.addItem("繁體中文")
        self.combo.addItem("English")
        self.combo.activated[str].connect(self.setLanguage)
        hbox.addWidget(QLabel(string._('Language')))
        hbox.addWidget(self.combo)
        vbox.addLayout(hbox)
        self.useRealFileName = QCheckBox(string._('Show original file name in recource list.'))
        vbox.addWidget(self.useRealFileName)
        vbox.addWidget(QLabel(string._('      *This setting will cause load resouce very slow,\n       please be careful.')))
        groupBox.setLayout(vbox)
        return groupBox

    def createReDownloadSettingGroup(self):
        groupBox = QGroupBox(string._('Retry setting'))
        vbox = QVBoxLayout()
        self.inp_redownload_times = QLineEdit()
        self.inp_redownload_time_between = QLineEdit()

        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel(string._('Retry times:')))
        hbox1.addWidget(self.inp_redownload_times)
        hbox1.setStretch(0,5)
        hbox1.setStretch(1,5)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel(string._('Second between retry:')))
        hbox2.addWidget(self.inp_redownload_time_between)
        hbox2.setStretch(0, 5)
        hbox2.setStretch(1, 5)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        groupBox.setLayout(vbox)
        return groupBox

    def handle_show(self):
        if self.isVisible()==False:
            self.readSetting()
            self.show()

    def readSetting(self):
        self.config.read('setting.ini',encoding='utf-8')
        index = self.combo.findText(self.config['User']['language'], QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.combo.setCurrentIndex(index)
        self.useRealFileName.setChecked(self.config['User'].getboolean('userealfilename'))
        self.inp_redownload_time_between.setText(self.config['User']['secondbetweenretry'])
        self.inp_redownload_times.setText(self.config['User']['retrytimes'])

    def setLanguage(self,lan):
        self.config['User']['language']=lan

    def write(self):
        self.config['User']['userealfilename'] = str(self.useRealFileName.isChecked())
        with open('setting.ini', 'w',encoding='utf-8') as configfile:
            self.config.write(configfile)
        self.signal_restart.emit()
        self.close()

    def closeWindow(self):
        self.close()

if __name__ == '__main__':

    app = QApplication(sys.argv)

    UserOption = UserOptionWindow()
    DevOption = DevOptionWindow()
    Updater = UpdaterGUI()
    mainGUI = myGUI()

    mainGUI.signal_showUserOptionWindow.connect(UserOption.handle_show)
    mainGUI.signal_close.connect(UserOption.closeWindow)
    mainGUI.signal_showDevOptionWindow.connect(DevOption.handle_show)
    mainGUI.signal_close.connect(DevOption.closeWindow)
    mainGUI.signal_close.connect(Updater.closeWindow)
    mainGUI.signal_startUpdate.connect(Updater.startDownload)
    UserOption.signal_restart.connect(mainGUI.restart)


    sys.exit(app.exec_())