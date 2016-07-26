#coding: utf8

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import boto3
from base64 import b64decode
from urlparse import parse_qs
import logging
import json
import requests
import JIRA.JIRAController
from JIRA.JIRAController import *
import Slack.SlackController
from Slack.SlackController import *

ENCRYPTED_EXPECTED_TOKEN = "CiA4znK+VnD9zT5liAMOoAyARL6hBQdNbofq7vv25AEA5BKfAQEBAgB4OM5yvlZw/c0+ZYgDDqAMgES+oQUHTW6H6u779uQBAOQAAAB2MHQGCSqGSIb3DQEHBqBnMGUCAQAwYAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAzUJFKUjzXzjWmKLNoCARCAM1OXKW0FMlDtb7itTIROd3ql+X1fqsCDMgi/aFVvpNvSSpwRvRarsqCGZlw5kH+xupNodQ==" #Enter the base-64 encoded, encrypted Slack command token (CiphertextBlob)

kms = boto3.client('kms')
expected_token = kms.decrypt(CiphertextBlob = b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    req_body = event['body']
    params = parse_qs(req_body)
    token = params['token'][0]
    if token != expected_token:
        logger.error("Request token (%s) does not match exptected", token)
        raise Exception("Invalid request token")

    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    command_text = params['text'][0]
    response_url = params['response_url']
    
    f1 = command_text.find(' => ')
    f2 = command_text.find(' token ')
    
    try:
        
        if f1 == -1 and f2 == -1:
            jira_key = command_text
            jira = getJIRADetails(jira_key)
            
            if jira['key'] != 'Error':
                retJson = buildSlackMessage("Jira Ticket Search", "", Slack.SlackController.JIRA_SEARCH, jira)
            else:
                retJson = buildSlackMessage("Jira Command Error", jira['error'], Slack.SlackController.ERROR, '')
    
        else:
            jira_key = command_text.split(' => ')[0]
            jira_token = command_text.split(' token ')[1]
            jira_status = command_text.split(' => ')[1].split(' token ')[0]
            
            setJIRATransition(jira_key,jira_status,jira_token)
            
            retJson = buildSlackMessage("Jira Ticket Update", jira_key, Slack.SlackController.JIRA_UPDATE, '')
            
    except:
        retJson = buildSlackMessage("Jira Command Error", 'Error on Lambda Function', Slack.SlackController.ERROR, '')
    
    return retJson

#jpost = {
#  "body": "token=jwucuzyOZLQLyKqrdElWulYr&text=NEW-26&command=/simpletest&user_name=testuser&channel_name=testChannel&response_url=http://uhuuu.com.br"
#}

#print (lambda_handler(jpost,context=None))