from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from openai import APIError, BadRequestError, RateLimitError, AuthenticationError
from dotenv import load_dotenv
import boto3
import traceback
import os

# Load environment variables before importing other modules
load_dotenv()

# Verify required environment variables
required_env_vars = [
    "OPENAI_API_KEY",
    
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION"
]

missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

from .schemas.base import (
    ChatRequest, 
    ChatResponse, 
    IAMPolicyRequest, 
    IAMPolicyResponse,
    Message,
    MessageRole,
    AWSCredentials
)
from .agents.orchestrator import OrchestratorAgent
from .agents.bedrock_agent import BedrockAgent

app = FastAPI(
    title="CloudPilot API",
    description="Multi-Agent AWS Assistant API",
    version="1.0.0"
)

# Add CORS middleware with development configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default development server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
orchestrator = OrchestratorAgent()
bedrock_agent = BedrockAgent()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"detail": exc.detail}),
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": str(exc)}),
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        },
    )

@app.get("/")
async def root():
    return {"message": "Welcome to CloudPilot API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Add system message if not present
        if not any(msg.role == MessageRole.SYSTEM for msg in request.messages):
            system_message = Message(
                role=MessageRole.SYSTEM,
                content="You are CloudPilot, an AI assistant specialized in AWS cloud operations. "
                       "You can help with AWS infrastructure management, security best practices, "
                       "and resource optimization."
            )
            request.messages.insert(0, system_message)

        try:
            # Pass AWS credentials to the orchestrator if provided
            response = await orchestrator.process_request(
                request.messages,
                aws_credentials=request.awsCredentials
            )
            return response
        except AuthenticationError:
            raise HTTPException(
                status_code=401,
                detail="Invalid OpenAI API key"
            )
        except RateLimitError:
            raise HTTPException(
                status_code=429,
                detail="OpenAI rate limit exceeded. Please try again later."
            )
        except BadRequestError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request to OpenAI API: {str(e)}"
            )
        except APIError as e:
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {str(e)}"
            )
        except boto3.exceptions.BotoCoreError as e:
            raise HTTPException(
                status_code=500,
                detail=f"AWS API error: {str(e)}"
            )
        except boto3.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidClientTokenId':
                return ChatResponse(
                    response="Your AWS credentials appear to be invalid. Please provide valid credentials.",
                    requiresCredentials=True
                )
            elif error_code == 'AccessDenied':
                return ChatResponse(
                    response="Your AWS credentials don't have sufficient permissions for this operation.",
                    requiresCredentials=True
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"AWS error: {str(e)}"
                )
        except Exception as e:
            # Log the full traceback for debugging
            print(f"Unexpected error: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in chat endpoint: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.post("/suggest-iam-policy", response_model=IAMPolicyResponse)
async def suggest_iam_policy(request: IAMPolicyRequest):
    try:
        policy_suggestion = await bedrock_agent.suggest_iam_policy(
            request.description,
            credentials=request.awsCredentials
        )
        if isinstance(policy_suggestion, dict) and "error" in policy_suggestion:
            raise HTTPException(status_code=400, detail=policy_suggestion["response"])
        return IAMPolicyResponse(
            policy_document=policy_suggestion,
            explanation="Policy generated based on provided description",
            warnings=[]  # Add any warnings from validation here
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate-aws-operation")
async def validate_aws_operation(operation: dict):
    try:
        validation_result = await bedrock_agent.validate_aws_operation(
            operation,
            credentials=operation.get('awsCredentials')
        )
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))