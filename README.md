# iLearnBackupTool


![](http://nicky.lionfree.net/iLearnBackupTool/iLearnBackupTool.PNG)

## 簡介
    這是一個逢甲大學線上教學平台(iLearn)的備份工具
    同學們可以使用他將平台上的教學資源備份到自己的電腦中
    由於moodle模組非常多且複雜
    因此目前僅簡單支援以下模組
1.   ![](http://nicky.lionfree.net/iLearnBackupTool/img/mod.discuss.svg)討論區
2.   ![](http://nicky.lionfree.net/iLearnBackupTool/img/mod.assign.svg)作業(支援學生及助教權限)
3.   ![](http://nicky.lionfree.net/iLearnBackupTool/img/mod.folder.svg)資料夾
4.   ![](http://nicky.lionfree.net/iLearnBackupTool/img/mod.page.svg)頁面
5.   ![](http://nicky.lionfree.net/iLearnBackupTool/img/mod.resource.svg)檔案
6.   <img src='http://nicky.lionfree.net/iLearnBackupTool/img/mod.videos.svg' width='25px'>影片
7.   ![](http://nicky.lionfree.net/iLearnBackupTool/img/mod.url.svg)連結

## 使用方法
包含兩種
* 一般使用者([影片請點我](https://www.youtube.com/watch?v=Jnds3ZruPoI))
    1. 下載[iLearnBackupTool.exe](https://github.com/fcu-d0441320/iLearnBackupTool/raw/master/iLearnBackupTool.exe)
    2. 雙點開啟程式
    3. 使用自己的NID進行登入
    4. 等待加載完成後，選擇想要備份的資料
    5. 按開始備份
    6. 打個球聊個天回家收割成果ヽ(✿ﾟ▽ﾟ)ノ
* 程式開發者
    1. Clone 整個專案
    2. 安裝相關套件
    3. 執行Main_GUI.py
    5. 使用自己的NID進行登入
    6. 等待加載完成後，選擇想要備份的資料
    7. 按開始備份
    8. 打個球聊個天回家收割成果ヽ(✿ﾟ▽ﾟ)ノ
    
## 版本資訊
* v1.2:
    1. 修正因iLearn加入loginToken及SSL加密導致無法連線的問題
    2. 修正因部分課程找不到資源而導致程式凍結的bug
    3. 修正URL模組中若連結帶有%字符會導致python無法解析的問題
    4. 修正因作業繳交文字中存在鏈結導致誤判為檔案的問題
    5. 新增支援作業為免提交檔案，只有文字之支援
* v1.1:
    1. 修正有助教權限的作業頁面，若尚未有人繳交作業會出現錯誤'content-length'
    2. 修正開發人員選項中，儲存按鈕失效問題
    3. 更新system函式為Popen以避免出現小黑窗的問題
    4. 將斷點續傳功能進度條更改為接續上次進度而非本次下載進度
* v1.0:
    1. 爬取iLearn頁面並下載資源
    2. 自動檢查更新
    3. iLearn資源斷點續傳功能
    4. 失敗列表自動重試功能(可在選項->偏好設定內調整)

## Bug&想做但尚未實做的功能
> Bug
>> 1. Learn伺服器拒絕下載時，會導致下載失敗('content-length')
>> 
> 想做但尚未實做的功能
>> 1. 測驗卷
>> 2. 巢狀資料夾
>> 3. 備份成網頁模板(php)
>> 4. 備份已對學生關閉，但仍具助教權限可存取之課程
> 無法實作的功能
>> 1.因iLearn權限問題，無法下載已關閉之課程資源

## 開發環境與套件
* Windows 10
* PyCharm
* Python 3.6.6 x86版本
* PyQt5
* Pyinstller-dev
* BeautifulSoup
* lxml
* requests
* threadpool
```shell
pip install PyQt5
pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
pip install BeautifulSoup
pip install lxml
pip install requests
pip install threadpool
```
## 教學資源
* [PyQt5中文教程](https://maicss.gitbooks.io/pyqt5/content/)
* [【Python】將Python打包成exe檔](https://medium.com/pyladies-taiwan/python-%E5%B0%87python%E6%89%93%E5%8C%85%E6%88%90exe%E6%AA%94-32a4bacbe351)
* [Qt官方文件](https://doc.qt.io/qt-5.11/classes.html)
* [莫煩PYTHON](https://morvanzhou.github.io/tutorials/data-manipulation/scraping/)
* [PyQt5实现下载进度条](https://blog.csdn.net/rain_of_mind/article/details/79989715)
* [用pyinstaller打包PyQt5程序](http://www.drelang.cn/2017/05/18/%E7%94%A8pyinstall%E6%89%93%E5%8C%85PyQt5%E7%A8%8B%E5%BA%8F/)

## 踩雷小記
1. PyInstaller 編譯完成後出現無法找到資源包
    因為正式版的PyInstaller尚未支援PyQt5
    把branch從master更改成devlop即可
    ```shell
    pip uninstall PyInstaller
    pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
    ```
2. PyInstaller 編譯完成後視窗閃退
    先確認是否帶有 -w參數(隱藏cmd窗口)
    若有此參數且程序內含有stdin,stdout則程式會無法運行
    
3. 編譯出的exe檔無法在x86及win7上運行
    需要將整個Python環境改成32位元再編譯即可
    ```shell
    安裝:
    set CONDA_FORCE_32BIT=1
    conda create -n py36_32 python=3.6
    啟用:
    activate py36_32
    關閉
    deactivate py36_32
    ```
4. PyInstaller 編譯完無法載入圖片資源
    先將圖片建立一個資源清單img.qrc
    格式如下
    ```xml
    <RCC>
        <qresource>
            <file alias=file1.png>file1.png</file>
            <file alias=file2.png>file2.png</file>
        </qresource>
    </RCC>
    ```
    接著呼叫pyrcc5將資源編譯為.py檔
    ```shell
    pyrcc5 -o img_qr.py img.qrc
    ```
    最後在檔案內import img_qr
    並將程式碼的原始路徑前加一個冒號即可
    ```python
        import img_qr
        #QIcon("img/DownloadFailed.png") #改成下面那句
        QIcon(":img/DownloadFailed.png")
    ```
5. QWidget can not set parent錯誤
    確認所有QWidget的操作皆再主線程運行
    修改的變數則由singal傳送到主線程修改
    
## 開發小記
**2018/08/05**
- all.py     : 試圖符合pep8，以下建議沒有被修正
    1. pep8建議變數與函式名稱使用C style命名，class變數沒有在init宣告...
        基於習慣沒有更動
    2. 涉及程式結構者~~看不懂的~~，Ex. might reference before assign
    3. 奇怪的BUG(cannot find referenced)，明明就可以跑...

**2018/08/03**
- Updater.py : 加上進度條
- README.md  : 0803進度

**2018/08/02**
- Updater.py : 完成基本功能
- .gitignore : 其實如果可以的話我很想刪掉remote repository上面的.idea/
- README.md  : 我會在這邊寫我改了啥XD

## 作者
*  夢之旋律  (陳琮斌)
*  Aimerfan (簡瑞梓)

## 版權聲明
iLearnBackupTool 版權所有 (C) 2018 Dream_Rhythm, Aimerfan 

本程式是自由軟體，您可以遵照自由軟體基金會 ( Free Software Foundation ) 出版的 GNU 通用公共許可證條款 ( GNU General Public License ) 第三版來修改和重新發佈這一程式，或者自由選擇使用任何更新的版本。

發佈這一程式的目的是希望它有用，但沒有任何擔保。甚至沒有適合特定目的而隱含的擔保。更詳細的情況請參閱 GNU 通用公共許可證。
