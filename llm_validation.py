import os
import sys
import logging
import asyncio
import argparse
import traceback
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.append(os.getcwd())
logger = logging.getLogger("LLM_Connect_Validation")

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    logger.error(f"Environment file not found at {env_path}")
    logger.info("Please create a .env file based on .env.example")
    sys.exit(1)

load_dotenv(env_path)


def get_llm_config(api_key: str = None, base_url: str = None, model_name: str = None):
    """Get and validate LLM configuration

    Args:
        api_key: LLM API key
        base_url: LLM API base URL
        model_name: LLM model name

    Returns:
        Tuple of (api_key, base_url, model_name) if valid, None otherwise
    """
    api_key = api_key or os.environ.get("LLM_API_KEY")
    base_url = base_url or os.environ.get("LLM_API_BASE")
    model_name = model_name or os.environ.get("LLM_MODEL")

    # Ensure base_url has correct format
    if base_url and not base_url.startswith(('http://', 'https://')):
        base_url = f"https://{base_url}"

    # Validate configuration completeness
    if not all([api_key, base_url, model_name]):
        logger.error("Error: Missing required LLM configuration parameters")
        return None

    return api_key, base_url, model_name


def log_config(api_key: str, base_url: str, model_name: str):
    """Log LLM configuration information

    Args:
        api_key: LLM API key
        base_url: LLM API base URL
        model_name: LLM model name
    """
    logger.info("=" * 50)
    logger.info(f"LLM Connection Configuration:")
    logger.info(
        f"LLM_API_KEY: {'*'*(len(api_key)-4) + api_key[-4:] if api_key else 'Not set'}")
    logger.info(f"LLM_BASE_URL: {base_url}")
    logger.info(f"LLM_MODEL_NAME: {model_name}")
    logger.info("=" * 50)


