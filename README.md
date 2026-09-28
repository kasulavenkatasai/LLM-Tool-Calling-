# LLM Tool Calling with Amazon Nova

This project demonstrates LLM tool calling using Amazon Nova, AWS Lambda, DynamoDB, and Python Boto3.

The LLM decides which tool to use based on the user's question.

## Architecture

                         ┌──────────────────┐
                         │       User       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Python Client   │
                         │    main.py       │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   LLMOrchestrator        │
                    │       Lambda             │
                    │                          │
                    │        Boto3             │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Amazon Nova         │
                    │     Tool Selection       │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┼─────────────┐
                    │            │             │
                    ▼            ▼             ▼
          ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐
          │   Employee   │ │   Weather    │ │ External Search │
          │     Tool     │ │     Tool     │ │      Tool       │
          └──────┬───────┘ └──────┬───────┘ └────────┬────────┘
                 │                │                  │
                 ▼                ▼                  ▼
          ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
          │EmployeeDetails│ │ WeatherDetails│  │ Wikipedia API│
          │   DynamoDB    │ │   DynamoDB    │  └──────────────┘
          └──────┬───────┘  └──────┬───────┘
                 │                │
                 └────────┬───────┘
                          │
                          │ Tool Result
                          ▼
                    ┌──────────────────┐
                    │   Amazon Nova    │
                    │  Final Response  │
                    └────────┬─────────┘
                             │
                    ┌────────┴─────────┐
                    │                  │
                    ▼                  ▼
             ┌──────────────┐    ┌──────────────┐
             │    User      │    │ Answer History│
             │   Response   │    │   DynamoDB   │
             └──────────────┘    └──────────────┘
