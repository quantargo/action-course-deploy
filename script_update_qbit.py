import boto3
from boto3.dynamodb.conditions import Key
import os
import json

#### UPDATE CONTENTS IN DDB
stage = os.environ['STAGE']
existing_table = boto3.resource('dynamodb').Table(stage + '-contents')
cf = 'qbit_meta.json'

moduleId=None
with open(cf) as f:
    contents = json.load(f)
    moduleId = contents[0]['moduleId']

### Remove items which already exist
results = existing_table.query(
    KeyConditionExpression=Key('moduleId').eq(moduleId),
    ProjectionExpression='contentId'
)
with existing_table.batch_writer() as batch:
  for each in results['Items']:
      batch.delete_item(Key={'moduleId': moduleId, 'contentId': each['contentId']})

## Upload content items
with open(cf) as f:
    contents = json.load(f)
    for c in contents:
      print(c['contentId'])
      response = existing_table.put_item(Item = c)
