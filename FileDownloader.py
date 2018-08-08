from os import makedirs,path,rename          # 匯入系統路徑模組
from bs4 import BeautifulSoup               # 匯入網頁分析模組
import img_qr                               # 匯入圖片
from PyQt5 import QtCore  # 匯入Qt5控件, 核心, gui
from configparser import ConfigParser
import language


class BasicDownloader(QtCore.QThread):              # 定義BasicDownloader(需繼承Qt控件才能發出訊號要求更改介面)
    signal_processBar = QtCore.pyqtSignal(float)    # 定義修改進度條之訊號
    signal_downloadNextFile = QtCore.pyqtSignal()   # 定義呼叫下載下一個檔案之訊號(回呼iLearnManager用的)
    signal_finishDownload = QtCore.pyqtSignal()     # 定義下載完成顯示"完成"之訊號
    signal_errorMsg = QtCore.pyqtSignal(str)        # 定義下載時發生例外時發出的訊號
    signal_setStatusProcessBar = QtCore.pyqtSignal(int, int) #定義修改進度條之訊號(index,value)

    def __init__(self):                       # 定義建構子
        super().__init__()                          # 初始化父類別
        self.signal_processBar.connect(self.ChangeProcessBarValue)  # 將收到"修改進度條"之訊號時的動作綁定副程式
        self.signal_finishDownload.connect(self.FinishDownload)     # 將收到"下載完成"之訊號時的動作綁定副程式
        self.signal_errorMsg.connect(self.showError)                # 將收到"有錯誤發生時"之訊號時的動作綁定副程式

    def setLanguage(self,lan):
        self.string = language.string()
        self.string.setLanguage(lan)

    def setInformation(self, session, Fileinfo, index, host):    # 設定資料
        self.host = host                            # 設定moodle主機網址
        self.session = session                      # 由呼叫者傳入session連結
        self.Fileinfo = Fileinfo                    # 傳入要下載的檔案資料
        self.idx = index                            # 傳入正在下載的檔案編號(用來修改介面使用)
        self.path = ('iLearn/' + self.Fileinfo['path']).rstrip()    # 移除行尾空白
        if not path.exists(self.path):              # == False      # 檢查下載路徑是否存在
            makedirs(self.path)                                     # 路徑不存在則建立檔案夾
        self.signal_setStatusProcessBar.emit(self.idx,-1)

    def ChangeProcessBarValue(self, now):           # 此副函式用來修改進度條(綁定"修改進度條"之訊號)
        self.signal_setStatusProcessBar.emit(self.idx, int(round(now*100,2)))

    def FinishDownload(self):                       # 此副函式用來修改進度條(綁定"下載完成"之訊號)
        self.signal_setStatusProcessBar.emit(self.idx, 101)

    def showError(self,Msg):                                # 此副函式用來顯示下載失敗之訊息(綁定"有錯誤發生"之訊號)
        self.signal_setStatusProcessBar.emit(self.idx, -2)

    def download(self):
        """
            由於PyQt5繪製GUI之執行緒在主執行緒
            因此實際下載的執行緒必須新開自己的執行緒
            否則會導致主執行緒阻塞而無法修改GUI
            但因新開執行緒需與繪製執行緒溝通
            因此需要利用"訊號(QtCore.pyqtSignal)"來進行通知
        """
        self.HtmlPaser()

    def HtmlPaser(self):         # 此副函式須被重載!
        # 請在這裡重載函式並補上分析代碼
        # 可直接呼叫downladWithRealUrl進行下載
        # 注意Exception!
        pass

    def downloadWithRealUrl(self, url, filename):       # 實際下載程式(於新開執行緒進行下載)
        try:
            url = str(url)
            r = self.session.get(url,stream=True)       # 獲取檔案(注意:因需將檔案分段下載才能實現進度條, 故request須設定為串流模式stream=True)
            chunk_size = 1024                           # 設定每個片段之大小(bytes)
            offset=0                                    # 設定當前以下載位元組為0
            fileSize = int(r.headers['content-length'])   # 從header獲取檔案長度
            if path.exists(self.path+'/'+filename):        # 判斷這個檔案是否已存在
                if path.getsize(self.path+'/'+filename)==fileSize:  #   判斷檔案是否已下載完成
                    self.signal_finishDownload.emit()                   # 若已下載完成直接發出"下載完成之訊號"
                    return                                              # 然後離開副程式
            with open(self.path+'/'+filename,"wb") as file:# 開啟要寫入之檔案
                for data in r.iter_content(chunk_size=chunk_size):  # 使用request之iter_content方法迭代串流數據
                    file.write(data)                                    # 將數據寫入檔案
                    offset += len(data)                                 # 更新已下載之大小
                    self.signal_processBar.emit(offset/fileSize)        # 使用emit函式發出"更新進度條"之訊號
            self.signal_finishDownload.emit()             # 下載完成後發出"下載完成之訊號"
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s, so download failed...\nException:')%(filename) + str(e))


