class string:
    def __init__(self):
        self.zh_tw_Strings = {'Download file %d finish!': '第 %d 個檔案下載完成!',
                              'Start Backup':'開始備份',
                              'Download Falied':'下載失敗',
                              'iLearn Backup Tool':'iLearn備份工具',
                              'Starting Backup Tool...':'備份工具啟動中...',
                              'Ready...':'就緒...',
                              'File name':'檔案名稱',
                              'Path':'儲存路徑',
                              'iLearn mod':'iLearn模組',
                              'Download status':'下載進度',
                              'Backup status':'備份狀態',
                              'Log':'日誌',
                              'Step 1: Login':'Step 1:登入iLearn',
                              'NID:':'帳號:',
                              'Password:':'密碼:',
                              'Clean':'清除',
                              'Login':'登入',
                              'iLearn status:':'iLearn狀態:',
                              'Step 3:Select save option':'Step 3:選擇儲存類型',
                              'Save as file':'儲存成檔案',
                              'Save as web page':'儲存成網頁',
                              'Step 2:Select sourse resource to backup':'Step 2:選擇要備份的課程資源',
                              'All course':'所有課程',
                              'File':'檔案',
                              'Quit':'關閉程式',
                              'Option':'選項',
                              'Developer options':'開發人員選項',
                              'Preferences':'偏好設定',
                              'Help':'幫助',
                              'Check update':'檢查更新',
                              'About':'關於',
                              'User %s is signing in...':'使用者 %s 登入中...',
                              'Sign in success':'登入成功',
                              '%s sign in sucess':'%s 已成功登入',
                              'Sign in failed':'登入失敗',
                              'Loading...':'載入中...',
                              'Loding course resource':'正在載入課程資源',
                              'There has no resource to download.':'沒有可下載的資源',
                              'Load course %s in %.3f sec, total has %d resource(s)':'載入課程 %s 花費%.3f秒, 共%d項資源',
                              'Load page %s  in %.3f sec.':'開啟%s頁面花費 %.3f 秒',
                              'Load discuss page %s  in %.3f sec.':'開啟討論區 %s頁面花費 %.3f 秒',
                              'Load resource page %s  in %.3f sec.':'開啟資源 %s頁面花費 %.3f 秒',
                              'Load folder page %s  in %.3f sec.':'開啟資夾 %s頁面花費 %.3f 秒',
                              'Find unsupport mod ':'發現不支援的課程模組 ',
                              'There has some exception when download %s, so download failed...\nException:':'下載 %s 時發生錯誤,因此下載失敗...\n例外:',
                              'There has some exception when download %s/%s, so download failed...\nException:':'下載 %s/%s 時發生錯誤,因此下載失敗...\n例外:',
                              'Downloading...':'正在下載...',
                              'Downloading...(%d/%d)':'正在下載...(%d/%d)',
                              'Start to download %dth file':'開始下載第 %d 個檔案',
                              'Loading file list':'正在獲取檔案清單',
                              'tool Information':'iLearn備份工具\n工具版本：%.1f\n開發者:夢o旋律(陳琮斌),Aimerfan(簡瑞梓)',
                              'Testing connection with iLearn2...':'正在測試iLearn2的連線...',
                              'Connecting...':'連線中...',
                              'Connect to iLearn2 success!':'iLearn2連線成功!',
                              'Connect success!':'連線成功!',
                              'Can not connect to iLearn2!':'iLearn2連線失敗!',
                              'Connect failed!':'連線失敗!',
                              'Auto login':'自動登入',
                              'Show load time':'顯示執行時間',
                              'Language':'語言設定',
                              'Show original file name in recource list.':'在資源選單中使用原始檔名',
                              '      *This setting will cause load resouce very slow,\n       please be careful.':'      *此設定會使得載入變得相當緩慢甚至卡死\n       請謹慎使用',
                              'New setting will be use on restart.':'設定將於重啟後生效',
                              'Open Folder':'開啟下載資料夾',
                              'Save and Restart':'儲存並重新啟動',
                              "Success:%d\nFailed:%d":"成功:%d\n失敗:%d",
                              "Download finish!":"下載完成!"
                     }
        self.English_Strings={'tool Information':'iLearn Backup Tool\nTool version：%.1f\nDeveloper:夢o旋律(陳琮斌),Aimerfan(簡瑞梓)'}
        self.LANGUAGE = '繁體中文'

    def setLanguage(self,lan):
        self.LANGUAGE = lan

    def _(self,s):
        if self.LANGUAGE == '繁體中文':
            return self.zh_tw_Strings[s]
        if self.LANGUAGE == 'English':
            if s in self.English_Strings:
                return self.English_Strings[s]
            else:
                return s
        else:
            return s