async def call_llm_api(api_key: str, base_url: str, model_name: str, messages: list, max_tokens: int = 1000, tools: list = None):
    """Universal LLM API call function

    Args:
        api_key: LLM API key
        base_url: LLM API base URL
        model_name: LLM model name
        messages: List of messages in chat format
        max_tokens: Maximum number of tokens to generate
        tools: List of tools in OpenAI API format (optional)

    Returns:
        Tuple of (success_flag, response_content, full_response_data)
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    if tools:
        data["tools"] = tools

    try:
        async with httpx.AsyncClient(timeout = 30) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers = headers,
                json = data,
            )
            resp.raise_for_status()
            resp_data = resp.json()
            logger.info(f"LLM Server Returned: {resp_data}")

            # Handle tool calls and normal responses
            if "choices" in resp_data and len(resp_data["choices"]) > 0:
                message = resp_data["choices"][0]["message"]
                resp_content = message.get("content", "").strip()

                # Log tool calls if present
                if "tool_calls" in message:
                    logger.info(f"LLM Tool Calls: {message['tool_calls']}")

                logger.info(f"LLM Response Content: {resp_content}")
                return True, resp_content, resp_data
            else:
                logger.error("Invalid response format: 'choices' field not found or empty")
                return False, "Invalid response format", None
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        logger.error(traceback.format_exc())
        return False, e, None


async def test_llm_connection(
    api_key: str = None,
    base_url: str = None,
    model_name: str = None,
):
    """Test LLM connection by sending a simple query

    Args:
        api_key: LLM API key
        base_url: LLM API base URL
        model_name: LLM model name

    Returns:
        Tuple of (success_flag, response_content)
    """
    config = get_llm_config(api_key, base_url, model_name)
    if not config:
        return False, "Missing required LLM configuration parameters"

    api_key, base_url, model_name = config
    log_config(api_key, base_url, model_name)

    messages = [
        {"role": "user", "content": "First tell me who you are? Then Please reply with the two words 'Test Successful' and nothing else"}
    ]

    success, resp_content, _ = await call_llm_api(
        api_key,
        base_url,
        model_name,
        messages,
        max_tokens = 20
    )

    if success and "Test Successful" in resp_content:
        logger.info("✅ LLM connection test successful!")
        logger.info(f"Model: {model_name}")
        logger.info(f"API Base: {base_url}")
        logger.info(f"Response: {resp_content}")
        logger.info("=" * 50)
        return True, resp_content
    elif success:
        logger.error(
            "❌ LLM connection test failed! Response did not contain 'Test Successful'")
        logger.error(f"Response: {resp_content}")
        logger.error("=" * 50)
        return False, "Response did not contain 'Test Successful'"
    else:
        logger.error("❌ LLM connection test failed!")
        logger.error("=" * 50)
        return False, resp_content


async def test_llm_capabilities(
    api_key: str = None,
    base_url: str = None,
    model_name: str = None,
):
    """Test LLM capabilities by generating questions from text

    Args:
        api_key: LLM API key
        base_url: LLM API base URL
        model_name: LLM model name

    Returns:
        Tuple of (success_flag, response_content)
    """
    config = get_llm_config(api_key, base_url, model_name)
    if not config:
        return False, "Missing required LLM configuration parameters"

    api_key, base_url, model_name = config
    log_config(api_key, base_url, model_name)

    test_text = "Artificial intelligence is a branch of computer science dedicated to creating machines capable of simulating human intelligence. It involves developing systems that can perceive, reason, learn, and make decisions. The applications of artificial intelligence are wide-ranging, including natural language processing, computer vision, robotics, and expert systems."

    messages = [
        {"role": "user", "content": f"Using Chinese! Based on the following text, generate a high-quality question. The question should have clear direction and test understanding of the core content:\n{test_text}"}
    ]

    success, resp_content, _ = await call_llm_api(
        api_key,
        base_url,
        model_name,
        messages,
        max_tokens = 1000
    )

    if success:
        logger.info("✅ LLM capabilities test successful!")
        logger.info("-" * 50)
        logger.info("Generated question:")
        logger.info(resp_content)
        logger.info("=" * 50)
        return True, resp_content
    else:
        logger.error("❌ LLM capabilities test failed!")
        logger.error("=" * 50)
        return False, resp_content


async def test_llm_tools_use(
    api_key: str = None,
    base_url: str = None,
    model_name: str = None,
):
    """Test LLM's tool usage capabilities

    Args:
        api_key: LLM API key
        base_url: LLM API base URL
        model_name: LLM model name

    Returns:
        Tuple of (success_flag, response_content)
    """
    config = get_llm_config(api_key, base_url, model_name)
    if not config:
        return False, "Missing required LLM configuration parameters"

    api_key, base_url, model_name = config
    log_config(api_key, base_url, model_name)

    # Define a simple calculator tool
    calculator_tool = {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform simple mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to calculate, such as '2+2' or '5*6'"
                    }
                },
                "required": ["expression"]
            }
        }
    }

    messages = [
        {"role": "user", "content": "Calculate 1234 multiplied by 5678."}
    ]

    success, resp_content, full_response = await call_llm_api(
        api_key,
        base_url,
        model_name,
        messages,
        max_tokens = 500,
        tools = [calculator_tool]
    )

    if success:
        logger.info("✅ LLM tools use test successful!")
        logger.info("-" * 50)
        logger.info("LLM response:")
        logger.info(resp_content)
        logger.info("=" * 50)

        # Check if tool call is present and correct
        tool_call_success = False
        if full_response and "choices" in full_response:
            message = full_response["choices"][0]["message"]
            if "tool_calls" in message:
                logger.info("✅ LLM returned tool call information")
                tool_calls = message["tool_calls"]
                logger.info(f"Tool Calls: {tool_calls}")

                # Check if calculator tool was called
                for tool_call in tool_calls:
                    if tool_call.get("function", {}).get("name") == "calculator":
                        expr = tool_call.get("function", {}).get("arguments", "")
                        logger.info(f"Calculator tool called with expression: {expr}")
                        tool_call_success = True

        if not tool_call_success:
            logger.warning("⚠️ LLM response did not include expected tool call")

        return True, resp_content
    else:
        logger.error("❌ LLM tools use test failed!")
        logger.error("=" * 50)
        return False, resp_content


def main():
    """Main function, using argparse to handle command-line arguments

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description = "LLM Validation Tool - Test LLM connection, capabilities, and tools use"
    )

    # Test type parameter
    parser.add_argument(
        "test_type",
        nargs = '?',
        choices = ["connection", "capabilities", "tools"],
        default = "capabilities",
        help = "Test type: connection (test connection), capabilities (test question generation), tools (test tool usage) (default: capabilities)"
    )

    # Configuration parameters
    parser.add_argument(
        "--api-key",
        help = "LLM API key (overrides .env file)"
    )

    parser.add_argument(
        "--base-url",
        help = "LLM API base URL (overrides .env file)"
    )

    parser.add_argument(
        "--model-name",
        help = "LLM model name (overrides .env file)"
    )

    # Log level
    parser.add_argument(
        "-v", "--verbose",
        action = "store_true",
        help = "Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level = log_level,
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers = [logging.StreamHandler()]
    )

    logger.info(f"Starting LLM validation test: {args.test_type}")

    # Select corresponding test function based on test type
    test_functions = {
        "connection": test_llm_connection,
        "capabilities": test_llm_capabilities,
        "tools": test_llm_tools_use
    }

    test_func = test_functions.get(args.test_type)
    if not test_func:
        logger.error(f"Unknown test type: {args.test_type}")
        logger.error("Valid test types: connection, capabilities, tools")
        sys.exit(1)

    # Run test
    try:
        test_result, resp_content = asyncio.run(
            test_func(
                api_key = args.api_key,
                base_url = args.base_url,
                model_name = args.model_name
            )
        )
        logger.info(f"Test Result: {test_result}")
        if not test_result:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test failed with unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
