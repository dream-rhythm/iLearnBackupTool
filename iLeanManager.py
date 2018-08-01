import requests
from bs4 import BeautifulSoup
class iLearnManager():
    def __init__(self):
        self.web = requests.Session()
        self.NID = ""
        self.Pass = ""
        self.courseList=[]

    def TestConnection(self):
        page = self.web.get("https://ilearn2.fcu.edu.tw/login/index.php")
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
        page = self.web.post('https://ilearn2.fcu.edu.tw/login/index.php', data=payload)
        html = BeautifulSoup(page.text, 'lxml')
        img_userpicture = html.find('img', {'class':'userpicture'})
        if img_userpicture != None:
            userName = img_userpicture.get('title').split(' ')[1][:-3]
            return True,userName
        else:
            return False,''

    def getCourseList(self):
        r = self.web.get("http://ilearn2.fcu.edu.tw/")
        soup = BeautifulSoup(r.text, 'lxml')
        div_course = soup.find_all('div', {"style": "font-size:1.1em;font-weight:bold;line-height:20px;"})
        CourseList = [div.a.attrs for div in div_course if 'class' not in div.a.attrs]
        for ele in CourseList:
            ele['id'] = ele['href'][-5:]
            del ele['href']
        self.courseList = CourseList
        return CourseList