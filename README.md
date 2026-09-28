
Use this as your `README.md`:

# LLM Tool Calling with Amazon Nova

This project demonstrates LLM tool calling using Amazon Nova, AWS Lambda, DynamoDB, and Python Boto3.

The LLM decides which tool to use based on the user's question.

## Architecture

```text
User
  │
  ▼
Python Client
  │
  ▼
LLMOrchestrator Lambda
  │
  ▼
Amazon Nova
  │
  ├── Employee Tool ──► EmployeeDetails DynamoDB
  │
  ├── Weather Tool ───► WeatherDetails DynamoDB
  │
  └── External Search ─► Wikipedia API
  │
  ▼
Amazon Nova
  │
  ▼
Final Answer
  │
  ▼
Answer History DynamoDB
````

## How It Works

1. User enters a question through the Python client.
2. The client invokes `LLMOrchestrator`.
3. Amazon Nova analyzes the question.
4. Nova decides whether a tool is required.
5. The Lambda executes the selected tool using Python/Boto3.
6. The tool retrieves the required information.
7. The result is sent back to Amazon Nova.
8. Nova generates the final answer.
9. The answer is stored in DynamoDB.

### Available Tools

* `get_employee_from_dynamodb` → Employee information
* `get_weather_from_dynamodb` → Weather information
* `external_search` → Public information using Wikipedia

## AWS Resources

* Amazon Bedrock / Amazon Nova
* AWS Lambda
* Amazon DynamoDB
* Amazon S3
* AWS CloudFormation
* AWS IAM

## Project Structure

```text
LLM-Tool-Calling/
│
├── backend/
│   └── index.py
│
├── client/
│   └── main.py
│
├── cloudformation.json
├── README.md
└── .gitignore
```

## Deployment

### 1. Create the backend ZIP

```powershell
Compress-Archive -Path .\backend\index.py -DestinationPath .\backend.zip -Force
```

### 2. Upload the backend ZIP to S3

```powershell
aws s3 cp .\backend.zip s3://YOUR-BUCKET/backend.zip
```

### 3. Deploy CloudFormation

```powershell
aws cloudformation deploy `
  --stack-name llm-tool-calling-stack `
  --template-file cloudformation.json `
  --parameter-overrides CodeBucket=YOUR-BUCKET BackendCodeKey=backend.zip `
  --capabilities CAPABILITY_NAMED_IAM `
  --region us-east-1
```

CloudFormation creates the required Lambda functions, DynamoDB tables, IAM roles, and seed data.

## Run the Application

```powershell
py .\client\main.py
```

Example questions:

```text
What is Sai's salary?
What department does Mani work in?
What is the weather in Chennai?
Who is the current Prime Minister of India?
```

## Notes

* `backend.zip` is only a deployment package and is not committed to GitHub.
* AWS credentials and secrets should never be committed.

  
* short overview :

This project uses Amazon Nova with tool calling to dynamically retrieve information from DynamoDB or an external API. The LLMOrchestrator Lambda receives the user's question, sends it to Nova, executes the selected tool using Python/Boto3, returns the tool result to Nova, and stores the final response in DynamoDB.
