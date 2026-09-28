import boto3
import json
import logging
import os
import uuid
from urllib.request import urlopen, Request
from urllib.parse import urlencode


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# AWS CLIENTS
# ============================================================

bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1"
)


# ============================================================
# DYNAMODB TABLES
# ============================================================

# Existing table used to store final question and answer.
answer_table = dynamodb.Table(
    os.environ["TABLE_NAME"]
)

# Employee information table.
employee_table = dynamodb.Table(
    "EmployeeDetails"
)

# Weather information table.
weather_table = dynamodb.Table(
    "WeatherDetails"
)


# ============================================================
# MODEL
# ============================================================

model_id = "us.amazon.nova-2-lite-v1:0"


# ============================================================
# TOOL DEFINITIONS
# ============================================================

tools = [

    # --------------------------------------------------------
    # EMPLOYEE DYNAMODB TOOL
    # --------------------------------------------------------

    {
        "toolSpec": {
            "name": "get_employee_from_dynamodb",
            "description": (
                "Get employee information from the EmployeeDetails "
                "DynamoDB table. Use this tool for employee questions "
                "such as salary or department. Always use this tool "
                "for employee information."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Employee name"
                        }
                    },
                    "required": ["name"]
                }
            }
        }
    },

    # --------------------------------------------------------
    # WEATHER DYNAMODB TOOL
    # --------------------------------------------------------

    {
        "toolSpec": {
            "name": "get_weather_from_dynamodb",
            "description": (
                "Get predefined weather information from the "
                "WeatherDetails DynamoDB table. Use this tool "
                "for weather questions."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name of the city"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    },

    # --------------------------------------------------------
    # EXTERNAL SEARCH TOOL
    # --------------------------------------------------------

    {
        "toolSpec": {
            "name": "external_search",
            "description": (
                "Search an external information source when "
                "the required information is not available "
                "through the predefined DynamoDB tools. "
                "Use this for general public information and "
                "current or latest information."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Information to search externally"
                            )
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    }
]


# ============================================================
# TOOL CONFIGURATION
# ============================================================

tool_config = {
    "tools": tools,
    "toolChoice": {
        "auto": {}
    }
}


# ============================================================
# EMPLOYEE DYNAMODB
# ============================================================

def get_employee_from_dynamodb(name):

    logger.info(
        "Querying EmployeeDetails DynamoDB for employee: %s",
        name
    )

    try:

        # Normalize employee name.
        # mani -> Mani
        # MANI -> Mani
        # Mani -> Mani

        name = name.strip().title()

        response = employee_table.get_item(
            Key={
                "name": name
            }
        )

        item = response.get("Item")

        if not item:

            logger.warning(
                "Employee not found in DynamoDB: %s",
                name
            )

            return {
                "error": f"Employee {name} was not found"
            }

        logger.info(
            "Employee information retrieved from DynamoDB"
        )

        # Convert DynamoDB Decimal values into
        # JSON-compatible values for Bedrock.

        return json.loads(
            json.dumps(item, default=str)
        )

    except Exception as error:

        logger.exception(
            "Employee DynamoDB query failed"
        )

        return {
            "error": (
                f"Employee DynamoDB query failed: {str(error)}"
            )
        }


# ============================================================
# WEATHER DYNAMODB
# ============================================================

def get_weather_from_dynamodb(city):

    logger.info(
        "Querying WeatherDetails DynamoDB for city: %s",
        city
    )

    try:

        # Normalize city name.
        # chennai -> Chennai
        # CHENNAI -> Chennai
        # Chennai -> Chennai

        city = city.strip().title()

        response = weather_table.get_item(
            Key={
                "city": city
            }
        )

        item = response.get("Item")

        if not item:

            logger.warning(
                "Weather information not found in DynamoDB: %s",
                city
            )

            return {
                "error": (
                    f"Weather information for {city} "
                    "was not found"
                )
            }

        logger.info(
            "Weather information retrieved from DynamoDB"
        )

        # Convert DynamoDB Decimal values such as
        # temperature into JSON-compatible values.

        return json.loads(
            json.dumps(item, default=str)
        )

    except Exception as error:

        logger.exception(
            "Weather DynamoDB query failed"
        )

        return {
            "error": (
                f"Weather DynamoDB query failed: {str(error)}"
            )
        }


# ============================================================
# EXTERNAL SEARCH
# ============================================================

def external_search(query):

    logger.info(
        "Calling external API for query: %s",
        query
    )

    try:

        # ====================================================
        # STEP 1: SEARCH WIKIPEDIA
        # ====================================================

        search_params = urlencode({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": "1"
        })

        search_url = (
            "https://en.wikipedia.org/w/api.php?"
            + search_params
        )

        search_request = Request(
            search_url,
            headers={
                "User-Agent": (
                    "LLMToolCalling/1.0 "
                    "(educational project)"
                )
            }
        )

        with urlopen(
            search_request,
            timeout=10
        ) as response:

            search_data = json.loads(
                response.read().decode()
            )

        search_results = (
            search_data
            .get("query", {})
            .get("search", [])
        )

        if not search_results:

            logger.warning(
                "No Wikipedia search results found"
            )

            return {
                "error": "No external information found"
            }

        # ====================================================
        # STEP 2: GET BEST MATCHING PAGE
        # ====================================================

        best_result = search_results[0]

        page_title = best_result.get("title")

        logger.info(
            "Best Wikipedia result: %s",
            page_title
        )

        if not page_title:

            return {
                "error": "Wikipedia result did not contain a page title"
            }

        # ====================================================
        # STEP 3: GET ACTUAL PAGE SUMMARY
        # ====================================================

        encoded_title = page_title.replace(
            " ",
            "_"
        )

        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + encoded_title
        )

        summary_request = Request(
            summary_url,
            headers={
                "User-Agent": (
                    "LLMToolCalling/1.0 "
                    "(educational project)"
                )
            }
        )

        with urlopen(
            summary_request,
            timeout=10
        ) as response:

            summary_data = json.loads(
                response.read().decode()
            )

        # ====================================================
        # STEP 4: EXTRACT USEFUL INFORMATION
        # ====================================================

        title = summary_data.get(
            "title",
            page_title
        )

        description = summary_data.get(
            "description"
        )

        summary = summary_data.get(
            "extract"
        )

        page_url = (
            summary_data
            .get("content_urls", {})
            .get("desktop", {})
            .get("page")
        )

        logger.info(
            "Wikipedia page information retrieved successfully"
        )

        return {
            "source": "Wikipedia",
            "title": title,
            "description": description,
            "summary": summary,
            "url": page_url
        }

    except Exception as error:

        logger.exception(
            "External API request failed"
        )

        return {
            "error": (
                f"External API request failed: {str(error)}"
            )
        }


# ============================================================
# EXECUTE TOOL
# ============================================================

def execute_tool(tool_name, tool_input):

    logger.info(
        "Executing tool: %s",
        tool_name
    )

    logger.info(
        "Tool input: %s",
        tool_input
    )

    try:

        # ----------------------------------------------------
        # EMPLOYEE DYNAMODB
        # ----------------------------------------------------

        if tool_name == "get_employee_from_dynamodb":

            result = get_employee_from_dynamodb(
                tool_input["name"]
            )

            return result

        # ----------------------------------------------------
        # WEATHER DYNAMODB
        # ----------------------------------------------------

        elif tool_name == "get_weather_from_dynamodb":

            result = get_weather_from_dynamodb(
                tool_input["city"]
            )

            return result

        # ----------------------------------------------------
        # EXTERNAL SEARCH
        # ----------------------------------------------------

        elif tool_name == "external_search":

            return external_search(
                tool_input["query"]
            )

        # ----------------------------------------------------
        # UNKNOWN TOOL
        # ----------------------------------------------------

        else:

            return {
                "error": "Unknown tool requested"
            }

    except Exception as error:

        logger.exception(
            "Tool execution failed"
        )

        return {
            "error": str(error)
        }


# ============================================================
# EXTRACT TEXT
# ============================================================

def extract_text(response):

    text = ""

    content = response[
        "output"
    ][
        "message"
    ][
        "content"
    ]

    for block in content:

        if "text" in block:

            text += block["text"]

    return text


# ============================================================
# SAVE ANSWER
# ============================================================

def save_answer(question, answer):

    answer_id = str(uuid.uuid4())

    answer_table.put_item(
        Item={
            "id": answer_id,
            "question": question,
            "answer": answer
        }
    )

    logger.info(
        "Answer saved successfully to DynamoDB"
    )


# ============================================================
# ASK NOVA
# ============================================================

def ask_nova(question):

    logger.info(
        "Starting LLM workflow"
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        "Answer the user's question.\n\n"

                        "You have three tools available:\n"
                        "1. EmployeeDetails DynamoDB tool\n"
                        "2. WeatherDetails DynamoDB tool\n"
                        "3. External search tool\n\n"

                        "For employee questions such as salary "
                        "or department, ALWAYS use the "
                        "EmployeeDetails DynamoDB tool.\n\n"

                        "For weather questions, use the "
                        "WeatherDetails DynamoDB tool.\n\n"

                        "Do not use external_search to find "
                        "private employee information such as "
                        "salary or department.\n\n"

                        "Use external_search for general public "
                        "information that is not available in "
                        "the DynamoDB tools.\n\n"

                        "For questions asking for current, "
                        "latest, or up-to-date information, "
                        "use external_search.\n\n"

                        "When external_search returns useful "
                        "information, answer the user's question "
                        "directly using that information. "
                        "Do not say that another search is needed "
                        "unless the tool result is actually "
                        "insufficient.\n\n"

                        "If external_search returns an error, "
                        "clearly state that the external source "
                        "could not provide the information.\n\n"

                        "If a DynamoDB tool returns an error, "
                        "report that the requested information "
                        "was not found. Do not search the "
                        "internet for private employee data.\n\n"

                        "Do not invent information.\n\n"

                        f"User question: {question}"
                    )
                }
            ]
        }
    ]

    # ========================================================
    # FIRST NOVA REQUEST
    # ========================================================

    logger.info(
        "Sending question to Amazon Nova"
    )

    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        toolConfig=tool_config,
        inferenceConfig={
            "maxTokens": 500,
            "temperature": 0
        }
    )

    # ========================================================
    # TOOL-CALLING LOOP
    # ========================================================

    while response["stopReason"] == "tool_use":

        logger.info(
            "Nova requested tool use"
        )

        assistant_message = response[
            "output"
        ][
            "message"
        ]

        messages.append(
            assistant_message
        )

        tool_results = []

        for content_block in assistant_message[
            "content"
        ]:

            if "toolUse" not in content_block:
                continue

            tool_use = content_block[
                "toolUse"
            ]

            tool_name = tool_use[
                "name"
            ]

            tool_input = tool_use[
                "input"
            ]

            tool_use_id = tool_use[
                "toolUseId"
            ]

            logger.info(
                "Nova selected tool: %s",
                tool_name
            )

            logger.info(
                "Nova tool input: %s",
                tool_input
            )

            result = execute_tool(
                tool_name,
                tool_input
            )

            logger.info(
                "Tool result: %s",
                result
            )

            logger.info(
                "Sending tool result back to Nova"
            )

            tool_results.append(
                {
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [
                            {
                                "json": result
                            }
                        ],
                        "status": (
                            "error"
                            if result and "error" in result
                            else "success"
                        )
                    }
                }
            )

        messages.append(
            {
                "role": "user",
                "content": tool_results
            }
        )

        # ====================================================
        # REQUEST FINAL ANSWER FROM NOVA
        # ====================================================

        logger.info(
            "Requesting final answer from Nova"
        )

        response = bedrock.converse(
            modelId=model_id,
            messages=messages,
            toolConfig=tool_config,
            inferenceConfig={
                "maxTokens": 500,
                "temperature": 0
            }
        )

    # ========================================================
    # FINAL ANSWER
    # ========================================================

    final_answer = extract_text(
        response
    )

    logger.info(
        "Final answer generated"
    )

    return final_answer


# ============================================================
# LAMBDA HANDLER
# ============================================================

def lambda_handler(event, context):

    logger.info(
        "Backend Lambda started"
    )

    try:

        question = event.get(
            "question"
        )

        if not question:

            logger.warning(
                "Question was not provided"
            )

            return {
                "statusCode": 400,
                "answer": "Question was not provided"
            }

        logger.info(
            "Question received: %s",
            question
        )

        answer = ask_nova(
            question
        )

        save_answer(
            question,
            answer
        )

        logger.info(
            "Backend Lambda completed successfully"
        )

        return {
            "statusCode": 200,
            "answer": answer
        }

    except Exception as error:

        logger.exception(
            "Backend Lambda failed"
        )

        return {
            "statusCode": 500,
            "answer": (
                "An error occurred while processing "
                "the question."
            ),
            "error": str(error)
        }