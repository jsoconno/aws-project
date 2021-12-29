import os
import boto3

def lambda_handler(event, context):
    region = os.environ["REGION"]
    bucket = os.environ["BUCKET"]
    name = "file"
    body = "end-to-end success"

    response = upload_file(
        region=region,
        bucket=bucket,
        name=name,
        body=body
    )

    return response

def upload_file(region, bucket, name, body):
    try:
        s3_client = boto3.client('s3', region_name=region)
        response = s3_client.put_object(
            Body=body,
            Bucket=bucket,
            Key=name,
            ServerSideEncryption="aws:kms"
        )
        print(response)
    except Exception as e:
        response = e
        print(response)
    
    return response