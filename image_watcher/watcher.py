import requests
import json

with requests.Session() as session:
    latest = session.get("http://10.160.2.223:5050/build_api/v1/latest?project_id=123&interim=false")
    latest_json = json.loads(latest.text)
    build_number = latest_json["build"]
    model = "FGT_1500D"
    download_url = "https://info.fortinet.com/files/FortiOS/v5.00/images/build" + build_number + "/" + model + "-v5-build" + build_number + "-FORTINET.out"
    download_build_payload = {'download_url': download_url}
    r = session.post("http://10.160.2.223:5050/build_api/v1/builds/builds", data=download_build_payload)
    status = json.loads(r.text)["status"]
    if status == "existed":
        print "no change, do nothing"
    if status == "downloaded":
        print "triggering build for b" + build_number
        t = session.post("http://10.160.2.103:8080/job/upgrade-fortigate-periodical/buildWithParameters?FW_VERSION=" + build_number)
