### CREATE MODULE
# 1. Create Git repository
# 2. Create Preliminary index.yml
# 3. Start build

import yaml
from yaml import SafeLoader, SafeDumper
import boto3
from boto3.dynamodb.conditions import Key
import os
import json
import sys
import glob
import frontmatter
from frontmatter.default_handlers import BaseHandler
from io import BytesIO
import re

#### Specify table
stage = os.environ['STAGE']
existing_table = boto3.resource('dynamodb').Table(stage + '-contents')
subscription_table = boto3.resource('dynamodb').Table(stage + '-subscriptions')

def delete_module(moduleId, existing_table):
  ### Remove qbits which already exist
  lek = None
  result_items = []
  while True:
    results = None
    if lek:
      results = existing_table.query(
          KeyConditionExpression=Key('moduleId').eq(moduleId),
          ProjectionExpression='contentId',
          ExclusiveStartKey = lek
      )
    else:
      results = existing_table.query(
          KeyConditionExpression=Key('moduleId').eq(moduleId),
          ProjectionExpression='contentId'
      )
    result_items.extend(results['Items'])
    if 'LastEvaluatedKey' in results:
      lek = results['LastEvaluatedKey']
    else:
      break
  result_items
  for each in result_items:
    existing_table.delete_item(Key={'moduleId': moduleId, 'contentId': each['contentId']})
  print('Deleted module ' + moduleId)
  return result_items

def invalidateModule(moduleId):
  print('Invalidate existing subscriptions for ', moduleId)
  subid = 'state_subscription_' + moduleId
  userIds = subscription_table.query(
    KeyConditionExpression=Key('subscriptionId').eq(subid),
    ProjectionExpression='userId',
    IndexName='subscriptionId-userId-index5')['Items']
  userIds = [u['userId']for u in userIds]
  for uid in userIds:
    print('Invalidate user ID', uid)
    subscription_table.update_item(
      Key={
          'userId': uid,
          'subscriptionId': subid
      },
      UpdateExpression="set invalidated=:invalidated",
      ExpressionAttributeValues={
          ":invalidated": True
      },
      ReturnValues="UPDATED_NEW"
    )

moduleId=None
with open('index.yml', 'r') as f:
  module = yaml.load(f, Loader=yaml.BaseLoader)
  moduleId = module['moduleId']
qbit_moduleId = 'qbit-' + moduleId

# Update Root element
module = {}
with open('index.yml', 'r') as f:
  module = yaml.load(f)
  # Adjust prefix of ogImage
  module['ogImage'] = '/'.join(['/assets/courses', module['moduleId'], module['ogImage']])

# Check for existing item
usagePlanPrevious = existing_table.query(
  KeyConditionExpression=Key('moduleId').eq(moduleId) & Key('contentId').eq(moduleId),
  ProjectionExpression='usagePlan')['Items']
if len(usagePlanPrevious) > 0:
  usagePlanPrevious = usagePlanPrevious[0]['usagePlan']
  print('usagePlanPrevious:', usagePlanPrevious)
  print('module[\'usagePlan\']:', module['usagePlan'])
  if usagePlanPrevious != module['usagePlan']:
    invalidateModule(moduleId)
    invalidateModule(qbit_moduleId)

delete_module(moduleId, existing_table)
#delete_module(qbit_moduleId, existing_table)

response = existing_table.put_item(Item = module)

if 'usagePlan' in module and module['usagePlan'] == 'pro':
  product_map_item = {
    'moduleId': module['moduleId'],
    'contentId': module['moduleId'] + '#product_courses-pro',
    'contentType': 'product_courses-pro'
  }
  response = existing_table.put_item(Item = product_map_item)
  product_map_qbit = {
    'moduleId': qbit_moduleId,
    'contentId': qbit_moduleId + '#product_courses-pro',
    'contentType': 'product_courses-pro'
  }
  response = existing_table.put_item(Item = product_map_qbit)
  product_map_item_course = {
    'moduleId': module['moduleId'],
    'contentId': module['moduleId'] + '#product_' + module['moduleId'],
    'contentType': 'product_' + module['moduleId']
  }
  response = existing_table.put_item(Item = product_map_item_course)
  product_map_qbit_course = {
    'moduleId': qbit_moduleId,
    'contentId': qbit_moduleId + '#product_' + module['moduleId'],
    'contentType': 'product_' + module['moduleId']
  }
  response = existing_table.put_item(Item = product_map_qbit_course)

with open('contents.yml', 'r') as f:
  contents = yaml.load(f)
  for item in contents:
    response = existing_table.put_item(Item = item)
    
with open('badge.yml', 'r') as f:
  badges = yaml.load(f)
  for item in badges:
    response = existing_table.put_item(Item = item)

contentfiles = sys.argv[1:]
for cf in contentfiles:
  with open(cf) as f:
    contents = json.load(f)
    for c in contents:
      print(c['contentId'])
      response = existing_table.put_item(Item = c)

#moduleId = os.path.basename(os.getcwd())
#qbitModuleId = "qbit-%s" % (moduleId)
### Use renv
#with open('renv.lock') as f:
#    contents = json.load(f)
#    runtime = 'package-amazonlinux-2018.03-r-' + contents['R']['Version']
#    for p in contents['Packages']:
#      pack = contents['Packages'][p]
#      rep = 'cran'
#      #if 'Repository' in pack:
#      #  rep = pack['Repository'].lower()
#      #elif 'Source' in pack:
#      #  rep = pack['Source'].lower()
#      depTo = runtime + '#' + rep + '#' + pack['Package'] + '-' + pack['Version']
#      depOut = {
#        'contentId': "%s_dependency_%s" % (qbitModuleId, depTo),
#        'contentType': "dependency",
#        'dependencyFrom': qbitModuleId,
#        'dependencyTo': depTo,
#        'moduleId': qbitModuleId
#      }
#      depOut.update(pack)
#      print('Writing ' + depOut['contentId'])
#      existing_table.put_item(depOut)
