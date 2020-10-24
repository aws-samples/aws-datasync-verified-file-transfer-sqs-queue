import json
import os
import re
import boto3
import logging
from crhelper import CfnResource
from urllib.parse import urlparse

task_id = os.environ['TASK_ID']
log_grp = os.environ['LOG_GROUP_ARN']
lambdaFunction = os.environ['LAMBDA_FUNCTION']
region = os.environ['REGION']
account = os.environ['ACCOUNT']
lambda_role = os.environ['LAMBDA_ROLE']
ds = boto3.client('datasync')
logs = boto3.client('logs')
lam = boto3.client('lambda')
iam = boto3.client('iam')
principal = "logs."+region+".amazonaws.com"
helper = CfnResource()
logger = logging.getLogger(__name__)

def testLocation(testLoc):
    listLocations = ds.list_locations()
    allLocations = listLocations['Locations']
    myLoc = next((item for item in allLocations if item['LocationArn'] == testLoc), False)
    if 'myLoc' in locals():
        if not myLoc['LocationUri'].startswith('s3'):
            raise ValueError("The destination location is not an S3 bucket. This solution can only be deployed for AWS DataSync tasks that have a destination location that is an S3 bucket.")
        else:
            print("Destination Location is S3 Bucket.  Updating lambda access role...")
            bucketParts = urlparse(myLoc['LocationUri'], allow_fragments=False)
            bucketArn = "arn:aws:s3:::"+bucketParts.netloc
            bucketPath = "arn:aws:s3:::"+bucketParts.netloc+"/*"
            bucketPolicy = '{"Version":"2012-10-17","Statement":{"Effect":"Allow","Action":["s3:ListBucket","s3:GetBucketLocation","s3:ListBucketMultipartUploads"],"Resource":"'+bucketArn+'"}}'
            objectPolicy = '{"Version":"2012-10-17","Statement":{"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:GetObjectAcl","s3:PutObjectAcl"],"Resource":"'+bucketPath+'"}}'
            iam.put_role_policy(RoleName=lambda_role,PolicyName="BucketActions",PolicyDocument=bucketPolicy)
            iam.put_role_policy(RoleName=lambda_role,PolicyName="ObjectActions",PolicyDocument=objectPolicy)

@helper.create
@helper.update
def datasynclogprep(event,context):
        logger.info("Got Create/Update")
        # Get TaskARN from Task ID
        allTasks = ds.list_tasks()
        for tasks in allTasks['Tasks']:
            if re.search(r'.*\/(.*)',tasks['TaskArn']).group(1) == task_id:
                taskARN = tasks['TaskArn']
        
        # Check that target is S3, otherwise exit   
        taskInfo = ds.describe_task(TaskArn=taskARN)
        destLocArn = taskInfo['DestinationLocationArn']
        testLocation(destLocArn)

        # Add permission for Cloudwatch Logs to call Lambda
        lam.add_permission(FunctionName=lambdaFunction,StatementId='datasynccwlambda',Action='lambda:InvokeFunction',Principal=principal,SourceArn=log_grp,SourceAccount=account)
        
        # Update the Task to add logging
        log_group = log_grp.rstrip(r':*')
        ds.update_task(TaskArn=taskARN,Options={'LogLevel':'TRANSFER'}, CloudWatchLogGroupArn=log_group)
        logs.put_resource_policy(policyName='trustDataSyncEvents',policyDocument='{ "Statement": [ {"Sid": "DataSyncLogsToCloudWatchLogs", "Effect": "Allow", "Action": ["logs:PutLogEvents"], "Principal": { "Service": "datasync.amazonaws.com" }, "Resource": "'+log_grp+'" } ], "Version": "2012-10-17"}')
        logs.put_resource_policy(policyName='trustDataSyncStream',policyDocument='{ "Statement": [ {"Sid": "DataSyncLogsToCloudWatchLogs", "Effect": "Allow", "Action": ["logs:CreateLogStream"], "Principal": { "Service": "datasync.amazonaws.com" }, "Resource": "'+log_group+'" } ], "Version": "2012-10-17"}')

@helper.delete
def delete(event,context):
    logger.info("Got Delete")
    iam.delete_role_policy(RoleName=lambda_role,PolicyName="BucketActions")
    iam.delete_role_policy(RoleName=lambda_role,PolicyName="ObjectActions")
    
def lambda_handler(event, context):
    helper(event,context)
