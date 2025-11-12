# aws_secrets.py
import boto3
import json
import os


def load_aws_secrets(secret_name: str, region_name: str = "us-east-2"):
    """
    Load secrets from AWS Secrets Manager without using CLI
    """
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    client = boto3.client(
        "secretsmanager",
        region_name=region_name,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )

    response = client.get_secret_value(SecretId=secret_name)
    secret_data = json.loads(response["SecretString"])
    return secret_data
