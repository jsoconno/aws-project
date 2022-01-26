import boto3
import os

def lambda_handler(event, context):
    # Make the connection to dynamodb
    dynamodb_client = boto3.client('dynamodb')

    # Select the table
    table = os.environ["TABLE_NAME"]

    # Add some data to the table
    insert = dynamodb_client.put_item(
        TableName=table,
        Item={
            "UserId": {"S": "Some User"}
        }
    )

    response = dynamodb_client.scan(
        TableName=table
    )

    return response