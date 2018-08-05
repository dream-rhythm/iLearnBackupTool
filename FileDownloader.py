from os import makedirs,path                # 匯入系統路徑模組
from bs4 import BeautifulSoup               # 匯入網頁分析模組
# import img_qr                             # 匯入圖片
from PyQt5 import QtWidgets,QtCore,QtGui    # 匯入Qt5控件, 核心, gui
from PyQt5.QtWidgets import QTableWidgetItem    # 匯入Qt5表格的控件
from threading import Thread                # 匯入多執行緒模組


class BasicDownloader(QtCore.QThread):              # 定義BasicDownloader(需繼承Qt控件才能發出訊號要求更改介面)
    signal_processBar = QtCore.pyqtSignal(float)    # 定義修改進度條之訊號
    signal_downloadNextFile = QtCore.pyqtSignal()   # 定義呼叫下載下一個檔案之訊號(回呼iLearnManager用的)
    signal_finishDownload =  QtCore.pyqtSignal()    # 定義下載完成顯示"完成"之訊號
    signal_errorMsg = QtCore.pyqtSignal(str)        # 定義下載時發生例外時發出的訊號

    def __init__(self):                             # 定義建構子
        super().__init__()                          # 初始化父類別
        self.ProcessBar = QtWidgets.QProgressBar()  # 建立下載進度條
        self.signal_processBar.connect(self.ChangeProcessBarValue)  # 將收到"修改進度條"之訊號時的動作綁定副程式
        self.signal_finishDownload.connect(self.FinishDownload)     # 將收到"下載完成"之訊號時的動作綁定副程式
        self.signal_errorMsg.connect(self.showError)                # 將收到"有錯誤發生時"之訊號時的動作綁定副程式

    def setInformation(self, session, Fileinfo, StatusTableInfo, index):    # 設定資料
        self.session = session                      # 由呼叫者傳入session連結
        self.Fileinfo = Fileinfo                    # 傳入要下載的檔案資料
        self.StatusTable = StatusTableInfo          # 傳入GUI中的下載進度表格(QTableWidget)
        self.idx = index                            # 傳入正在下載的檔案編號(用來修改介面使用)
        self.path = ('iLearn/' + self.Fileinfo['path']).rstrip()    # 移除行尾空白
        if not path.exists(self.path):              # == False      # 檢查下載路徑是否存在
            makedirs(self.path)                                     # 路徑不存在則建立檔案夾
        self.StatusTable.setCellWidget(self.idx, 3, self.ProcessBar)    # 將下載進度條新增到表格中

    def ChangeProcessBarValue(self, now):           # 此副函式用來修改進度條(綁定"修改進度條"之訊號)
        self.ProcessBar.setValue(round(now*100,2))  # 設定進度條

    def FinishDownload(self):                       # 此副函式用來修改進度條(綁定"下載完成"之訊號)
        self.StatusTable.removeCellWidget(self.idx,3)   # 移除進度條之控件
        OkIcon = QtGui.QIcon(":img/FinishDownload.png") # 開啟下載完成之圖案
        item = QTableWidgetItem(OkIcon , "OK")          # 新增顯示OK的元件
        self.StatusTable.setItem(self.idx,3,item)       # 將新元件設定到表格內
        self.signal_downloadNextFile.emit()             # 呼叫iLearnManager進行下一個檔案之下載

    def showError(self):                                # 此副函式用來顯示下載失敗之訊息(綁定"有錯誤發生"之訊號)
        self.StatusTable.removeCellWidget(self.idx,3)   # 移除進度條之控件
        ErrorIcon = QtGui.QIcon(":img/DownloadFailed.png")  # 開啟下載失敗之圖案
        item = QTableWidgetItem(ErrorIcon, '下載失敗')       # 新增顯示失敗的元件
        self.StatusTable.setItem(self.idx, 3, item)           # 將新元件設定到表格內
        self.signal_downloadNextFile.emit()                 # 呼叫iLearnManager進行下一個檔案之下載

    def download(self):
        """
            由於PyQt5繪製GUI之執行緒在主執行緒
            因此實際下載的執行緒必須新開自己的執行緒
            否則會導致主執行緒阻塞而無法修改GUI
            但因新開執行緒需與繪製執行緒溝通
            因此需要利用"訊號(QtCore.pyqtSignal)"來進行通知
        """
        t = Thread(target=self.HtmlPaser)
        t.start()

    def HtmlPaser(self):         # 此副函式須被重載!
        # 請在這裡重載函式並補上分析代碼
        # 可直接呼叫downladWithRealUrl進行下載
        # 注意Exception!
        pass

    def downloadWithRealUrl(self, url, filename):       # 實際下載程式(於新開執行緒進行下載)
        try:
            r = self.session.get(url,stream=True)       # 獲取檔案(注意:因需將檔案分段下載才能實現進度條, 故request須設定為串流模式stream=True)
            chunk_size = 1024                           # 設定每個片段之大小(bytes)
            offset=0                                    # 設定當前以下載位元組為0
            fileSize = int(r.headers['content-length'])     # 從header獲取檔案長度
            if path.exists(self.path+'/'+filename):     # 判斷這個檔案是否已存在
                if path.getsize(self.path+'/'+filename)==fileSize:  #   判斷檔案是否已下載完成
                    self.signal_finishDownload.emit()   # 若已下載完成直接發出"下載完成之訊號"
                    return                              # 然後離開副程式
            with open(self.path+'/'+filename,"wb") as file:         # 開啟要寫入之檔案
                for data in r.iter_content(chunk_size=chunk_size):  # 使用request之iter_content方法迭代串流數據
                    file.write(data)                        # 將數據寫入檔案
                    offset+=len(data)                       # 更新已下載之大小
                    self.signal_processBar.emit(offset/fileSize)    # 使用emit函式發出"更新進度條"之訊號
            self.signal_finishDownload.emit()               # 下載完成後發出"下載完成之訊號"
        except Exception as e:
            self.signal_errorMsg.emit('下載 '+filename+' 時發生錯誤,因此下載失敗!\n'+str(e))


class discuss(BasicDownloader):                 # 繼承自BasicDownloader
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        url = 'https://ilearn2.fcu.edu.tw/mod/forum/discuss.php?d='+self.Fileinfo['mod_id']     # 生成網址
        r = self.session.get(url)                           # 獲取資料
        html = BeautifulSoup(r.text,'html.parser')              # 使用BeautifulSoup進行分析
        div = html.find('div',{'class':'posting fullpost'})     # 尋找議題內容
        attachFile = html.find('div',{'class':'attachments'})   # 尋找附加檔案

        try:
            with open(self.path+'/公佈欄內容.txt','w',encoding='utf-8') as file:     # 寫入議題內容
                file.write(div.text)

            if attachFile is not None:                          # 如果有附檔
                url = attachFile.a.get('href')                  # 獲取連結
                fileName = attachFile.find_all('a')[1].text     # 獲取檔名
                self.downloadWithRealUrl(url,fileName)          # 下載
            else:
                self.signal_finishDownload.emit()
        except Exception as err:
            self.signal_errorMsg.emit('下載 '+self.path+'/公佈欄內容.txt'+'時發生錯誤,因此下載失敗!\n'+str(err))
