import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("Reflector")


class Reflector:
    """
    Reflector class for enhancing agent responses through self-reflection and criticism
    """

    def __init__(
        self,
        client = None,
        model: str = None,
        config: Dict[str, Any] = None
    ):
        self.client = client
        self.model = model
        self.config = config or {}

        # Extract parameters from config
        self.temperature = self.config.get("temperature", 0.7)
        self.disabled = self.config.get("disabled", False)
        self.max_tokens = self.config.get("max_tokens", None)

        logger.debug(f"Reflector initialized, model: {model}, disabled: {self.disabled}")

    def apply_reflection(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Apply reflection to a conversation

        This method examines the conversation history and adds reflection
        to improve the agent's reasoning process.

        Args:
            messages: Conversation messages

        Returns:
            Potentially modified messages
        """
        if self.disabled or not self.client or not self.model:
            return messages

        if len(messages) < 2:
            return messages

        # Extract the last user query
        last_user_msg = None
        last_assistant_msg = None

        # Find the most recent user-assistant exchange
        for i in range(len(messages)-1, 0, -1):
            if messages[i]["role"] == "assistant" and last_assistant_msg is None:
                last_assistant_msg = messages[i]["content"]
            elif messages[i]["role"] == "user" and last_assistant_msg is not None and last_user_msg is None:
                last_user_msg = messages[i]["content"]
                break

        if not last_user_msg or not last_assistant_msg:
            return messages

        # Reflect on the response
        improved_response = self.reflect(last_user_msg, last_assistant_msg)

        # If reflection improved the response, update the last assistant message
        if improved_response and improved_response != last_assistant_msg:
            for i in range(len(messages)-1, 0, -1):
                if messages[i]["role"] == "assistant":
                    messages[i]["content"] = improved_response
                    break

        return messages

    def _build_reflection_prompt(self, query: str, current_response: str) -> str:
        """
        Build reflection prompt

        Args:
            query: User query
            current_response: Current LLM-generated response

        Returns:
            Reflection prompt text
        """
        return f"""
Please evaluate the quality of the following response, which is an answer to a user query. After evaluation, provide an improved version if necessary:

User Query: {query}

Current Response:
{current_response}

Please evaluate the response based on the following aspects:
1. Accuracy: Is the information accurate?
2. Relevance: Does the response fully answer the user's query?
3. Completeness: Does it cover all important aspects?
4. Clarity: Is the expression clear and understandable?
5. Logicality: Are the arguments logical?
6. Format: Is the format appropriate and easy to read?

Please provide your improved response below. If no improvement is needed, just repeat the original response.
"""

    def _extract_improved_response(self, reflection_content: str) -> str:
        """
        Extract improved response from reflection content

        Args:
            reflection_content: Full reflection content from LLM

        Returns:
            Extracted improved response or None if not found
        """
        try:
            # Simple extraction - try to find the improved response section
            # This is a basic implementation; can be enhanced with more robust parsing

            # Check if there's a clear section indicating the improved response
            lines = reflection_content.split("\n")
            improved_response = []
            capture = False

            for line in lines:
                line = line.strip()

                # Look for indicators of improved response
                if any(keyword in line.lower() for keyword in [
                    "improved response", "revised response", "better answer",
                    "corrected response", "enhanced response"
                ]):
                    capture = True
                    continue

                if capture and line:
                    improved_response.append(line)

            # If no specific section found, check if the reflection is different from original
            if improved_response:
                return "\n".join(improved_response)
            else:
                # If no clear section, return the entire reflection content as fallback
                return reflection_content

        except Exception as e:
            logger.error(f"Error extracting improved response: {str(e)}")
            return None

    def reflect(self, query: str, current_response: str) -> str:
        """
        Reflect on and improve the current response

        Args:
            query: User query
            current_response: Current LLM-generated response

        Returns:
            Improved response or original response (if no improvement)
        """
        if self.disabled or not self.client or not self.model:
            logger.debug("Reflector is disabled or not fully configured, skipping reflection process")
            return current_response

        if not current_response.strip():
            logger.debug("Current response is empty, skipping reflection process")
            return current_response

        try:
            # Build reflection prompt
            reflection_prompt = self._build_reflection_prompt(query, current_response)

            logger.debug(f"Sending reflection prompt to LLM")

            # Request LLM for reflection
            response = self.client.chat.completions.create(
                model = self.model,
                messages = [
                    {
                        "role": "system",
                        "content": "You are a high-quality response analyzer. Your task is to evaluate and improve given responses."
                    },
                    {
                        "role": "user",
                        "content": reflection_prompt
                    }
                ],
                temperature = self.temperature,
                max_tokens = self.max_tokens
            )

            # Extract reflection content
            reflection_content = response.choices[0].message.content

            logger.debug(f"Received reflection content: {reflection_content[:100]}...")

            # Extract improved response
            improved_response = self._extract_improved_response(reflection_content)

            # If improved response is extracted, return it
            if improved_response and improved_response != current_response:
                logger.info("Reflection process produced an improved response")
                return improved_response
            else:
                logger.debug("Reflection process did not produce significant improvement")
                return current_response

        except Exception as e:
            logger.error(f"Error during reflection process: {str(e)}")
            # Return original response on error
            return current_response
