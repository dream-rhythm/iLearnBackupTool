import requests
from os import makedirs,path
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets,QtCore
from threading import Thread

class BasicDownloader(QtCore.QThread):
    signal_processBar = QtCore.pyqtSignal(float)
    signal_finishDownload =  QtCore.pyqtSignal()
    def __init__(self):
        super(BasicDownloader,self).__init__()
        self.ProcessBar = QtWidgets.QProgressBar()
        self.signal_processBar.connect(self.ChangeProcessBarValue)
        self.signal_finishDownload.connect(self.FinishDownload)

    def setInformation(self, session, Fileinfo, StatusTableInfo, index):
        self.session = session
        self.Fileinfo = Fileinfo
        self.StatusTable = StatusTableInfo
        self.idx = index
        if path.exists('iLearn/' + self.Fileinfo['path'])==False:
            makedirs('iLearn/' + self.Fileinfo['path'])
        self.StatusTable.setCellWidget(self.idx, 3, self.ProcessBar)

    def ChangeProcessBarValue(self,now):
        self.ProcessBar.setValue(round(now*100,2))

    def FinishDownload(self):
        self.StatusTable.setCellWidget(self.idx,3,QtWidgets.QLabel('完成!'))

    def download(self):
        url = 'https://ilearn2.fcu.edu.tw/draftfile.php/235323/user/draft/37218845/Ch10_指標.ppt'
        filename = 'Ch10_指標.ppt'
        t = Thread(target=self.downloadWithRealUrl,args=(url,filename))
        t.start()

    def downloadWithRealUrl(self,url,filename):
        r = self.session.get(url,stream=True)
        chunk_size = 1024
        offset=0
        fileSize = int(r.headers['content-length'])
        with open(filename,mode="wb") as file:
            for data in r.iter_content(chunk_size=chunk_size):
                file.write(data)
                offset+=len(data)
                self.signal_processBar.emit(offset/fileSize)
        self.signal_finishDownload.emit()


