from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str

class AWSCredentials(BaseModel):
    accessKeyId: str
    secretAccessKey: str
    region: str = "ap-south-1"

class AWSResourceAction(BaseModel):
    operation: str
    service: str
    parameters: Dict[str, Any]
    status: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = None
    aws_context: Optional[Dict[str, Any]] = None
    awsCredentials: Optional[AWSCredentials] = None

class ChatResponse(BaseModel):
    response: str
    actions_taken: List[str] = []
    aws_resources_affected: List[Dict[str, Any]] = []
    validation_results: Optional[Dict[str, Any]] = None
    requiresCredentials: Optional[bool] = None
    error: Optional[str] = None

class IAMPolicyRequest(BaseModel):
    description: str
    service: Optional[str] = None
    resource_arns: Optional[List[str]] = None
    awsCredentials: Optional[AWSCredentials] = None

class IAMPolicyResponse(BaseModel):
    policy_document: Dict[str, Any]
    explanation: Optional[str] = None
    warnings: List[str] = []
    requiresCredentials: Optional[bool] = None