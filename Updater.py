import requests
from sys import stdout

durl = 'https://raw.githubusercontent.com/fcu-d0441320/iLearnBackupTool/master/iLearnBackupTool.exe'
with requests.get(durl, stream=True) as dlink, open('iLearnBackupTool.exe', 'wb') as binfile:
    # http error detected
    if dlink.status_code != 200:
        print('http error {code}.'.format(code=dlink.status_code()))
        exit(dlink.status_code)

    # initial download record paramater
    total_size = int(dlink.headers['Content-Length'])
    batch_size = int(total_size / 50)
    recived_size = 0

    # start download
    stdout.write('[{:50s}] {:d}%'.format('', 0))
    stdout.flush()
    # print per. 2% content recived
    for i, content in enumerate(dlink.iter_content(chunk_size=batch_size)):
        stdout.write('\r[{:<50s}] {:d}%'.format('='*i, i*2))
        stdout.flush()
        # update contect has recived
        recived_size += binfile.write(content)
        if recived_size == total_size:
            break
    print('')

print('Update Success.')
