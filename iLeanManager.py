import requests
from bs4 import BeautifulSoup
class iLearnManager():
    def __init__(self,host):
        self.web = requests.Session()
        self.host = host
        self.NID = ""
        self.Pass = ""
        self.courseList=[]

    def TestConnection(self):
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
            UrlList = section.contents[2].ul.contents
            for url in UrlList:
                url = url.find_all('a')[0]
                href = url.get('href')
                mod = url.get('href').split('/mod/')[1].split('/view')[0]
                mod_id = url.get('href').split('?id=')[1].split('"')[0]
                mod_name = url.find_all('span', {'class': 'instancename'})[0]
                if mod_name.span != None:
                    mod_name.span.decompose()
                mod_name = mod_name.text
                path = classInfo['title'] + '/' + section_name + '/' + mod_name
                ResourceList.append({'path': path, 'mod': mod, 'mod_id': mod_id, 'name': mod_name})
        return ResourceList

    def getCourseFileList(self,classInfo):
        MainResourceList = self.getCourseMainResourceList(classInfo)

        pass