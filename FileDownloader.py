from os import makedirs, path  # 匯入系統路徑模組
from bs4 import BeautifulSoup  # 匯入網頁分析模組
import img_qr  # 匯入圖片
from PyQt5 import QtCore  # 匯入Qt5\核心
from configparser import ConfigParser
import json
import language


class BasicDownloader(QtCore.QThread):  # 定義BasicDownloader(需繼承Qt控件才能發出訊號要求更改介面)
    signal_processBar = QtCore.pyqtSignal(float)  # 定義修改進度條之訊號
    signal_downloadNextFile = QtCore.pyqtSignal()  # 定義呼叫下載下一個檔案之訊號(回呼iLearnManager用的)
    signal_finishDownload = QtCore.pyqtSignal()  # 定義下載完成顯示"完成"之訊號
    signal_errorMsg = QtCore.pyqtSignal(str)  # 定義下載時發生例外時發出的訊號
    signal_printMsg = QtCore.pyqtSignal(str)  # 定義下載時發生例外時發出的訊號
    signal_setStatusProcessBar = QtCore.pyqtSignal(int, int)  # 定義修改進度條之訊號(index,value)
    signal_setStatusBarText = QtCore.pyqtSignal(str)
    signal_startDownlooad = QtCore.pyqtSignal()

    def __init__(self):  # 定義建構子
        super().__init__()  # 初始化父類別
        self.signal_processBar.connect(self.ChangeProcessBarValue)  # 將收到"修改進度條"之訊號時的動作綁定副程式
        self.signal_finishDownload.connect(self.FinishDownload)  # 將收到"下載完成"之訊號時的動作綁定副程式
        self.signal_errorMsg.connect(self.showError)  # 將收到"有錯誤發生時"之訊號時的動作綁定副程式
        self.string = language.string()  # 建立語言檔
        self.signal_startDownlooad.connect(self.startDownloadSpeedTimer)  # 將開始更新下載速率的信號連接到更新的副程式
        self.speedCountTimer = QtCore.QTimer()  # 建立定時更新下載速率的計時器
        self.speedCountTimer.timeout.connect(self.showSpeed)  # 設定計時器對應的副函式
        self.DownloadReady = 0  # 設定已下載之區塊數
        self.lastSpeedDownload = 0  # 設定上次更新時的區塊數
        self.ms = 500  # 設定更新下載速度的頻率(ms)

    def setLanguage(self, lan):  # 設定語言的副程式
        self.string.setLanguage(lan)  # 設定語言

    def startDownloadSpeedTimer(self):  # 開始下載速率定時器的副程式
        self.speedCountTimer.start(self.ms)  # 開始計時器

    def setInformation(self, session, Fileinfo, index, host):  # 設定資料
        self.host = host  # 設定moodle主機網址
        self.session = session  # 由呼叫者傳入session連結
        self.Fileinfo = Fileinfo  # 傳入要下載的檔案資料
        self.idx = index  # 傳入正在下載的檔案編號(用來修改介面使用)
        self.path = ('iLearn/' + self.Fileinfo['path']).rstrip()  # 移除行尾空白
        if not path.exists(self.path):  # == False      # 檢查下載路徑是否存在
            makedirs(self.path)  # 路徑不存在則建立檔案夾
        self.signal_setStatusProcessBar.emit(self.idx, -1)

    def ChangeProcessBarValue(self, now):  # 此副函式用來修改進度條(綁定"修改進度條"之訊號)
        self.signal_setStatusProcessBar.emit(self.idx, int(round(now * 100, 2)))

    def FinishDownload(self):  # 此副函式用來修改進度條(綁定"下載完成"之訊號)
        self.signal_setStatusProcessBar.emit(self.idx, 101)

    def showError(self, Msg):  # 此副函式用來顯示下載失敗之訊息(綁定"有錯誤發生"之訊號)
        self.signal_setStatusProcessBar.emit(self.idx, -2)

    def print(self, Msg):  # 此副函式用來顯示Debug訊息(綁定"printMsg"之訊號)
        self.signal_printMsg.emit(str(Msg))

    def showSpeed(self):  # 計算下載速率
        speed = (self.DownloadReady - self.lastSpeedDownload) * 1024 * 1000 / self.ms  # bytes
        text = "%dbytes/s"  # 單位設定
        if speed > 1024:  # 如果可以晉級Kb/s
            speed /= 1024
            text = "%.2fKb/s"
        if speed > 1024:  # 如果可以晉級Mb/s
            speed /= 1024
            text = "%.2fMb/s"
        self.lastSpeedDownload = self.DownloadReady  # 設定已下載之區塊資料
        self.signal_setStatusBarText.emit(self.string._("Speed: ") + text % speed)  # 透過訊號傳送到前端

    def download(self):
        """
            由於PyQt5繪製GUI之執行緒在主執行緒
            因此實際下載的執行緒必須新開自己的執行緒
            否則會導致主執行緒阻塞而無法修改GUI
            但因新開執行緒需與繪製執行緒溝通
            因此需要利用"訊號(QtCore.pyqtSignal)"來進行通知
        """
        self.HtmlPaser()

    def HtmlPaser(self):  # 此副函式須被重載!
        # 請在這裡重載函式並補上分析代碼
        # 可直接呼叫downladWithRealUrl進行下載
        # 注意Exception!
        pass

    def downloadWithRealUrl(self, url, filename,sendFinishSignal=True):  # 實際下載程式(於新開執行緒進行下載)
        try:
            self.signal_startDownlooad.emit()  # 發送下載開始的訊號
            self.DownloadReady = 0  # 已下載之區塊歸零
            self.lastSpeedDownload = 0  # 已下載之區塊歸零
            url = str(url)  # 設定網址
            headers = {'Accept-Encoding': 'gzip, deflate, br'}  # 加上檔頭
            r = self.session.get(url, headers=headers,
                                 stream=True)  # 獲取檔案(注意:因需將檔案分段下載才能實現進度條, 故request須設定為串流模式stream=True)
            chunk_size = 1024  # 設定每個片段之大小(bytes)
            offset = 0  # 設定當前已下載位元組為0
            try:
                fileSize = int(r.headers['content-length'])  # 從header獲取檔案長度
            except:
                fileSize = 0
            if path.exists(self.path + '/' + filename):  # 判斷這個檔案是否已存在
                if path.getsize(self.path + '/' + filename) == fileSize:  # 判斷檔案是否已下載完成
                    self.speedCountTimer.stop()  # 下載完成要發送停止顯示速率的訊號
                    self.signal_finishDownload.emit()  # 若已下載完成直接發出"下載完成之訊號"
                    return  # 然後離開副程式
                else:  # 如果還沒有下載完成
                    headers['Range'] = 'bytes=%d-' % path.getsize(self.path + '/' + filename)  # 檔頭加上已下載之檔案大小
                    r = self.session.get(url, headers=headers, stream=True)  # 重新發送下載請求
                    offset += path.getsize(self.path + '/' + filename)  # 設定已下載之檔案大小
            with open(self.path + '/' + filename, "ab") as file:  # 開啟要寫入之檔案
                for data in r.iter_content(chunk_size=chunk_size):  # 使用request之iter_content方法迭代串流數據
                    self.DownloadReady += 1  # 已下載之區塊+1
                    file.write(data)  # 將數據寫入檔案
                    offset += len(data)  # 更新已下載之大小
                    if fileSize != 0:  # 如果有檔案總長度
                        self.signal_processBar.emit(offset / fileSize)  # 使用emit函式發出"更新進度條"之訊號
            self.speedCountTimer.stop()  # 下載完要中止計時器
            if sendFinishSignal:
                self.signal_finishDownload.emit()  # 下載完成後發出"下載完成之訊號"
        except Exception as e:
            self.speedCountTimer.stop()  # 發生錯誤時要中止計時器
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s, so download failed...\nException:') % (
                    filename) + str(e))  # 然後將錯誤寫到log


