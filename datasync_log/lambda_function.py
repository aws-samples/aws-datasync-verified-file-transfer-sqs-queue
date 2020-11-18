import gzip
import json
import base64
import re
import boto3
import os


sqs_queue = os.environ['SQS_QUEUE']
task_id = os.environ['TASK_ID']

s3 = boto3.resource('s3')
sqs = boto3.client('sqs')
ds = boto3.client('datasync')

def lambda_handler(event, context):
    # Capture and convert the cloudwatch logs into text
    cw_data = event['awslogs']['data']
    compressed_payload = base64.b64decode(cw_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    payload = json.loads(uncompressed_payload)
    log_events = payload['logEvents']
    
    # Use the task to identify source and target locations
    allTasks = ds.list_tasks()
    for tasks in allTasks['Tasks']:
        if re.search(r'.*\/(.*)',tasks['TaskArn']).group(1) == task_id:
            taskARN = tasks['TaskArn']
    taskInfo = ds.describe_task(TaskArn=taskARN)
    sourceARN = taskInfo['SourceLocationArn']
    targetARN = taskInfo['DestinationLocationArn']
    allLocations = ds.list_locations()
    for locs in allLocations['Locations']:
        if locs['LocationArn'] == sourceARN:
            source_loc = locs['LocationUri'].rstrip('/')
        if locs['LocationArn'] == targetARN:
            full_target = locs['LocationUri'][5:]
            targetElements = full_target.split('/',1)
            target_loc = targetElements[0]
            prefix = targetElements[1]

    # For each each log event (corresponding to "Verified file" entries in CW Logs), create source path and attach to S3 object as metadata, and add path to queue
    for log_event in log_events:
        fileEvent = log_event['message']
        regexp = re.compile(r'(\/.*)+\,')
        m = regexp.search(fileEvent)
        fileLoc = m.group().rstrip('\,')
        source = source_loc+fileLoc
        key = prefix + fileLoc[1:]
        # Add source path as user metadata on S3 object
        s3_object = s3.Object(target_loc, key)
        s3_object.metadata.update({'source-path':source})
        s3_object.copy_from(CopySource={'Bucket':target_loc, 'Key':key}, Metadata=s3_object.metadata, MetadataDirective='REPLACE')
        # Add source path to queue
        sqs.send_message(QueueUrl=sqs_queue,MessageBody=source)
