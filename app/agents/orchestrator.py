from typing import List, Dict, Any, Optional
from openai import OpenAI, APIError, BadRequestError, RateLimitError, AuthenticationError
from ..schemas.base import Message, ChatResponse, AWSCredentials
from ..tools.aws_tools import AWSTools, AWSResponse
from .bedrock_agent import BedrockAgent
from dotenv import load_dotenv
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OrchestratorAgent:
    def __init__(self):
        # Load environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise Exception("OpenAI API key not found in environment variables")
            
        try:
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4-1106-preview"  # Using the stable model name
            self.aws_tools = AWSTools()
            self.bedrock_agent = BedrockAgent()
        except Exception as e:
            logger.error(f"Error initializing OrchestratorAgent: {str(e)}")
            raise

        # Define tools that require AWS credentials
        self.aws_operations = {
            'get_s3_bucket_sizes': True,
            'list_ec2_instances': True,
            'describe_iam_role': True,
            'create_s3_bucket': True,
            'create_lambda_function': True,
            'create_iam_role': True,
            'assign_policy_to_role': True,
            'get_s3_bucket_file_count': True  # Add new operation
        }

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_s3_bucket_file_count",
                    "description": "Returns the number of files in an S3 bucket or all buckets",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bucket_name": {
                                "type": "string",
                                "description": "Optional. Name of the specific S3 bucket to check. If not provided, checks all buckets."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_s3_bucket_sizes",
                    "description": "Returns total size of all accessible S3 buckets",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_ec2_instances",
                    "description": "Returns list of EC2 instances with their details",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "describe_iam_role",
                    "description": "Returns details about an IAM role",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "role_name": {
                                "type": "string",
                                "description": "Name of the IAM role"
                            }
                        },
                        "required": ["role_name"]
                    }
                }
            }
        ]

        # Add new tool for IAM policy suggestion
        self.tools.append({
            "type": "function",
            "function": {
                "name": "suggest_iam_policy",
                "description": "Suggests an IAM policy based on a description of required permissions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the required permissions"
                        }
                    },
                    "required": ["description"]
                }
            }
        })

        # Add AWS resource creation tools
        self.tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "create_s3_bucket",
                    "description": "Creates a new S3 bucket",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bucket_name": {
                                "type": "string",
                                "description": "Name of the S3 bucket to create"
                            }
                        },
                        "required": ["bucket_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_lambda_function",
                    "description": "Creates a new Lambda function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the Lambda function"
                            },
                            "role_arn": {
                                "type": "string",
                                "description": "ARN of the IAM role for the function"
                            },
                            "runtime": {
                                "type": "string",
                                "description": "Runtime environment (e.g., python3.9)"
                            },
                            "handler": {
                                "type": "string",
                                "description": "Function handler (e.g., index.handler)"
                            },
                            "zip_file_path": {
                                "type": "string",
                                "description": "Path to the zip file containing function code"
                            }
                        },
                        "required": ["name", "role_arn", "runtime", "handler", "zip_file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_iam_role",
                    "description": "Creates a new IAM role",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the IAM role"
                            },
                            "policy_document": {
                                "type": "object",
                                "description": "IAM policy document"
                            }
                        },
                        "required": ["name", "policy_document"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "assign_policy_to_role",
                    "description": "Attaches an existing policy to an IAM role",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "role_name": {
                                "type": "string",
                                "description": "Name of the IAM role"
                            },
                            "policy_arn": {
                                "type": "string",
                                "description": "ARN of the policy to attach"
                            }
                        },
                        "required": ["role_name", "policy_arn"]
                    }
                }
            }
        ])

    def _requires_aws_credentials(self, function_name: str) -> bool:
        return self.aws_operations.get(function_name, False)

    async def process_request(self, messages: List[Message], aws_credentials: Optional[AWSCredentials] = None) -> ChatResponse:
        try:
            logger.info("Processing request with %d messages", len(messages))
            # Convert messages to OpenAI format
            openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
            logger.debug("OpenAI messages: %s", json.dumps(openai_messages))
            
            try:
                logger.info("Calling OpenAI API with model: %s", self.model)
                # Get response from OpenAI with function calling
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                logger.debug("OpenAI response: %s", json.dumps(response.model_dump()))
            except AuthenticationError as e:
                logger.error("OpenAI authentication failed: %s", str(e))
                raise
            except RateLimitError as e:
                logger.error("OpenAI rate limit exceeded: %s", str(e))
                raise
            except BadRequestError as e:
                logger.error("OpenAI bad request: %s", str(e))
                raise
            except APIError as e:
                logger.error("OpenAI API error: %s", str(e))
                raise
            except Exception as e:
                logger.error("Unexpected error calling OpenAI: %s", str(e), exc_info=True)
                raise
            
            message = response.choices[0].message
            actions_taken = []
            aws_resources_affected = []
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    try:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        logger.info("Processing tool call: %s with arguments: %s", function_name, arguments)
                        
                        # Check if operation requires AWS credentials
                        if self._requires_aws_credentials(function_name):
                            if not aws_credentials:
                                return ChatResponse(
                                    response="I'll need your AWS credentials to perform this operation. Don't worry - your credentials will be used securely and only for this specific task. Please provide them in the prompt.",
                                    requiresCredentials=True
                                )

                            # Add credentials to the arguments
                            arguments['credentials'] = aws_credentials

                        # Execute the function
                        try:
                            result = await self._execute_function(function_name, arguments)
                            
                            # Handle AWSResponse type
                            if isinstance(result, AWSResponse):
                                if result.requires_credentials:
                                    return ChatResponse(
                                        response=result.message,
                                        requiresCredentials=True
                                    )
                                elif not result.success:
                                    return ChatResponse(
                                        response=result.message,
                                        actions_taken=actions_taken
                                    )
                                else:
                                    actions_taken.append(f"Successfully executed {function_name}")
                                    result = result.data  # Use the data for OpenAI response

                            # Record AWS resource changes
                            if function_name in self.aws_operations:
                                aws_resources_affected.append({
                                    'operation': function_name,
                                    'parameters': {k: v for k, v in arguments.items() if k != 'credentials'}
                                })

                            # Add results to conversation
                            openai_messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "tool_calls": [tool_call]
                            })
                            openai_messages.append({
                                "role": "tool",
                                "content": json.dumps(result),
                                "tool_call_id": tool_call.id
                            })

                        except Exception as e:
                            error_msg = str(e)
                            if "credentials" in error_msg.lower() or "access" in error_msg.lower():
                                return ChatResponse(
                                    response=f"I need valid AWS credentials to perform this operation: {error_msg}",
                                    requiresCredentials=True
                                )
                            raise
                    except Exception as e:
                        logger.error("Error processing tool call: %s", str(e))
                        raise
                
                try:
                    # Get final response after function execution
                    final_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=openai_messages
                    )
                    content = final_response.choices[0].message.content
                    logger.info("Final response received from OpenAI")
                except Exception as e:
                    logger.error("Error getting final response from OpenAI: %s", str(e))
                    raise
            else:
                content = message.content
            
            return ChatResponse(
                response=content,
                actions_taken=actions_taken,
                aws_resources_affected=aws_resources_affected,
                requiresCredentials=False
            )
            
        except Exception as e:
            logger.error("Error in process_request: %s", str(e))
            raise Exception(f"Error in process_request: {str(e)}")

    async def validate_aws_operation(self, operation: Dict[str, Any], credentials: Optional[AWSCredentials] = None) -> bool:
        try:
            logger.info("Validating AWS operation: %s", operation)
            validation_result = await self.bedrock_agent.validate_aws_operation(operation, credentials)
            is_valid = validation_result.get('is_valid', False)
            logger.info("Validation result: %s", is_valid)
            return is_valid
        except Exception as e:
            logger.error("Error validating AWS operation: %s", str(e))
            raise Exception(f"Error validating AWS operation: {str(e)}")

    async def _execute_function(self, function_name: str, arguments: Dict[str, Any] = None) -> Any:
        if not hasattr(self.aws_tools, function_name):
            logger.error("Unknown function: %s", function_name)
            raise Exception(f"Unknown function: {function_name}")
            
        function = getattr(self.aws_tools, function_name)
        logger.info("Executing function: %s with arguments: %s", function_name, arguments)
        if arguments:
            return await function(**arguments)
        return await function()