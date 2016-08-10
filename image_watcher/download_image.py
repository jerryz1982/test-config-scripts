import requests
import base64
import os

def _download_content(username, password, download_url):
    payload = {
        "name": username,
        "password": password
    }
    with requests.Session() as session:
        try:
            login = session.post("https://info.fortinet.com/session", data=payload)
            # login.cookies.p()
        except Exception, e:
            # "error".p()
            # # login.cookies.p()
            # session.cookies.p()
            pass
        # NOTE the stream=True parameter
        login = session.post("https://info.fortinet.com/login", data=payload)

        content = session.get(download_url, stream=True)
        return content

def _save_content(content, filepath):
    with open(filepath, 'wb') as f:
        index = 0
        for chunk in content.iter_content(chunk_size=1024): 
            index += 1
            # print index
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return filepath

def main(username, password, download_url, save_path):
    content = _download_content(username, password, download_url)

    filename = download_url.split('/')[-1]
    filepath = os.path.join(save_path, filename)

    return _save_content(content, filepath)

if __name__ == '__main__':
    from minitest import *

    with test(main):
        username = "chengji"
        # password = base64.b64encode("")
        password = base64.b64decode("SmNqYzE2MCM=")
        download_url = "https://info.fortinet.com/files/FortiOS/v5.00/images/build1025/md5sum.txt"
        # download_url = "https://info.fortinet.com/files/FortiOS/v5.00/images/build1025/FGR_60D-v5-build1025-FORTINET.out"
        save_path = "/home/dahoo/Downloads"
        main(username, password, download_url, save_path).p()
        pass
