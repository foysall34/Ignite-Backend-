# pinecone_helper.py
import os
import boto3
import json
from pinecone import Pinecone
from botocore.exceptions import NoCredentialsError, ClientError


def load_aws_secrets(secret_name: str, region_name: str = "us-east-2"):
    """Fetch secret data from AWS Secrets Manager"""
    try:
        client = boto3.client(
            "secretsmanager",
            region_name=region_name,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        response = client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response["SecretString"])
        return secret_data

    except NoCredentialsError:
        print("AWS credentials not found. Please check your .env file.")
        return None
    except ClientError as e:
        print(f" AWS Secrets Manager error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while loading secrets: {e}")
        return None


def get_pinecone_client(secret_name: str = "prod/senses", region_name: str = "us-east-2"):
    """
    Fetch Pinecone API key from AWS and return an initialized Pinecone client.
    Handles all errors gracefully.
    """
    secrets = load_aws_secrets(secret_name, region_name)
    if not secrets:
        print(" Could not load secrets from AWS.")
        return None

    pinecone_key = secrets.get("PINECONE_API_KEY") or secrets.get("pinecone_api_key")
    if not pinecone_key:
        print(" Pinecone API key missing in AWS Secret JSON.")
        return None

    try:
        # Create and return Pinecone client
        pc = Pinecone(api_key=pinecone_key)
        print(" Pinecone client initialized successfully!")
        return pc
    except Exception as e:
        print(f"Failed to initialize Pinecone client: {e}")
        return None
