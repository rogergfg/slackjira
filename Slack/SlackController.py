#coding: utf8

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import boto3
import json
import ConfigParser

JIRA_SEARCH = 1
JIRA_UPDATE = 2
ERROR = 3

#Init of buildSlackMessage
def buildSlackMessage(title, message, slackCmd, data):
    try:

        config = ConfigParser.RawConfigParser()
        config.read('.//app.cfg')

        LinkJIRA = config.get('application','LinkJIRA')

        if slackCmd == JIRA_SEARCH:
            retJson = {
                "text": "*" + title + "*",
                "attachments": [
                    {
                        "text": "JIRA Ticket: <" + LinkJIRA + "%s|%s> \n JIRA Status: %s \n JIRA Description: %s " % (data['key'], data['key'], data['fields']['status']['name'], data['fields']['summary'])
                    }
                ]
            }
            
        elif slackCmd == JIRA_UPDATE: 
            retJson = {
                "text": "*" + title + "*",
                "attachments": [
                    {
                        "text": "JIRA Ticket: <" + LinkJIRA + "%s|%s> \n\n Operation: Updated Successfully! " % (message,message)
                    }
                ]
            }
        elif slackCmd == ERROR:
            retJson = {
                "text": "*" + title + "*",
                "attachments": [
                    {
                        "text": "Unable to provide the information! \n Please, review your Slash Command and Try Again! \n Operation: %s " % (message)
                    }
                ]
            }
            
        return retJson
    except:
        ret = {'key':'Error','error':'Error on Slack Message'}
        return ret
#End of buildSlackMessage