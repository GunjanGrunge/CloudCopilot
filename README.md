# CloudPilot - Multi-Agent AWS Assistant

CloudPilot is an intelligent AWS assistant that uses a multi-agent architecture to help you manage and interact with your AWS resources. It combines OpenAI's GPT-4 and AWS Bedrock models to provide intelligent AWS operations and assistance.

## 🚀 Features

- Interactive chat interface for AWS operations
- Secure handling of AWS credentials
- Support for common AWS operations (S3, EC2, IAM, etc.)
- Intelligent policy suggestions and validation
- Real-time AWS resource information

## 🔑 Required API Keys

Before getting started, you'll need the following API keys and credentials:

1. **OpenAI API Key**
   - Get it from: https://platform.openai.com/api-keys
   - Required for: Core chat functionality and reasoning

2. **AWS Credentials**
   - Required credentials:
     - AWS Access Key ID
     - AWS Secret Access Key
     - AWS Region
   - How to get them:
     1. Log into AWS Console
     2. Go to IAM → Users → Your User
     3. Create Access Keys under "Security credentials"
   - Required permissions:
     - S3 access
     - EC2 read access
     - IAM role management
     - AWS Bedrock access

3. **AWS Bedrock Access** (Optional)
   - Required for advanced policy validation and suggestions
   - Enable Bedrock service in your AWS account
   - Grant Bedrock access in your IAM permissions

## 📋 Environment Setup

1. Create a `.env` file in the root directory:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# AWS Configuration (Optional - can be provided through UI)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region

# AWS Bedrock Configuration
AWS_BEDROCK_MODEL_ID=anthropic.claude-v2
```

## 🛠️ Development Setup

### Backend Setup

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the FastAPI backend:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🎯 Usage Guide

### For Users

1. Access the web interface at `http://localhost:5173`

2. You can interact with CloudPilot in two ways:
   - Using environment variables for AWS credentials
   - Providing AWS credentials through the UI when needed

3. Example operations:
   - "Show me my S3 buckets"
   - "List my EC2 instances"
   - "Count files in my S3 bucket"
   - "Create an IAM role for Lambda"

4. Security notes:
   - Credentials provided through UI are only stored in memory
   - All operations are validated before execution
   - Use principle of least privilege when creating AWS credentials

### For Developers

#### Project Structure
```
cloudpilot/
├── app/                    # Backend FastAPI application
│   ├── main.py            # Main FastAPI app
│   ├── agents/            # AI agents implementation
│   ├── schemas/           # Pydantic models
│   └── tools/             # AWS operation tools
└── frontend/              # React frontend
    ├── src/
    │   ├── components/    # React components
    │   └── services/      # API services
    └── public/            # Static assets
```

#### Adding New Features

1. **Adding new AWS operations:**
   - Add new methods to `app/tools/aws_tools.py`
   - Update tool schemas in `app/agents/orchestrator.py`
   - Add corresponding types in `app/schemas/base.py`

2. **Extending the UI:**
   - Components are in `frontend/src/components`
   - API services are in `frontend/src/services/api.ts`

3. **Adding new AI capabilities:**
   - Extend agent logic in `app/agents/`
   - Update prompt handling in orchestrator

## 🔒 Security Best Practices

1. **AWS Credentials:**
   - Use temporary credentials when possible
   - Create dedicated IAM users with minimal permissions
   - Rotate access keys regularly
   - Never commit credentials to source control

2. **API Security:**
   - Use HTTPS in production
   - Implement rate limiting
   - Add proper authentication for production use

3. **Data Handling:**
   - Credentials are never stored permanently
   - All operations are logged
   - Validation occurs before execution

## 🐛 Troubleshooting

Common issues and solutions:

1. **Backend Connection Issues:**
   - Ensure FastAPI is running on port 8000
   - Check CORS settings if deploying to different domains

2. **AWS Operation Failures:**
   - Verify AWS credentials are valid
   - Check IAM permissions
   - Look for specific error messages in logs

3. **OpenAI API Issues:**
   - Verify API key is valid
   - Check API usage limits
   - Ensure proper environment variable setup

## 📚 API Documentation

The FastAPI backend provides automatic API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
![Mermaid Chart](https://www.mermaidchart.com/raw/acae59fa-2d16-4e51-9a86-66ea05021118?theme=light&version=v0.1&format=svg)
