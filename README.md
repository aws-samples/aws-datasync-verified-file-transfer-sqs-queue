## aws-datasync-verified-file-transfer-sqs-queue

This sample code deploys a solution that will take an existing AWS DataSync task, set it up to generate file level logging, and
deploy an AWS Lambda function that will parse the file level logging in the CloudWatch logs, generate the source data path, and
populate an Amazon SQS queue with a list of successfully transferred files.  The source path of the file will also be attached to
the S3 object as custome metadata.

Prerequisites:
Download the contents of this GitHub repository. In the root directory, run the “makeZip.sh” script to create two zip files: datasync_log.zip 
and datasync_log_prep.zip.  Place these two zip files and the datasynclog.yml CloudFormation template into an S3 bucket in your environment.  
Ensure that the user deploying the solution has access to the bucket containing these files.  Note the name of the S3 bucket, as it will be an 
input parameter for the CloudFormation template.

Ensure that you have a DataSync task created that has a destination type of “Amazon S3 bucket”.  Note the Task ID for the task that you wish to 
use for this solution, as it will be an input parameter for the CloudFormation template.  The stack deployment will fail with an error if the target 
location is not an S3 bucket.  

For more information on deploying and running the solution, refer to the blog post here:
<insert blog post when published>

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

