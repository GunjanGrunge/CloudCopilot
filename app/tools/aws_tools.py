import boto3
import os
import json
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from ..schemas.base import AWSCredentials
import logging
from botocore.exceptions import ClientError, BotoCoreError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AWSResponse:
    def __init__(self, success: bool, data: Any = None, message: str = None, requires_credentials: bool = False):
        self.success = success
        self.data = data
        self.message = message
        self.requires_credentials = requires_credentials

class AWSTools:
    def __init__(self):
        self.session = None

    def _init_session(self, credentials: Optional[AWSCredentials] = None) -> Union[str, None]:
        """Initialize AWS session with provided credentials"""
        try:
            if credentials:
                self.session = boto3.Session(
                    aws_access_key_id=credentials.accessKeyId,
                    aws_secret_access_key=credentials.secretAccessKey,
                    region_name=credentials.region
                )
                return None
            return "AWS credentials are required for this operation"
        except Exception as e:
            return f"Failed to initialize AWS session: {str(e)}"

    def _get_client(self, service: str, credentials: Optional[AWSCredentials] = None):
        """Get AWS service client with appropriate credentials"""
        error = self._init_session(credentials)
        if error:
            raise Exception(error)
        return self.session.client(service)

    async def get_s3_bucket_sizes(self, credentials: Optional[AWSCredentials] = None) -> AWSResponse:
        """Returns total size of all accessible S3 buckets"""
        if not credentials:
            return AWSResponse(
                success=False,
                message="To list your S3 buckets and their sizes, I'll need your AWS credentials. Please provide them securely.",
                requires_credentials=True
            )

        try:
            s3 = self._get_client('s3', credentials)
            buckets = []
            response = s3.list_buckets()
            
            for bucket in response['Buckets']:
                size = 0
                paginator = s3.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=bucket['Name']):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            size += obj['Size']
                buckets.append({
                    'name': bucket['Name'],
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2)
                })
            
            return AWSResponse(
                success=True,
                data=buckets,
                message=f"Successfully retrieved information for {len(buckets)} bucket(s)"
            )
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidAccessKeyId':
                return AWSResponse(
                    success=False,
                    message="The AWS Access Key ID you provided is invalid. Please check your credentials.",
                    requires_credentials=True
                )
            elif error_code == 'SignatureDoesNotMatch':
                return AWSResponse(
                    success=False,
                    message="The AWS Secret Access Key you provided is invalid. Please check your credentials.",
                    requires_credentials=True
                )
            elif error_code == 'AccessDenied':
                return AWSResponse(
                    success=False,
                    message="Your AWS credentials don't have permission to list S3 buckets. Please check your IAM permissions.",
                    requires_credentials=True
                )
            else:
                return AWSResponse(
                    success=False,
                    message=f"AWS error: {str(e)}",
                    requires_credentials=False
                )
        except Exception as e:
            return AWSResponse(
                success=False,
                message=f"Error getting S3 bucket sizes: {str(e)}",
                requires_credentials=False
            )

    async def list_ec2_instances(self, credentials: Optional[AWSCredentials] = None) -> AWSResponse:
        """Returns list of EC2 instances with their details"""
        if not credentials:
            return AWSResponse(
                success=False,
                message="To list your EC2 instances, I'll need your AWS credentials. Please provide them securely.",
                requires_credentials=True
            )

        try:
            ec2 = self._get_client('ec2', credentials)
            response = ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'id': instance['InstanceId'],
                        'type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'public_ip': instance.get('PublicIpAddress', 'N/A'),
                        'private_ip': instance.get('PrivateIpAddress', 'N/A')
                    })
            
            return AWSResponse(
                success=True,
                data=instances,
                message=f"Successfully retrieved information for {len(instances)} instance(s)"
            )
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']:
                return AWSResponse(
                    success=False,
                    message="Invalid AWS credentials provided. Please check your Access Key ID and Secret Access Key.",
                    requires_credentials=True
                )
            elif error_code == 'AccessDenied':
                return AWSResponse(
                    success=False,
                    message="Your AWS credentials don't have permission to list EC2 instances. Please check your IAM permissions.",
                    requires_credentials=True
                )
            else:
                return AWSResponse(
                    success=False,
                    message=f"AWS error: {str(e)}",
                    requires_credentials=False
                )
        except Exception as e:
            return AWSResponse(
                success=False,
                message=f"Error listing EC2 instances: {str(e)}",
                requires_credentials=False
            )

    async def describe_iam_role(self, role_name: str, credentials: Optional[AWSCredentials] = None) -> AWSResponse:
        if not credentials:
            return AWSResponse(
                success=False,
                message=f"To describe the IAM role '{role_name}', I'll need your AWS credentials. Please provide them securely.",
                requires_credentials=True
            )

        try:
            iam = self._get_client('iam', credentials)
            role = iam.get_role(RoleName=role_name)
            policies = iam.list_attached_role_policies(RoleName=role_name)
            
            return AWSResponse(
                success=True,
                data={
                    'role': role['Role'],
                    'attached_policies': policies['AttachedPolicies']
                },
                message=f"Successfully retrieved details for IAM role '{role_name}'"
            )
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']:
                return AWSResponse(
                    success=False,
                    message="Invalid AWS credentials provided. Please check your Access Key ID and Secret Access Key.",
                    requires_credentials=True
                )
            elif error_code == 'AccessDenied':
                return AWSResponse(
                    success=False,
                    message="Your AWS credentials don't have permission to access IAM roles. Please check your IAM permissions.",
                    requires_credentials=True
                )
            else:
                return AWSResponse(
                    success=False,
                    message=f"AWS error: {str(e)}",
                    requires_credentials=False
                )
        except Exception as e:
            return AWSResponse(
                success=False,
                message=f"Error describing IAM role: {str(e)}",
                requires_credentials=False
            )

    async def get_s3_bucket_file_count(self, bucket_name: str = None, credentials: Optional[AWSCredentials] = None) -> AWSResponse:
        """Returns the number of files in specified S3 bucket, or all buckets if none specified"""
        if not credentials:
            return AWSResponse(
                success=False,
                message="To count files in your S3 buckets, I'll need your AWS credentials. Please provide them securely.",
                requires_credentials=True
            )

        try:
            s3 = self._get_client('s3', credentials)
            bucket_stats = []
            
            try:
                # If no bucket specified, list all buckets
                if not bucket_name:
                    response = s3.list_buckets()
                    buckets = [bucket['Name'] for bucket in response['Buckets']]
                else:
                    buckets = [bucket_name]

                for bucket in buckets:
                    file_count = 0
                    total_size = 0
                    
                    # Use paginator to handle buckets with more than 1000 objects
                    paginator = s3.get_paginator('list_objects_v2')
                    try:
                        for page in paginator.paginate(Bucket=bucket):
                            if 'Contents' in page:
                                file_count += len(page['Contents'])
                                total_size += sum(obj['Size'] for obj in page['Contents'])
                                
                        bucket_stats.append({
                            'bucket_name': bucket,
                            'file_count': file_count,
                            'total_size_bytes': total_size,
                            'total_size_mb': round(total_size / (1024 * 1024), 2)
                        })
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'NoSuchBucket':
                            return AWSResponse(
                                success=False,
                                message=f"The specified bucket '{bucket}' does not exist",
                                requires_credentials=False
                            )
                        raise

                # Format response message
                if len(bucket_stats) == 1:
                    bucket = bucket_stats[0]
                    message = f"Bucket '{bucket['bucket_name']}' contains {bucket['file_count']} files ({bucket['total_size_mb']} MB)"
                else:
                    total_files = sum(b['file_count'] for b in bucket_stats)
                    total_size_mb = sum(b['total_size_mb'] for b in bucket_stats)
                    message = f"Found {total_files} files across {len(bucket_stats)} buckets (Total size: {total_size_mb:.2f} MB)"

                return AWSResponse(
                    success=True,
                    data=bucket_stats,
                    message=message
                )

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchBucket':
                    return AWSResponse(
                        success=False,
                        message=f"The specified bucket '{bucket_name}' does not exist",
                        requires_credentials=False
                    )
                elif error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']:
                    return AWSResponse(
                        success=False,
                        message="Invalid AWS credentials provided. Please check your Access Key ID and Secret Access Key.",
                        requires_credentials=True
                    )
                elif error_code == 'AccessDenied':
                    return AWSResponse(
                        success=False,
                        message="Your AWS credentials don't have permission to list objects in S3 buckets. Please check your IAM permissions.",
                        requires_credentials=True
                    )
                else:
                    return AWSResponse(
                        success=False,
                        message=f"AWS error: {str(e)}",
                        requires_credentials=False
                    )

        except Exception as e:
            return AWSResponse(
                success=False,
                message=f"Error counting S3 files: {str(e)}",
                requires_credentials=False
            )