#coding: utf8

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import requests
import json
import ConfigParser

#Init of getJIRADetails
def getJIRADetails(key):
    
    try:

        config = ConfigParser.RawConfigParser()
        config.read('.//app.cfg')

        headers = {
            'Authorization': 'Basic ' + config.get('application','TokenJIRA'),
            'Content-Type': 'application/json'
        }

        resp = requests.get(config.get('application','JIRARest') + '/' + key + '?fields=key,summary,status',headers=headers)
        
        return resp.json()         
                    
    except: 
        ret = {'key':'Error','error':'Error on JIRA search'}
        return ret
   
#End of getJIRADetails

#Init of setJIRATransition
def setJIRATransition(jira_key,status,token):

    newTransID = 0

    try:

        config = ConfigParser.RawConfigParser()
        config.read('.//app.cfg')

        headers = {
            'Authorization': 'Basic ' + token,
            'Content-Type': 'application/json'
        }

        resp = requests.get(config.get('application','JIRARest') + '/' + jira_key + '/transitions',headers=headers)
        resp = resp.json() 
        
        for transitionItem in resp['transitions']:
            if transitionItem['to']['name'] == status:
                newTransID = int(transitionItem['id'])

        if status == '':
            return ''

        jpost = {
            'transition':{
                'id':newTransID
            }
        }

        resp = requests.post(config.get('application','JIRARest') + '/' + jira_key + '/transitions',json=jpost,headers=headers)
        
        return resp.json()

    except:
        ret = {'key':'Error','error':'Error on JIRA transition update'}
        return ret

#End of setJIRATransition