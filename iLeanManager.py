import requests
from bs4 import BeautifulSoup
import FileDownloader
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
import language
import time

class iLearnManager(QWidget):
    signal_finishDownload = pyqtSignal()
    signal_Log = pyqtSignal(str)
    signal_setStatusProcessBar=pyqtSignal(int,int)
    signal_setStatusBarText = pyqtSignal(str)

    def __init__(self, host='https://ilearn2.fcu.edu.tw',lan='繁體中文'):
        super(iLearnManager,self).__init__()
        self.web = requests.Session()
        self.NID = ""
        self.Pass = ""
        self.courseList = []
        self.host = host
        self.string = language.string()
        self.string.setLanguage(lan)
        self.downloader={"forum/discuss":FileDownloader.discuss(),
                         "folder/resource":FileDownloader.folderResource(),
                         "resource":FileDownloader.resource(),
                         "url":FileDownloader.url(),
                         "page":FileDownloader.page(),
                         "assign":FileDownloader.assign(),
                         "videos":FileDownloader.videos()}
        for ele in self.downloader:
            self.downloader[ele].setLanguage(lan)
            self.downloader[ele].signal_downloadNextFile.connect(self.finishDownload)
            self.downloader[ele].signal_errorMsg.connect(self.showErrorMsg)
            self.downloader[ele].signal_printMsg.connect(self.print)
            self.downloader[ele].signal_setStatusProcessBar.connect(self.setStatusProcessBar)
            self.downloader[ele].signal_setStatusBarText.connect(self.setStatusBarText)
    def setStatusBarText(self,s):
        self.signal_setStatusBarText.emit(s)
    def print(self,msg):
        self.signal_Log.emit(msg)

    def TestConnection(self):
        self.print(self.string._('Testing connection with iLearn2...'))
        page = self.web.get(self.host+"/login/index.php")
        html = BeautifulSoup(page.text, 'lxml')
        form_login = html.find('form', id='login')
        self.loginToken = html.find('input', {'name':'logintoken'}).attrs['value']

        if form_login is not None:
            return True
        else:
            return False

    def setUser(self, NID, Password):
        self.NID = NID
        self.Pass = Password

    def Login(self):
        payload = {'username': self.NID, 'password': self.Pass,'logintoken':self.loginToken}
        page = self.web.post(self.host+'/login/index.php', data=payload)
        html = BeautifulSoup(page.text, 'lxml')
        img_userpicture = html.find('img', {'class':'userpicture'})
        if img_userpicture is not None:
            userName = img_userpicture.get('title').split(' ')[1][:-3]
            return True, userName
        else:
            return False, ''

    def getCourseList(self,showOldTACourse):
        r = self.web.get(self.host)
        soup = BeautifulSoup(r.text, 'lxml')
        div_course = soup.find_all('div', {"style": "font-size:1.1em;font-weight:bold;line-height:20px;"})
        CourseList = [div.a.attrs for div in div_course if 'class' not in div.a.attrs or showOldTACourse]
        for ele in CourseList:
            ele['id'] = ele['href'][-5:]
            del ele['href']
        self.courseList = CourseList
        return CourseList

    def getCourseMainResourceList(self, classInfo,showTime):
        tStart = time.time()
        r = self.web.get(self.host+'/course/view.php?id=' + classInfo['id'])
        tStop = time.time()
        if showTime:
            self.print(self.string._('Load page %s  in %.3f sec.')%(classInfo['title'],tStop-tStart))
        soup = BeautifulSoup(r.text, 'lxml')
        ResourceList = []
        try:
            div_main = soup.find_all('ul', {"class": "topics"})[0]
            div_section = div_main.find_all('li',{'role':'region'})
            for section in div_section:
                try:
                    section_name = section.find_all('h3', {'class': 'sectionname'})[0].text
                except:
                    section_name = section.get('aria-label')
                try:
                    UrlList = section.contents[2].ul.contents
                except:
                    UrlList = []
                resourceInSection=[]
                for url in UrlList:
                    try:
                        url = url.find_all('a')[0]
                        href = url.get('href')
                        mod = href.split('/mod/')[1].split('/view')[0]
                        mod_id = href.split('?id=')[1].split('"')[0]
                        mod_name = url.find_all('span', {'class': 'instancename'})[0]
                        if mod_name.span is not None:
                            mod_name.span.decompose()
                        mod_name = mod_name.text
                        path = classInfo['title'] + '/' + self.removeIllageWord(section_name)
                        resourceInSection.append({'path': path, 'mod': mod, 'mod_id': mod_id, 'name': self.removeIllageWord(mod_name)})
                    except:
                        pass
                if len(resourceInSection) != 0:
                    ResourceList.append({'name':section_name,'mods':resourceInSection})
        except:
            pass
        return ResourceList

    def removeIllageWord(self, string):
        for ele in '/\\*|?:"':
            while ele in string:
                string = string.replace(ele, '-')
        while '<' in string:
            string = string.replace(ele, '(')
        while '>' in string:
            string = string.replace(ele, ')')
        return string

    def getCourseFileList(self, classInfo,useRealFileName,showTime):
        MainResourceList = self.getCourseMainResourceList(classInfo,showTime)
        FileList=[]
        for section in MainResourceList:
            recourceList = []
            for recource in section['mods']:
                if recource['mod']=='forum':
                    data =self.getFileList_forum(recource,showTime)
                    if data!=None:
                        recource['data']=data
                        recourceList.append(recource)
                elif recource['mod']=='resource':
                    if useRealFileName==True:
                        recource = self.getFileList_resource(recource,showTime)
                    recourceList.append(recource)
                elif recource['mod'] in ['url', 'assign', 'page', 'videos']:
                    recourceList.append(recource)
                elif recource['mod'] == 'folder':
                    data=self.getFileList_folder(recource,showTime)
                    if len(data)!=0:
                        recource['data'] = data
                        recourceList.append(recource)
                else:
                    self.print(self.string._('Find unsupport mod ')+recource['mod']+' mod: '+recource['name'])
            if len(recourceList)!=0:
                FileList.append({'section':section['name'],'mods':recourceList})
        return FileList

    def getFileList_forum(self, info,showTime):
        FileList = []
        tStart = time.time()
        r = self.web.get('https://ilearn2.fcu.edu.tw/mod/forum/view.php?id=' + info['mod_id'])
        tStop = time.time()
        if showTime:
            self.print(self.string._('Load discuss page %s  in %.3f sec.') % (info['name'], tStop - tStart))
        soup = BeautifulSoup(r.text, 'lxml')
        try:
            folderName = soup.find_all('div',{'role': 'main'})[0].h2.text
        except:
            folderName = soup.find('p',{'class':'tree_item leaf hasicon active_tree_node'}).a.text
        allTopic = soup.find_all('td', {'class': 'topic starter'})
        for topic in allTopic:
            path = info['path'] + '/' + folderName + '/ '+self.removeIllageWord(topic.text)
            mod = 'forum/discuss'
            mod_id = topic.a.get('href').split('d=')[1]
            name = self.removeIllageWord(topic.text)
            FileList.append({'path': path, 'mod': mod, 'mod_id': mod_id, 'name': name})
        if len(FileList)==0:
            return None
        else:
            return FileList

    def getFileList_resource(self, info,showTime):
        tStart = time.time()
        r = self.web.get('https://ilearn2.fcu.edu.tw/mod/resource/view.php?id=' + info['mod_id'])
        tStop = time.time()
        if showTime:
            self.print(self.string._('Load resource page %s  in %.3f sec.') % (info['name'], tStop - tStart))
        soup = BeautifulSoup(r.text, 'lxml')
        try:
            filename = soup.find('div',{'class':'resourceworkaround'}).a.text
        except:
            filename = info['name']
        info['name'] = filename
        return info

    def getFileList_folder(self, info,showTime):
        tStart = time.time()
        r = self.web.get('https://ilearn2.fcu.edu.tw/mod/folder/view.php?id=' + info['mod_id'])
        tStop = time.time()
        if showTime:
            self.print(self.string._('Load folder page %s  in %.3f sec.') % (info['name'], tStop - tStart))
        soup = BeautifulSoup(r.text, 'html.parser')
        FileList = []
        try:
            filetable = soup.find_all('span',{'class':'fp-filename-icon'})
        except:
            filetable = []
        for file in filetable:
            try:
               url = file.a.get('href')
               filename = file.find('span',{'class':'fp-filename'}).text
               mod='folder/resource'
               path = info['path']+'/'+info['name']
               FileList.append({'path': path, 'mod': mod, 'name': filename, 'mod_id': url})
            except:
                pass
        return FileList

    def DownloadFile(self,index, fileInfo):
        try:
            self.downloader[fileInfo['mod']].setInformation(self.web, fileInfo, index,self.host)
            self.downloader[fileInfo['mod']].download()
        except Exception as e:
            self.print('error! '+str(e))

    def setStatusProcessBar(self,idx,value):
        self.signal_setStatusProcessBar.emit(idx,value)

    def finishDownload(self):
        self.signal_finishDownload.emit()

    def showErrorMsg(self, Msg):
        self.print(Msg)
