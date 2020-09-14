from __future__ import print_function
import boto3
import json
import datetime
from urllib import urlretrieve
from botocore.exceptions import ClientError
import time

sns = boto3.client('sns')
inspector = boto3.client('inspector')
s3 = boto3.client('s3')

# SNS topic - will be created if it does not already exist
SNS_TOPIC = "Inspector-Finding-Delivery"

# assesment report name
reportFileName = "assesmentReport.pdf"

# S3 Bucket Name
BUCKET_NAME="assesmentreport"

# finding results number
max_results = 250000

# list for no. of High severity incidents
high_severities_list = []

# setting up paginator for the listing findings
paginator = inspector.get_paginator('list_findings')

# filter for searching findings
finding_filter = { 'severities': ['High'] }

def upload_file(file_name, bucket, object_name=None):
    
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def lambda_handler(event, context):
    
    # extract the message that Inspector sent via SNS
    message = event['Records'][0]['Sns']['Message']
    
    # get inspector notification type
    notificationType = json.loads(message)['event']
    
    # checking for the event type
    if notificationType == "ASSESSMENT_RUN_COMPLETED":
        
        # getting arn for the assement run
        runArn = json.loads(message)['run']
        
        # generating the report
        while True:
            reportResponse = inspector.get_assessment_report(
            assessmentRunArn=runArn,
            reportFileFormat='PDF',
            reportType='FULL'
            )
            if reportResponse['status'] == 'COMPLETED':
                break
            time.sleep(5)
            
        # downloading the report 
        file_status = urlretrieve(reportResponse['url'],
          '/tmp/' + reportFileName)
        
        # uploading to s3  
        upload_file('/tmp/' + reportFileName,BUCKET_NAME, 
          runArn.split(":")[5] + "/" + reportFileName)
        
        # getting the findings for the run Arn
        for findings in paginator.paginate(
        maxResults=max_results,
        assessmentRunArns=[
            runArn,
        ],
        filter = finding_filter):
            for finding_arn in findings['findingArns']:
                high_severities_list.append(finding_arn)
                
        # sending emails if no. of high severity issues are more than 1        
        if len(high_severities_list) > 1:
            
            subject = "There is High Severity Issue in the assement run"
            messageBody = ("High severity issue is reported in assesment run" + runArn + "\n\n" + 
            "Please check the  detailed report here:" +
            "s3://" + BUCKET_NAME + "/" + runArn.split(":")[5] + "/" + reportFileName)

            # create SNS topic if necessary
            response = sns.create_topic(Name = SNS_TOPIC)
            snsTopicArn = response['TopicArn']


            # publish notification to topic
            response = sns.publish(
                TopicArn = snsTopicArn,
                Message = messageBody,
                Subject = subject
                )

            return 0
        
        return 0
