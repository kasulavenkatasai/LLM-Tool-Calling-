import boto3
import json


# ============================================================
# AWS CLIENT
# ============================================================

lambda_client = boto3.client(
    "lambda",
    region_name="us-east-1"
)


# ============================================================
# ASK BACKEND LAMBDA
# ============================================================

def ask_question(question):

    response = lambda_client.invoke(
        FunctionName="LLMOrchestrator",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "question": question
        }).encode()
    )

    payload = response[
        "Payload"
    ].read().decode()

    result = json.loads(
        payload
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    question = input(
        "\nAsk your question: "
    )

    print(
        "\nThinking..."
    )

    result = ask_question(
        question
    )

    print(
        "\n================================"
    )

    print(
        "FINAL ANSWER"
    )

    print(
        "================================"
    )

    print(
        result.get(
            "answer",
            "No answer returned"
        )
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()