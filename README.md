# AmazonInspectorLambdaFindingProcessor
This script is designed to run in AWS Lambda and will not work elsewhere.

When properly configured, the script receives findings (JSON-formatted security issue notifications) from the Amazon Inspector service in AWS, via SNS, and then formats and forwards them to a destination email address of your choice.

You MUST change the value of DEST_EMAIL_ADDR in line 13, or the script will not work.

The script and necessary configuration are described in the following blog post:
https://aws.amazon.com/blogs/aws/scale-your-security-vulnerability-testing-with-amazon-inspector