class discuss(BasicDownloader):  # 繼承自BasicDownloader
    def __init__(self):  # 初始化
        super().__init__()  # 初始化父類別

    def HtmlPaser(self):  # 重載HtmlPaser
        try:
            url = self.host + '/mod/forum/discuss.php?d=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            div = html.find('div', {'class': 'posting fullpost'})  # 尋找議題內容
            attachFile = html.find('div', {'class': 'attachments'})  # 尋找附加檔案

            with open(self.path + '/討論區內容.txt', 'w', encoding='utf-8') as file:  # 寫入議題內容
                file.write(div.text)

            if attachFile is not None:  # 如果有附檔
                url = attachFile.a.get('href')  # 獲取連結
                fileName = attachFile.find_all('a')[1].text  # 獲取檔名
                self.downloadWithRealUrl(url, fileName)  # 下載
            else:
                self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (
                    self.path, '討論區內容') + str(e))


class folderResource(BasicDownloader):
    def __init__(self):  # 初始化
        super().__init__()  # 初始化父類別

    def HtmlPaser(self):  # 重載HtmlPaser
        url = self.Fileinfo['mod_id']  # 生成網址
        try:
            self.downloadWithRealUrl(url, self.Fileinfo['name'])  # 下載
        except Exception as e:
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (
                    self.path, self.Fileinfo['name']) + str(e))


