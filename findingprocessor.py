from __future__ import print_function
import boto3
import json
import datetime

sns = boto3.client('sns')
inspector = boto3.client('inspector')

# SNS topic - will be created if it does not already exist
SNS_TOPIC = "Inspector-Finding-Delivery"

# Destination email - will be subscribed to the SNS topic if not already
DEST_EMAIL_ADDR = "changeme@example.com"

# quick function to handle datetime serialization problems
enco = lambda obj: (
    obj.isoformat()
    if isinstance(obj, datetime.datetime)
    or isinstance(obj, datetime.date)
    else None
)

def lambda_handler(event, context):

    # extract the message that Inspector sent via SNS
    message = event['Records'][0]['Sns']['Message']

    # get inspector notification type
    notificationType = json.loads(message)['event']

    # skip everything except report_finding notifications
    if notificationType != "FINDING_REPORTED":
        print('Skipping notification that is not a new finding: ' + notificationType)
        return 1
    
    # extract finding ARN
    findingArn = json.loads(message)['finding']

    # get finding and extract detail
    response = inspector.describe_findings(findingArns = [ findingArn ], locale='EN_US')
    print(response)
    finding = response['findings'][0]
    
    # skip uninteresting findings
    title = finding['title']
    if title == "Unsupported Operating System or Version":
        print('Skipping finding: ', title)
        return 1
        
    if title == "No potential security issues found":
        print('Skipping finding: ', title)
        return 1
    
    # get the information to send via email
    subject = title[:100] # truncate @ 100 chars, SNS subject limit
    messageBody = "Title:\n" + title + "\n\nDescription:\n" + finding['description'] + "\n\nRecommendation:\n" + finding['recommendation']
    
    # un-comment the following line to dump the entire finding as raw json
    # messageBody = json.dumps(finding, default=enco, indent=2)

    # create SNS topic if necessary
    response = sns.create_topic(Name = SNS_TOPIC)
    snsTopicArn = response['TopicArn']

    # check to see if the subscription already exists
    subscribed = False
    response = sns.list_subscriptions_by_topic( TopicArn = snsTopicArn )

    nextPageToken = ""
    
    # iterate through subscriptions array in paginated list API call
    while True:
        response = sns.list_subscriptions_by_topic(
            TopicArn = snsTopicArn,
            NextToken = nextPageToken
            )

        for subscription in response['Subscriptions']:
            if ( subscription['Endpoint'] == DEST_EMAIL_ADDR ):
                subscribed = True
                break
        
        if 'NextToken' not in response:
            break
        else:
            nextPageToken = response['NextToken']
       
        
    # create subscription if necessary
    if ( subscribed == False ):
        response = sns.subscribe(
            TopicArn = snsTopicArn,
            Protocol = 'email',
            Endpoint = DEST_EMAIL_ADDR
            )

    # publish notification to topic
    response = sns.publish(
        TopicArn = snsTopicArn,
        Message = messageBody,
        Subject = subject
        )

    return 0
