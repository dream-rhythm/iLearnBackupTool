import os


with open('img.qrc', mode='w') as f:
    f.write('<RCC>\n')
    f.write('<qresource>\n')
    for path,dic,files in os.walk('img'):
        for file in files:
            filePath = path+'/'+file
            s = '<file alias="'
            s += filePath
            s += '">'+filePath+'</file>\n'
            f.write(s)
    f.write('</qresource>\n')
    f.write('</RCC>\n')

os.system('pyrcc5 -o img_qr.py img.qrc')
os.system('pyinstaller --hidden-import=PyQt5.sip -F -w --icon=".\img\Main_Icon.ico" --clean Main_GUI.py ')
#os.system('pyinstaller --hidden-import=PyQt5.sip -F -w --icon=".\img\Main_Icon.ico" --clean Updater_GUI.py ')
# os.system('pyinstaller -F Main_GUI.spec')
os.system('copy dist\Main_GUI.exe iLearnBackupTool.exe')
#os.system('copy dist\\Updater_GUI.exe Updater_GUI.exe')
os.system('rmdir /Q /S dist')
os.system('rmdir /Q /S build')
os.system('rmdir /Q /S __pycache__')
os.system('del /Q img.qrc')
os.system('del /Q Main_GUI.spec')
