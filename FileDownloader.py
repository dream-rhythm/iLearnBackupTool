from os import makedirs,path                #匯入系統路徑模組
from bs4 import BeautifulSoup               #匯入網頁分析模組
import img_qr                               #匯入圖片
from PyQt5 import QtWidgets,QtCore,QtGui    #匯入Qt5控件, 核心, gui
from PyQt5.QtWidgets import QTableWidgetItem
from threading import Thread                #匯入多執行緒模組

class BasicDownloader(QtCore.QThread):              #定義BasicDownloader(需繼承Qt控件才能發出訊號要求更改介面)
    signal_processBar = QtCore.pyqtSignal(float)    #定義修改進度條之訊號
    signal_finishDownload =  QtCore.pyqtSignal()    #定義下載完成顯示"完成"之訊號
    def __init__(self):                             #定義建構子
        super().__init__()                          #初始化父類別
        self.ProcessBar = QtWidgets.QProgressBar()  #建立下載進度條
        self.signal_processBar.connect(self.ChangeProcessBarValue)  #將收到"修改進度條"之訊號時的動作綁定副程式
        self.signal_finishDownload.connect(self.FinishDownload)     #將收到"下載完成"之訊號時的動作綁定副程式

    def setInformation(self, session, Fileinfo, StatusTableInfo, index):    #設定資料
        self.session = session                      #由呼叫者傳入session連結
        self.Fileinfo = Fileinfo                    #傳入要下載的檔案資料
        self.StatusTable = StatusTableInfo          #傳入GUI中的下載進度表格(QTableWidget)
        self.idx = index                            #傳入正在下載的檔案編號(用來修改介面使用)
        if path.exists('iLearn/' + self.Fileinfo['path'])==False:   #檢查下載路徑是否存在
            makedirs('iLearn/' + self.Fileinfo['path'])                 #路徑不存在則建立檔案夾
        self.StatusTable.setCellWidget(self.idx, 3, self.ProcessBar) #將下載進度條新增到表格中

    def ChangeProcessBarValue(self,now):            #此副函式用來修改進度條(綁定"修改進度條"之訊號)
        self.ProcessBar.setValue(round(now*100,2))      #設定進度條

    def FinishDownload(self):                       #此副函式用來修改進度條(綁定"下載完成"之訊號)
        self.StatusTable.removeCellWidget(self.idx,3)   #移除進度條之控件
        OkIcon = QtGui.QIcon(":img/FinishDownload.png") #開啟下載完成之圖案
        item = QTableWidgetItem(OkIcon , "OK")          #新增顯示OK的元件
        self.StatusTable.setItem(self.idx,3,item)       #將新元件設定到表格內

    def download(self):         #此副函式須被重載!
        """
                由於PyQt5繪製GUI之執行緒在主執行緒
                因此實際下載的執行緒必須新開自己的執行緒
                否則會導致主執行緒阻塞而無法修改GUI
                但因新開執行緒需與繪製執行緒溝通
                因此需要利用"訊號(QtCore.pyqtSignal)"來進行通知
            """
        url = 'https://ilearn2.fcu.edu.tw/draftfile.php/235323/user/draft/817919947/106學年度第一學期計概(三)(四)實習作業 .doc'
        filename = 'test.doc'
        t = Thread(target=self.downloadWithRealUrl,args=(url,filename))
        t.start()

    def downloadWithRealUrl(self,url,filename):     #實際下載程式(於新開執行緒進行下載)
        r = self.session.get(url,stream=True)       #獲取檔案(注意:因需將檔案分段下載才能實現進度條, 故request須設定為串流模式stream=True)
        chunk_size = 1024                           #設定每個片段之大小(bytes)
        offset=0                                    #設定當前以下載位元組為0
        fileSize = int(r.headers['content-length'])   #從header獲取檔案長度
        with open(filename,mode="wb") as file:      #開啟要寫入之檔案
            for data in r.iter_content(chunk_size=chunk_size):  #使用request之iter_content方法迭代串流數據
                file.write(data)                        #將數據寫入檔案
                offset+=len(data)                       #更新已下載之大小
                self.signal_processBar.emit(offset/fileSize)#使用emit函式發出"更新進度條"之訊號
        self.signal_finishDownload.emit()            #下載完成後發出"下載完成之訊號"