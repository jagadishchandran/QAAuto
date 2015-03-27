import requests
import json
from requests.auth import HTTPBasicAuth

class IntegrateJira:

    DEBUG_ON = True
    
    QMetryProject = "eCL_RegressionSuite"

    def update_defect(self, QMetryProject, name, documentation):
        self.DEBUG_ON = False
        url = "http://172.27.186.81:2990/jira/rest/api/2/issue"
        getprojecturl = "http://172.27.186.81:2990/jira/rest/api/2/project/"
        user = "jagadish.chandran"
        passwd = "Christ@123"
        headers = {"content-type": "application/json"}
        getproject = requests.get(getprojecturl,headers=headers, auth=HTTPBasicAuth(user,passwd))
        getproject = getproject.json()
        responselen = len(getproject)
        for i in range(0,responselen):
            if getproject[i]['name'] == QMetryProject:
                projectid = getproject[i]['id']
                print projectid
                break
        payload = 	{
        "fields": 	{
        "project": 	{
        "id": projectid
        },
        "summary": "Testcase name: " + name + "   ***   " + documentation + "***  Got Failed",
        "issuetype": {
        "name": "Bug"
        },
        "assignee": {
        "name": "jagadish.chandran"
        },
        "reporter": {
        "name": "jagadish.chandran"
        },
        "labels": ["automation_defects"]
        }
        }
        r = requests.post(url,data=json.dumps(payload), headers=headers, auth=HTTPBasicAuth(user,passwd))
        print r.json()['key']
        return r.json()['key']
