import requests
from bs4 import BeautifulSoup
import FileDownloader
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

class iLearnManager(QWidget):
    signal_finishDownload = pyqtSignal()
    def __init__(self):
        super(iLearnManager,self).__init__()
        self.web = requests.Session()
        self.NID = ""
        self.Pass = ""
        self.courseList=[]

    def setInformation(self,host,LogSpace):
        self.host = host
        self.LogSpace = LogSpace

    def print(self,msg):
        self.LogSpace.appendPlainText(msg)

    def TestConnection(self):
        self.print('正在測試與iLearn的連線...')
        page = self.web.get(self.host+"/login/index.php")
        html = BeautifulSoup(page.text, 'lxml')
        form_login = html.find('form', id='login')
        if form_login != None:
            return True
        else:
            return False

    def setUser(self,NID,Password):
        self.NID = NID
        self.Pass = Password

    def Login(self):
        payload = {'username': self.NID, 'password': self.Pass}
        page = self.web.post(self.host+'/login/index.php', data=payload)
        html = BeautifulSoup(page.text, 'lxml')
        img_userpicture = html.find('img', {'class':'userpicture'})
        if img_userpicture != None:
            userName = img_userpicture.get('title').split(' ')[1][:-3]
            return True,userName
        else:
            return False,''

    def getCourseList(self):
        r = self.web.get(self.host)
        soup = BeautifulSoup(r.text, 'lxml')
        div_course = soup.find_all('div', {"style": "font-size:1.1em;font-weight:bold;line-height:20px;"})
        CourseList = [div.a.attrs for div in div_course if 'class' not in div.a.attrs]
        for ele in CourseList:
            ele['id'] = ele['href'][-5:]
            del ele['href']
        self.courseList = CourseList
        return CourseList

    def getCourseMainResourceList(self,classInfo):
        r = self.web.get(self.host+'/course/view.php?id=' + classInfo['id'])
        soup = BeautifulSoup(r.text, 'lxml')
        div_section = soup.find_all('li', {"class": "section main clearfix"})
        ResourceList = []
        for section in div_section:
            section_name = section.find_all('h3', {'class': 'sectionname'})[0].text
            try:
                UrlList = section.contents[2].ul.contents
            except:
                UrlList=[]
            for url in UrlList:
                try:
                    url = url.find_all('a')[0]
                    href = url.get('href')
                    mod = url.get('href').split('/mod/')[1].split('/view')[0]
                    mod_id = url.get('href').split('?id=')[1].split('"')[0]
                    mod_name = url.find_all('span', {'class': 'instancename'})[0]
                    if mod_name.span != None:
                        mod_name.span.decompose()
                    mod_name = mod_name.text
                    path = classInfo['title'] + '/' + self.removeIllageWord(section_name)
                    ResourceList.append({'path': path, 'mod': mod, 'mod_id': mod_id, 'name': self.removeIllageWord(mod_name)})
                except:
                    pass
        return ResourceList

    def removeIllageWord(self,string):
        for ele in '/\\*|?:"':
            while ele in string:
                string = string.replace(ele,'-')
        while '<' in string:
            string = string.replace(ele,'(')
        while '>' in string:
            string = string.replace(ele,')')
        return string

    def getCourseFileList(self,classInfo):
        MainResourceList = self.getCourseMainResourceList(classInfo)
        FileList=[]
        for recource in MainResourceList:
            if recource['mod']=='forum':
                FileList.extend(self.getFileList_forum(recource))
            elif recource['mod'] in ['url','resource','assign','page','videos']:
                FileList.append(recource)
            elif recource['mod']=='folder':
                FileList.extend(self.getFileList_folder(recource))
            else:
                print('Not support',recource['mod'],'mod:',recource['name'])
        return FileList

    def getFileList_forum(self,info):
        FileList = []
        r = self.web.get('https://ilearn2.fcu.edu.tw/mod/forum/view.php?id=' + info['mod_id'])
        soup = BeautifulSoup(r.text, 'lxml')
        allTopic = soup.find_all('td', {'class': 'topic starter'})
        for topic in allTopic:
            path = info['path'] + '/' + self.removeIllageWord(topic.text)
            mod = 'forum/discuss'
            mod_id = topic.a.get('href').split('d=')[1]
            name = self.removeIllageWord(topic.text)
            FileList.append({'path': path, 'mod': mod, 'mod_id': mod_id, 'name': name})
        return FileList

    def getFileList_folder(self,info):
        return []

    def DownloadFile(self,StatusTable,index,fileInfo):
        downloader = FileDownloader.BasicDownloader()
        downloader.setInformation(self.web, fileInfo, StatusTable, index)
        downloader.signal_finishDownload.connect(self.finishDownload)
        downloader.download()

    def finishDownload(self):
        self.signal_finishDownload.emit()