class resource(BasicDownloader):
    def __init__(self):  # 初始化
        super().__init__()  # 初始化父類別

    def HtmlPaser(self):  # 重載HtmlPaser
        try:
            url = self.host + '/mod/resource/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            if 'Content-Disposition' in r.headers:
                url = url
                filename = str(r.headers['Content-Disposition']).split('=')[1][1:-1]
            else:
                html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
                try:
                    attachFile = html.find('div', {'class': 'resourceworkaround'})  # 尋找議題內容
                    filename = attachFile.a.text  # 尋找附加檔案
                    url = attachFile.a.get('href')
                except:
                    attachFile = html.iframe  # 尋找議題內容
                    url = attachFile.get('src')
                    filename = url.split('/')[-1]  # 尋找附加檔案
            self.downloadWithRealUrl(url, filename)  # 下載
        except Exception as e:
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (
                    self.path, self.Fileinfo['name']) + str(e))


class url(BasicDownloader):
    def __init__(self):  # 初始化
        super().__init__()  # 初始化父類別

    def HtmlPaser(self):  # 重載HtmlPaser
        try:
            url = self.host + '/mod/url/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            realUrl = html.find('div', {'class': 'urlworkaround'}).a.get('href')  # 尋找網址
            lnk = ConfigParser()  # 設定捷徑參數
            lnk['{000214A0-0000-0000-C000-000000000046}'] = {}
            lnk['{000214A0-0000-0000-C000-000000000046}']['Prop3'] = '19,11'
            lnk['InternetShortcut'] = {}
            lnk['InternetShortcut']['IDList'] = ''
            with open(self.path + '/' + self.Fileinfo['name'] + '.url', mode='w') as f:  # 寫出到檔案
                lnk.write(f)
                f.write('Url = %s\n'%realUrl)
            self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (
                    self.path, self.Fileinfo['name'] + '.url') + str(e))


