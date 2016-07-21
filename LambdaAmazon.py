#coding: utf8
'''
This function handles a Slack slash command and echoes the details back to the user.

Follow these steps to configure the slash command in Slack:

  1. Navigate to https://<your-team-domain>.slack.com/services/new

  2. Search for and select "Slash Commands".

  3. Enter a name for your command and click "Add Slash Command Integration".

  4. Copy the token string from the integration settings and use it in the next section.

  5. After you complete this blueprint, enter the provided API endpoint URL in the URL field.


Follow these steps to encrypt your Slack token for use in this function:

  1. Create a KMS key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html.

  2. Encrypt the token using the AWS CLI.
     $ aws kms encrypt --key-id alias/<KMS key name> --plaintext "<COMMAND_TOKEN>"

  3. Copy the base-64 encoded, encrypted key (CiphertextBlob) to the kmsEncyptedToken variable.

  4. Give your function's role permission for the kms:Decrypt action.
     Example:
       {
         "Version": "2012-10-17",
         "Statement": [
           {
             "Effect": "Allow",
             "Action": [
               "kms:Decrypt"
             ],
             "Resource": [
               "<your KMS key ARN>"
             ]
           }
         ]
       }

Follow these steps to complete the configuration of your command API endpoint

  1. When completing the blueprint configuration select "POST" for method and
     "Open" for security on the Endpoint Configuration page.

  2. After completing the function creation, open the newly created API in the
     API Gateway console.

  3. Add a mapping template for the application/x-www-form-urlencoded content type with the
     following body: { "body": $input.json("$") }

  4. Deploy the API to the prod stage.

  5. Update the URL for your Slack slash command with the invocation URL for the
     created API resource in the prod stage.
'''

import boto3
from base64 import b64decode
from urlparse import parse_qs
import logging
import urllib2
import sys
import json
import threading;

ENCRYPTED_EXPECTED_TOKEN = "" # Enter the base-64 encoded, encrypted Slack command token (CiphertextBlob)
TokenJIRA = "" # Enter the JIRA token generated by username and password
JIRARest = "" # Enter your JIRA Rest API link https://xxxxxxxx.jira.com/rest/api/2/issue
JIRA_SEARCH = 1
JIRA_UPDATE = 2
ERROR = 3

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
                retJson = buildSlackMessage("Jira Ticket Search", "", JIRA_SEARCH, jira)
            else:
                retJson = buildSlackMessage("Jira Command Error", jira['error'], ERROR, '')
    
        else:
            jira_key = command_text.split(' => ')[0]
            jira_token = command_text.split(' token ')[1]
            jira_status = command_text.split(' => ')[1].split(' token ')[0]
            
            setJIRATransition(jira_key,jira_status,jira_token)
            
            retJson = buildSlackMessage("Jira Ticket Update", jira_key, JIRA_UPDATE, '')
            
    except:
        retJson = buildSlackMessage("Jira Command Error", 'Error on Lambda Function', ERROR, '')
    
    return retJson

#Init of getJIRADetails
def getJIRADetails(key):
    
    try:

        headers = {
            'Authorization': 'Basic ' + TokenJIRA,
            'Content-Type': 'application/json'
        }

        req = urllib2.Request(JIRARest + '/' + key + '?fields=key,summary,status',headers=headers)
        resp = urllib2.urlopen(req).read()
        resp = str(resp)
        resp = json.loads(resp)

        urllib2.urlopen(req).close()
        
        return resp         
                    
    except: 
        ret = {'key':'Error','error':'Error on JIRA search'}
        return ret
   
#End of getJIRADetails

#Init of setJIRATransition
def setJIRATransition(jira_key,status,token):

    newTransID = 0

    try:

        headers = {
            'Authorization': 'Basic ' + token,
            'Content-Type': 'application/json'
        }

        req = urllib2.Request(JIRARest + '/' + jira_key + '/transitions',headers=headers)
        resp = urllib2.urlopen(req).read()
        resp = str(resp)
        resp = json.loads(resp)

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

        urllib2.urlopen(req).close()

        req = urllib2.Request(JIRARest + '/' + jira_key + '/transitions',headers=headers)
        req.add_data(json.dumps(jpost))

        resp = urllib2.urlopen(req).read()
        
        return resp

    except:
        ret = {'key':'Error','error':'Error on JIRA transition update'}
        return ret

#End of setJIRATransition    

#Init of buildSlackMessage
def buildSlackMessage(title, message, slackCmd, data):
    try:
        if slackCmd == JIRA_SEARCH:
            retJson = {
                "text": "*" + title + "*",
                "attachments": [
                    {
                        "text": "JIRA Ticket: %s \n JIRA Status: %s \n JIRA Description: %s " % (data['key'], data['fields']['status']['name'], data['fields']['summary'])
                    }
                ]
            }
            
        if slackCmd == JIRA_UPDATE: 
            retJson = {
                "text": "*" + title + "*",
                "attachments": [
                    {
                        "text": "JIRA Ticket: %s \n\n Operation: Updated Successfully! " % (message)
                    }
                ]
            }
        if slackCmd == ERROR:
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