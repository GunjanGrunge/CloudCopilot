# Multi-Agent AWS Assistant – Architecture & Functional Design

This project implements an intelligent AWS assistant using a **multi-agent architecture**. It leverages both **OpenAI SDK** and **AWS Bedrock models** to split tasks between reasoning, tool selection, information fetching, and task execution.

---

## 🤖 Agent Roles

### 1. **Main Orchestrator Agent (OpenAI GPT-4)**
- Uses OpenAI SDK (`gpt-4-turbo`) as the core reasoning model.
- Handles user input, determines intent, and decides whether to:
  - Call a **tool** (for informational AWS queries)
  - Delegate a task to another agent (like the AWS Execution Agent)

### 2. **Informational Tools (AWS SDK via boto3)**
- Function-calling tools for safe, **read-only** queries.
- Example functions:
  - `get_s3_bucket_sizes()`
  - `list_ec2_instances()`
  - `describe_iam_role()`
- Implemented in Python using `boto3`.

### 3. **AWS Execution Agent**
- Dedicated to handling **execution-level AWS tasks** (i.e. creating/modifying resources).
- Can use:
  - **AWS Bedrock** (Claude) for reasoning or validation
  - **boto3** for execution

#### Example operations:
- `create_s3_bucket(bucket_name)`
- `create_lambda_function(name, role, runtime, handler)`
- `create_iam_role(name, policy_document)`
- `assign_policy_to_role(role_name, policy_arn)`

---

## 🧱 Architecture Summary

| Task Type                        | Responsible Agent       | Implementation         |
|----------------------------------|--------------------------|--------------------------|
| "What is my total S3 usage?"     | GPT-4 (Tool Call)        | `boto3` function         |
| "Do I have any EC2 instances?"   | GPT-4 (Tool Call)        | `boto3` function         |
| "Explain this IAM policy"        | Claude (via Bedrock)     | `bedrock-runtime`        |
| "Create a Lambda function"       | AWS Execution Agent      | `boto3` + (optional) Claude |
| "Summarize my AWS usage"         | GPT-4 (Formatting)       | `openai.ChatCompletion` |

---

## 🧠 Reasoning Flow Example

**User Input:**  
> “Create a role with S3 full access and attach it to a Lambda function”

**System Flow:**
1. GPT-4 recognizes this is an executable task → delegates to `AWS Execution Agent`
2. The AWS Agent:
   - Optionally calls Claude to validate/optimize policy
   - Uses `boto3` to create the IAM role + Lambda
3. The agent returns a structured response
4. GPT-4 formats the message and returns it to the user

---

## 🧩 Key Technologies

- **OpenAI SDK** (`gpt-4-turbo`) for orchestration and chat
- **AWS SDK for Python (`boto3`)** for actual AWS operations
- **AWS Bedrock SDK** to call models like Claude (for policy validation, suggestions, audits)
- **FastAPI** (suggested) as backend agent routing layer
- **JSON tool schema** for OpenAI function calling

---

## 🔐 Security & Access

- User provides IAM Access Key & Secret Key
- Temporary IAM sessions recommended (via STS)
- Only scoped roles (e.g., with access to S3, Lambda, IAM, Bedrock) should be accepted
- All actions logged and permission-validated before execution

---

## 🧰 Optional Tool/Function Naming (for OpenAI tool spec)

```json
[
  {
    "name": "get_s3_usage",
    "description": "Returns total size of all accessible S3 buckets",
    "parameters": {}
  },
  {
    "name": "create_lambda_function",
    "description": "Creates a Lambda function using IAM role",
    "parameters": {
      "function_name": "string",
      "runtime": "string",
      "handler": "string",
      "role_arn": "string",
      "zip_file_path": "string"
    }
  },
  {
    "name": "explain_policy_with_claude",
    "description": "Uses Claude to explain an IAM policy",
    "parameters": {
      "policy_json": "string"
    }
  }
]