class assign(BasicDownloader):
    def __init__(self):  # 初始化
        super().__init__()  # 初始化父類別
    def saveTextBox(self,html,path):
        path = self.path+'/'+path
        with open(path,mode='w') as file:
            file.write(html)

    def HtmlPaser(self):  # 重載HtmlPaser
        try:
            url = self.host + '/mod/assign/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            filename = self.Fileinfo['name']
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            assign_content = html.find('div', id='intro').text  # 尋找作業要求
            if not path.exists(self.path + '/' + self.Fileinfo['name'].rstrip()):  # 檢查目錄是否存在
                makedirs(self.path + '/' + self.Fileinfo['name'].rstrip())  # 不存在就建一個
            with open(self.path + '/' + self.Fileinfo['name'].rstrip() + '/作業要求.txt', 'w', encoding='utf-8') as f:
                f.write(assign_content)
            TAGradingLink = html.find('div', {'class': 'gradingsummary'})  # 尋找助教權限
            if TAGradingLink != None:
                StudentSubmit = TAGradingLink.find('tr', {'class': 'r1'}).find('td', {'class': 'cell c1 lastcol'}).text
                if int(StudentSubmit) != 0:
                    realUrl = url + '&action=downloadall'
                    filename = self.Fileinfo['name'].rstrip() + '/所有繳交的作業.zip'
                    self.downloadWithRealUrl(realUrl, filename)  # 下載
                else:
                    self.signal_finishDownload.emit()
            else:
                HasSubmit = html.find('td', {'class': 'submissionstatussubmitted cell c1 lastcol'})
                if HasSubmit != None:
                    box = html.find('div', {'class': 'box boxaligncenter submissionsummarytable'})
                    #print(box)
                    textBox = box.find('div',{'class':'no-overflow'})
                    if textBox != None:
                        filename = self.Fileinfo['name'].rstrip() + '/提交的文字.html'
                        text = str(textBox).replace('\xa0',' ')
                        self.saveTextBox(text, filename)
                    filebox = box.find('div',{'id':'assign_files_tree5c24d28b36dd14'})
                    if filebox != None:
                        #print(filebox)
                        file = box.find('a')
                        realUrl = file.get('href')
                        if 'ilearn2.fcu.edu.tw' in realUrl:
                            filename = self.Fileinfo['name'].rstrip() + '/' + file.text
                            self.downloadWithRealUrl(realUrl, filename,False)  # 下載
                    self.signal_finishDownload.emit()
                else:
                    self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (
                    self.path, filename) + str(e))


class page(BasicDownloader):
    def __init__(self):  # 初始化
        super().__init__()  # 初始化父類別

    def HtmlPaser(self):  # 重載HtmlPaser
        try:
            url = self.host + '/mod/page/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            page = html.find('div', {'role': 'main'})  # 尋找議題內容
            with open(self.path + '/' + self.Fileinfo['name'] + '.txt', mode='w', encoding='utf-8') as f:
                f.write(page.text)
            self.signal_finishDownload.emit()
        except Exception as e:
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (
                    self.path, self.Fileinfo['name'] + '.txt') + str(e))


class videos(BasicDownloader):
    def __init__(self):  # 初始化
        super().__init__()  # 初始化父類別

    def saveUrlLink(self,url,filenmae):
        realUrl = url.replace('%', '%%')  # 尋找網址
        lnk = ConfigParser()  # 設定捷徑參數
        lnk['{000214A0-0000-0000-C000-000000000046}'] = {}
        lnk['{000214A0-0000-0000-C000-000000000046}']['Prop3'] = '19,11'
        lnk['InternetShortcut'] = {}
        lnk['InternetShortcut']['IDList'] = ''
        lnk['InternetShortcut']['URL'] = str(realUrl)
        with open(self.path + '/' + filenmae + '.url', mode='w') as f:  # 寫出到檔案
            lnk.write(f)
        self.signal_finishDownload.emit()

    def HtmlPaser(self):  # 重載HtmlPaser
        try:
            url = self.host + '/mod/videos/view.php?id=' + self.Fileinfo['mod_id']  # 生成網址
            r = self.session.get(url)  # 獲取資料
            html = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup進行分析
            video = html.find('video').source  # 尋找議題內容
            if type(video) != type(None):
                videoSrc = video.get('src')
                videoType = videoSrc.split('/')[-1].split('.')[-1]
                filename = self.Fileinfo['name'] + '.' + videoType
                self.downloadWithRealUrl(videoSrc, filename)
            else:
                JSON = html.find('video').get('data-setup')
                data = json.loads(JSON)
                link = data['sources'][0]['src']
                self.saveUrlLink(link,self.Fileinfo['name'])

        except Exception as e:
            self.signal_errorMsg.emit(
                self.string._('There has some exception when download %s/%s, so download failed...\nException:') % (
                    self.path, self.Fileinfo['name']) + str(e))
