import requests

req = requests.Session()
dlink = req.get('https://github.com/fcu-d0441320/iLearnBackupTool/raw/master/iLearnBackupTool.exe')

if dlink.status_code != 200:
    print('http error {code}.'.format(code=dlink.status_code()))
    exit(1)

with open('iLearnBackupTool.exe', 'wb') as binfile:
    binfile.write(exefile.content)

print('Success')