class discuss(BasicDownloader):                 # 繼承自BasicDownloader
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        try:
            url = self.host+'/mod/forum/discuss.php?d='+self.Fileinfo['mod_id']     # 生成網址
            r = self.session.get(url)                           # 獲取資料
            html = BeautifulSoup(r.text,'lxml')              # 使用BeautifulSoup進行分析
            div = html.find('div',{'class':'posting fullpost'})     # 尋找議題內容
            attachFile = html.find('div',{'class':'attachments'})   # 尋找附加檔案

            with open(self.path+'/討論區內容.txt','w',encoding='utf-8') as file:     # 寫入議題內容
                file.write(div.text)

            if attachFile is not None:                          # 如果有附檔
                url = attachFile.a.get('href')                  # 獲取連結
                fileName = attachFile.find_all('a')[1].text     # 獲取檔名
                self.downloadWithRealUrl(url,fileName)          # 下載
            else:
                self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s/%s, so download failed...\nException:')% (self.path,'討論區內容') + str(e))


class folderResource(BasicDownloader):
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        url = self.Fileinfo['mod_id']                        # 生成網址
        try:
            self.downloadWithRealUrl(url, self.Fileinfo['name'])          # 下載
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (self.path, self.Fileinfo['name']) + str(e))


class resource(BasicDownloader):
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        try:
            url = self.host+'/mod/resource/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            attachFile = html.find('div', {'class': 'resourceworkaround'})  # 尋找議題內容
            filename = attachFile.a.text  # 尋找附加檔案
            url = attachFile.a.get('href')

            self.downloadWithRealUrl(url,filename)          # 下載
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (self.path, self.Fileinfo['name']) + str(e))


class url(BasicDownloader):
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        try:
            url = self.host+'/mod/url/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            realUrl = html.find('div', {'class': 'urlworkaround'}).a.get('href')  # 尋找議題內容
            lnk = ConfigParser()
            lnk['{000214A0-0000-0000-C000-000000000046}']={}
            lnk['{000214A0-0000-0000-C000-000000000046}']['Prop3']='19,11'
            lnk['InternetShortcut']={}
            lnk['InternetShortcut']['IDList']=''
            lnk['InternetShortcut']['URL']=str(realUrl)
            self.Fileinfo['name']+='.url'
            with open(self.path+'/'+self.Fileinfo['name'],mode='w') as f:
                lnk.write(f)
            self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (self.path, self.Fileinfo['name']) + str(e))


class assign(BasicDownloader):
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        try:
            url = self.host+'/mod/assign/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            filename = self.Fileinfo['name']
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')                     # 使用BeautifulSoup進行分析
            assign_content = html.find('div', id='intro').text          # 尋找助教權限
            if not path.exists(self.path+'/'+self.Fileinfo['name'].rstrip()):
                makedirs(self.path+'/'+self.Fileinfo['name'].rstrip())
            with open(self.path+'/'+self.Fileinfo['name'].rstrip()+'/作業要求.txt','w',encoding='utf-8') as f:
                f.write(assign_content)
            TAGradingLink = html.find('div', {'class': 'gradingsummary'})          # 尋找助教權限
            if TAGradingLink !=None :
                realUrl = url +'&action=downloadall'
                filename = self.Fileinfo['name'].rstrip()+'/所有繳交的作業.zip'
                self.downloadWithRealUrl(realUrl, filename)  # 下載
            else:
                HasSubmit = html.find('td', {'class': 'submissionstatussubmitted cell c1 lastcol'})
                if HasSubmit!=None:
                    box  = html.find('div',{'class':'box boxaligncenter submissionsummarytable'})
                    file = box.find('a')
                    realUrl = file.get('href')
                    filename = self.Fileinfo['name'].rstrip()+'/'+file.text
                    self.downloadWithRealUrl(realUrl, filename)  # 下載
                else:
                    self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (self.path, filename) + str(e))


class page(BasicDownloader):
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        try:
            url = self.host+'/mod/page/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            page = html.find('div', {'role': 'main'})  # 尋找議題內容
            self.Fileinfo['name'] += '.txt'
            with open(self.path+'/'+self.Fileinfo['name'],mode='w',encoding='utf-8') as f:
                f.write(page.text)
            self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (self.path, self.Fileinfo['name']) + str(e))


class videos(BasicDownloader):
    def __init__(self):                         # 初始化
        super().__init__()                      # 初始化父類別

    def HtmlPaser(self):                                    # 重載HtmlPaser
        try:
            url = self.host+'/mod/videos/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            video = html.find('video').source.get('src')  # 尋找議題內容
            videoType = video.split('/')[-1].split('.')[-1]
            filename = self.Fileinfo['name']+'.'+videoType
            self.downloadWithRealUrl(video,filename)
        except Exception as e:
            self.signal_errorMsg.emit(self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (self.path, self.Fileinfo['name']) + str(e))
