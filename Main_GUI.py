import sys
import subprocess
import requests
import time
import _thread
from threading import Thread
from iLeanManager import iLearnManager
from functools import partial
from os.path import exists
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QMessageBox
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QGroupBox, QHBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QDesktopWidget,QWidget,QTableWidgetItem, QTabWidget, QPlainTextEdit, QAbstractItemView
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QTableWidget,QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
from configparser import ConfigParser
import threadpool
import img_qr


class myGUI(QMainWindow):
    signal_startDownload = QtCore.pyqtSignal()
    signal_loginSuccess = QtCore.pyqtSignal()
    signal_showUserOptionWindow = QtCore.pyqtSignal()
    signal_showDevOptionWindow = QtCore.pyqtSignal()
    signal_close = QtCore.pyqtSignal()
    signal_appenDownloadList = QtCore.pyqtSignal(dict)
    signal_processbar_value = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.config = ConfigParser()
        self.pool = threadpool.ThreadPool(4)
        self.readSetting()
        self.version = 0.1
        self.checkUpdate()
        self.host='https://ilearn2.fcu.edu.tw'
        self.statusbar = self.statusBar()
        self.initUI()
        self.web = iLearnManager(self.host)
        self.init_iLearn()
        self.FileTree={}
        self.fileList=[]
        self.nowLoad = 0
        self.signal_startDownload.connect(self.startDownload)
        self.signal_loginSuccess.connect(self.ShowResource)
        self.signal_appenDownloadList.connect(self.appendItemToDownloadList)
        self.signal_processbar_value.connect(self.setProcessBarValue)
        if self.config['dev'].getboolean('autologin')==True:
            self.btn_login.click()

    def closeEvent(self, event):
        self.signal_close.emit()
        self.close()

    def init_iLearn(self):
        self.web.signal_finishDownload.connect(self.startDownload)
        self.web.signal_Log.connect(self.print)
        t = Thread(target=self.TestiLearnConnection)
        t.run()

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
        self.createMenu()
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
        self.input_NID.setText(self.config['dev']['nid'])
        label_Pass = QLabel("密碼:")
        self.input_Pass = QLineEdit()
        self.input_Pass.setText(self.config['dev']['pass'])
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
        groupBox = QGroupBox("Step 2:選擇要備份的課程資源")

        self.CourseListBox = QVBoxLayout()
        self.CourseListBox.addStretch(1)

        self.CourseTreeList = QTreeWidget()
        self.CourseTreeList.setHeaderHidden(True)
        self.CourseTreeList.setEnabled(False)
        self.CourseTreeList.itemExpanded.connect(self.ExpandCourse)
        self.CourseTreeListRoot = QTreeWidgetItem(self.CourseTreeList)
        self.CourseTreeListRoot.setText(0,"所有課程")
        self.CourseTreeListRoot.setFlags(self.CourseTreeListRoot.flags()|QtCore.Qt.ItemIsTristate|QtCore.Qt.ItemIsUserCheckable)
        self.CourseTreeListRoot.setCheckState(0, QtCore.Qt.Unchecked)

        HLayout = QHBoxLayout()
        HLayout.addWidget(self.CourseTreeList)

        groupBox.setLayout(HLayout)

        return groupBox

    def createMenu(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('檔案')
        closeAct = QAction('關閉程式', self)
        closeAct.triggered.connect(qApp.quit)
        fileMenu.addAction(closeAct)

        optMenu = menubar.addMenu('選項')
        DevOptAct = QAction('開發人員選項',self)
        DevOptAct.triggered.connect(self.showDevOption)
        UserOptionAction = QAction('偏好設定',self)
        UserOptionAction.triggered.connect(self.showUserOption)
        optMenu.addAction(UserOptionAction)
        optMenu.addAction(DevOptAct)

    def showUserOption(self):
        self.signal_showUserOptionWindow.emit()

    def showDevOption(self):
        self.signal_showDevOptionWindow.emit()

    def Login(self):
        t = Thread(target = self.__Login)
        t.run()

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
            child.setText(0,'載入中...')
            child.setCheckState(0, QtCore.Qt.Unchecked)
        self.startBackgroundLoad()

    def ExpandCourse(self,courseItem):
        if courseItem.child(0).text(0)=='載入中...':
            i = 0
            for ele in self.courseList:
                if ele['title'] == courseItem.text(0):
                    break
                else:
                    i += 1
            self.timer = QtCore.QTimer()  # 计时器
            self.timer.timeout.connect(partial(self.ShowFileResource, i, courseItem))
            self.timer.start(10)

    def startBackgroundLoad(self):
        if self.nowLoad<len(self.courseList):
            self.statusProcessBar.setMaximum(len(self.courseList))
            self.statusProcessBar.setFormat('正在載入課程資源(%v/'+'%d)'%(len(self.courseList)))

            reqs = threadpool.makeRequests(self.loadFileTreeBackground, range(len(self.courseList)))
            for req in reqs:
                self.pool.putRequest(req)

    def setProcessBarValue(self,value):
        if value ==self.statusProcessBar.maximum():
            self.btn_StartBackup.setEnabled(True)
            self.statusProcessBar.setFormat('就緒...')
            self.statusProcessBar.setMaximum(100)
            self.statusProcessBar.setValue(0)
            if self.nowLoad==self.CourseTreeListRoot.childCount():
                for i,courseItem in [(i,self.CourseTreeListRoot.child(i)) for i in range(self.CourseTreeListRoot.childCount())]:
                    if courseItem.child(0).text(0)=="載入中...":
                        self.ShowFileResource(i,courseItem)
                self.nowLoad=0
        else:
            self.statusProcessBar.setValue(value)

    def loadFileTreeBackground(self,index):
        if self.courseList[index]['title'] not in self.FileTree:
            FileList = self.web.getCourseFileList(self.courseList[index]
                                                  ,useRealFileName=self.config['User'].getboolean('userealfilename')
                                                  ,showTime=self.config['dev'].getboolean('showloadtime'))
            if self.courseList[index]['title'] not in self.FileTree:
                self.FileTree[self.courseList[index]['title']] = FileList
            self.nowLoad+=1
            self.signal_processbar_value.emit(self.nowLoad)

    def ShowFileResource(self,i,courseItem):
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
            sectionItem.setText(0, '沒有可下載的資源')
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
        self.print('載入課程 %s 花費%.3f秒, 共%d項資源'%(courseItem.text(0),tStop-tStart,totalFiles))

    def showFileList(self):
        backupList = []
        courseIndex = 0
        for courseItem in [self.CourseTreeListRoot.child(i) for i in range(self.CourseTreeListRoot.childCount())]:
            courseIndex += 1
            self.signal_processbar_value.emit(courseIndex)
            courseData = self.FileTree[courseItem.text(0)]
            if courseItem.checkState(0)!=QtCore.Qt.Unchecked:
                for sectionItem in [courseItem.child(i) for i in range(courseItem.childCount())]:
                    sectionItemName = sectionItem.text(0)
                    if sectionItemName=='沒有可下載的資源':
                        continue
                    sectionData = [courseData[i] for i in range(len(courseData)) if courseData[i]['section']==sectionItemName][0]
                    if sectionItem.checkState(0)!=QtCore.Qt.Unchecked:
                        for modItem in [sectionItem.child(i)for i in range(sectionItem.childCount())]:
                            modItemName = modItem.text(0)
                            modData = [sectionData['mods'][i] for i in range(len(sectionData['mods'])) if sectionData['mods'][i]['name']==modItemName][0]
                            if modItem.checkState(0)!=QtCore.Qt.Unchecked:
                                self.print(str(modItem.checkState(0))+'='+(modItem.text(0))+str(modData))
                                if modData['mod']=='forum':
                                    for topicItem in [modItem.child(i) for i in range(modItem.childCount())]:
                                        if topicItem.checkState(0)==QtCore.Qt.Checked:
                                            topicName = topicItem.text(0)
                                            resource = [modData['data'][i]for i in range(len(modData['data'])) if modData['data'][i]['name']==topicName][0]
                                            self.signal_appenDownloadList.emit(resource)
                                elif  modData['mod']in ['resource','url', 'assign', 'page', 'videos']:
                                    if modItem.checkState(0)==QtCore.Qt.Checked:
                                        self.signal_appenDownloadList.emit(modData)
                                elif modData['mod']=='folder':
                                    for fileItem in [modItem.child(i)for i in range(modItem.childCount())]:
                                        if fileItem.checkState(0)==QtCore.Qt.Checked:
                                            fileName = fileItem.text(0)
                                            resource = [modData['data'][i] for i in range(len(modData['data'])) if  modData['data'][i]['name'] == fileName][0]
                                            self.signal_appenDownloadList.emit(resource)
        self.nowDownload = 0
        self.signal_startDownload.emit()

    def appendItemToDownloadList(self,Item):
        self.fileList.append(Item)
        self.btn_StartBackup.setEnabled(False)
        mod = Item['mod']
        if  '/' in mod:
            mod = mod.split('/')[1]
        row_count = self.StatusTable.rowCount()
        self.StatusTable.insertRow(row_count)
        self.StatusTable.setItem(row_count, 0, QTableWidgetItem(Item['name']))
        self.StatusTable.setItem(row_count, 1, QTableWidgetItem(Item['path']))
        self.StatusTable.setItem(row_count, 2, QTableWidgetItem(QIcon(':img/mod.%s.svg'%mod),Item['mod']))
        self.StatusTable.setItem(row_count, 3, QTableWidgetItem('等待中...'))

    def startDownload(self):
        if self.nowDownload < len(self.fileList):
            self.web.DownloadFile(self.StatusTable,self.nowDownload,self.fileList[self.nowDownload])
            self.nowDownload += 1
            self.btn_StartBackup.setText('正在下載...('+str(self.nowDownload)+'/'+str(len(self.fileList))+')')
            self.print('nowDownload='+str(self.nowDownload))

    def StartBackup(self):
        self.statusProcessBar.setFormat("正在獲取檔案清單(%v" +"/%d)" % self.CourseTreeListRoot.childCount())
        self.statusProcessBar.setMaximum(self.CourseTreeListRoot.childCount())
        t=Thread(target=self.showFileList)
        t.run()

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

    def readSetting(self):
        if exists('setting.ini'):
            self.config.read('setting.ini')
        else:
            self.config['User']={}
            self.config['User']['userealfilename']='False'
            self.config['dev']={}
            self.config['dev']['nid']=''
            self.config['dev']['pass']=''
            self.config['dev']['autologin']=''
            self.config['dev']['showloadtime']='False'
            with open('setting.ini','w') as configfile:
                self.config.write(configfile)

class UserOptionWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(200, 200)
        self.setWindowTitle('偏好設定')
        self.vbox = QVBoxLayout()
        self.useRealFileName = QCheckBox('使用原始檔名')
        self.vbox.addWidget(self.useRealFileName)
        self.setLayout(self.vbox)
        self.config = ConfigParser()
        self.readSetting()

    def handle_show(self):
        if self.isVisible()==False:
            self.show()

    def readSetting(self):
        if exists('setting.ini'):
            self.config.read('setting.ini')
        else:
            self.config['User']={}
            self.config['User']['userealfilename']='False'
            self.config['dev']={}
            self.config['dev']['nid']=''
            self.config['dev']['pass']=''
            self.config['dev']['autologin']=''
            self.config['dev']['showloadtime']='False'
            with open('setting.ini','w') as configfile:
                self.config.write(configfile)
        self.useRealFileName.setChecked(self.config['User'].getboolean('userealfilename'))

    def closeEvent(self, QCloseEvent):
        self.config['User']['userealfilename'] =str(self.useRealFileName.isChecked())
        with open('setting.ini','w') as configfile:
            self.config.write(configfile)
        self.close()

class DevOptionWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(300, 200)
        self.setWindowTitle('開發人員選項')
        self.vbox = QVBoxLayout()

        hbox_nid = QHBoxLayout()
        hbox_nid.addWidget(QLabel('NID:'))
        self.inp_nid = QLineEdit()
        hbox_nid.addWidget(self.inp_nid)
        self.vbox.addLayout(hbox_nid)

        hbox_pass = QHBoxLayout()
        hbox_pass.addWidget(QLabel('Pass:'))
        self.inp_pass = QLineEdit()
        hbox_pass.addWidget(self.inp_pass)
        self.vbox.addLayout(hbox_pass)

        self.autoLogin = QCheckBox('自動登入')
        self.vbox.addWidget(self.autoLogin)
        self.showTime = QCheckBox('顯示執行時間')
        self.vbox.addWidget(self.showTime)

        self.setLayout(self.vbox)
        self.config = ConfigParser()
        self.readSetting()

    def handle_show(self):
        if self.isVisible()==False:
            self.show()

    def readSetting(self):
        if exists('setting.ini'):
            self.config.read('setting.ini')
        else:
            self.config['User']={}
            self.config['User']['userealfilename']='False'
            self.config['dev']={}
            self.config['dev']['nid']=''
            self.config['dev']['pass']=''
            self.config['dev']['autologin']='False'
            self.config['dev']['showloadtime']='False'
            with open('setting.ini','w') as configfile:
                self.config.write(configfile)
        self.inp_nid.setText(self.config['dev']['nid'])
        self.inp_pass.setText(self.config['dev']['pass'])
        self.autoLogin.setChecked(self.config['dev'].getboolean('autologin'))
        self.showTime.setChecked(self.config['dev'].getboolean('showloadtime'))

    def closeEvent(self, QCloseEvent):
        self.handle_close()
    def handle_close(self):
        self.config['dev']['nid'] = self.inp_nid.text()
        self.config['dev']['pass'] = self.inp_pass.text()
        self.config['dev']['autologin'] = str(self.autoLogin.isChecked())
        self.config['dev']['showloadtime'] = str(self.showTime.isChecked())
        with open('setting.ini', 'w') as configfile:
            self.config.write(configfile)
        self.close()

class UserOptionWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(300, 200)
        self.setWindowTitle('偏好設定')
        self.vbox = QVBoxLayout()
        self.useRealFileName = QCheckBox('使用原始檔名')
        self.vbox.addWidget(self.useRealFileName)
        self.setLayout(self.vbox)
        self.config = ConfigParser()
        self.readSetting()

    def handle_show(self):
        if self.isVisible()==False:
            self.show()

    def readSetting(self):
        if exists('setting.ini'):
            self.config.read('setting.ini')
        else:
            self.config['User']={}
            self.config['User']['userealfilename']='False'
            self.config['dev']={}
            self.config['dev']['nid']=''
            self.config['dev']['pass']=''
            self.config['dev']['autologin']=''
            self.config['dev']['showloadtime']='False'
            with open('setting.ini','w') as configfile:
                self.config.write(configfile)

    def closeEvent(self, QCloseEvent):
        self.handle_close()

    def handle_close(self):
        self.config['User']['userealfilename'] = str(self.useRealFileName.isChecked())
        with open('setting.ini', 'w') as configfile:
            self.config.write(configfile)
        self.close()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainGUI = myGUI()
    UserOption = UserOptionWindow()
    DevOption = DevOptionWindow()
    mainGUI.signal_showUserOptionWindow.connect(UserOption.handle_show)
    mainGUI.signal_close.connect(UserOption.closeEvent)
    mainGUI.signal_showDevOptionWindow.connect(DevOption.handle_show)
    mainGUI.signal_close.connect(DevOption.closeEvent)

    sys.exit(app.exec_())