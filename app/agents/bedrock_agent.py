import boto3
import json
import os
from typing import Dict, Any, Optional, Union
from botocore.exceptions import ClientError, BotoCoreError
from ..schemas.base import AWSCredentials
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockAgent:
    def __init__(self):
        self.session = None
        self.model_id = os.environ.get('AWS_BEDROCK_MODEL_ID', 'anthropic.claude-v2')
        logger.info(f"Initialized BedrockAgent with model: {self.model_id}")

    def _init_session(self, credentials: Optional[AWSCredentials] = None) -> Union[str, None]:
        """Initialize AWS session with provided or default credentials"""
        try:
            if credentials:
                self.session = boto3.Session(
                    aws_access_key_id=credentials.accessKeyId,
                    aws_secret_access_key=credentials.secretAccessKey,
                    region_name=credentials.region
                )
            else:
                raise Exception("AWS credentials are required for this operation")
            logger.info("AWS session initialized successfully")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize AWS session: {str(e)}")
            return str(e)

    def _get_bedrock_client(self, credentials: Optional[AWSCredentials] = None):
        """Get Bedrock client with appropriate credentials"""
        error = self._init_session(credentials)
        if error:
            raise Exception(error)
        return self.session.client('bedrock-runtime')

    async def validate_aws_operation(
        self, 
        operation: Dict[str, Any],
        credentials: Optional[AWSCredentials] = None
    ) -> Dict[str, Any]:
        """
        Validates an AWS operation using Claude. This includes checking permissions
        and validating that the operation is safe to execute.
        """
        try:
            # First validate the credentials have required permissions
            if credentials:
                try:
                    sts = self.session.client('sts')
                    identity = sts.get_caller_identity()
                    logger.info(f"Validating operation for AWS user: {identity['Arn']}")
                except Exception as e:
                    return {
                        "is_valid": False,
                        "security_concerns": [
                            "Unable to validate AWS credentials"
                        ],
                        "best_practice_suggestions": [
                            "Ensure the provided credentials are valid",
                            "Ensure the credentials have sufficient permissions"
                        ],
                        "parameter_validation": {
                            "valid_parameters": [],
                            "invalid_parameters": ["credentials"],
                            "missing_parameters": []
                        },
                        "recommendation": f"Please provide valid AWS credentials. Error: {str(e)}"
                    }

            prompt = f"""
            Please analyze this AWS operation for potential security issues, best practices, and validate its parameters:

            Operation: {json.dumps(operation, indent=2)}

            Provide your analysis in the following JSON format:
            {{
                "is_valid": boolean,
                "security_concerns": [list of strings],
                "best_practice_suggestions": [list of strings],
                "parameter_validation": {{
                    "valid_parameters": [list of strings],
                    "invalid_parameters": [list of strings],
                    "missing_parameters": [list of strings]
                }},
                "recommendation": "string"
            }}
            
            Consider these security aspects:
            1. Principle of least privilege
            2. Resource naming conventions
            3. Access control settings
            4. Data security implications
            5. Cost implications
            """

            response = await self._invoke_bedrock(prompt, credentials)
            try:
                validation_result = json.loads(response)
                if not isinstance(validation_result, dict) or 'is_valid' not in validation_result:
                    raise Exception("Invalid validation response format")
                return validation_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse validation response: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Error in validate_aws_operation: {str(e)}")
            raise

    async def suggest_iam_policy(
        self, 
        description: str,
        credentials: Optional[AWSCredentials] = None
    ) -> Dict[str, Any]:
        """Suggests an IAM policy based on a description"""
        try:
            prompt = f"""
            Please suggest an AWS IAM policy based on this description of required permissions:

            Description: {description}

            Provide your response as a valid IAM policy JSON document with minimal required permissions following the principle of least privilege.
            Include comments explaining each permission.

            Consider:
            1. Use specific resource ARNs where possible
            2. Avoid overly permissive actions (e.g., '*')
            3. Include necessary conditions
            4. Follow AWS security best practices
            """

            response = await self._invoke_bedrock(prompt, credentials)
            try:
                policy = json.loads(response)
                return policy
            except json.JSONDecodeError:
                return {"error": "Could not parse policy", "response": response}

        except Exception as e:
            logger.error(f"Error in suggest_iam_policy: {str(e)}")
            raise

    async def _invoke_bedrock(
        self, 
        prompt: str,
        credentials: Optional[AWSCredentials] = None
    ) -> str:
        """Invokes Bedrock with the given prompt"""
        try:
            request = {
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 2048,
                "temperature": 0,
                "top_p": 0.9,
            }

            try:
                bedrock = self._get_bedrock_client(credentials)
                response = bedrock.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request)
                )
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'AccessDeniedException':
                    logger.error("Access denied to AWS Bedrock")
                    raise Exception("Access denied to AWS Bedrock. Please check your IAM permissions.")
                elif error_code == 'ValidationException':
                    logger.error(f"Invalid request to Bedrock: {str(e)}")
                    raise Exception(f"Invalid request to Bedrock: {str(e)}")
                elif error_code == 'ThrottlingException':
                    logger.error("AWS Bedrock request was throttled")
                    raise Exception("AWS Bedrock request was throttled. Please try again later.")
                else:
                    logger.error(f"AWS Bedrock error: {str(e)}")
                    raise Exception(f"AWS Bedrock error: {str(e)}")
            except BotoCoreError as e:
                logger.error(f"AWS Bedrock connection error: {str(e)}")
                raise Exception(f"AWS Bedrock connection error: {str(e)}")

            try:
                response_body = json.loads(response['body'].read())
                completion = response_body.get('completion', '')
                if not completion:
                    logger.error("Empty response from Bedrock")
                    raise Exception("Empty response from Bedrock")
                return completion
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse Bedrock response: {str(e)}")
                raise Exception(f"Failed to parse Bedrock response: {str(e)}")

        except Exception as e:
            logger.error(f"Error in _invoke_bedrock: {str(e)}")
            raise Exception(f"Error in _invoke_bedrock: {str(e)}")