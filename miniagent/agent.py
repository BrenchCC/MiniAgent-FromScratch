import os
import re
import sys
import json
import time
import logging
from typing import Any, Callable, Dict, List, Optional, Union

from tenacity import retry, stop_after_attempt, wait_random_exponential


sys.path.append(os.getcwd())

from miniagent.utils import parse_json, Reflector   
from miniagent.tools import get_registered_tools, get_tool, get_tool_description

logger = logging.getLogger("MiniAgent")

class MiniAgent():
    """
    MiniAgent main class for MiniAgent
    """
    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: str = "You are a helpful assistant called MiniAgent created by brench that can use tools to get information and perform tasks.",
        use_reflector: bool = True,
        **kwargs
    ):
        """
        Initialize MiniAgent

        Args:
            model: LLM model name
            api_key: API key for LLM service
            base_url: Base URL for LLM service (optional)
            temperature: Temperature for LLM sampling (default: 0.7)
            system_prompt: System prompt for MiniAgent (default: "You are a helpful assistant that can use tools to get information and perform tasks.")
            use_reflector: Whether to use reflector for response improvement (default: False)
            **kwargs: Additional keyword arguments for LLM client   
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.top_p = top_p
        self.system_prompt = system_prompt
        self.tools = []
        self.client = None
        self.use_reflector = use_reflector
        
        # Initialize the LLM client
        self._init_llm_client()
        
        # Initialize reflector if enabled
        if use_reflector:
            self.reflector = Reflector(self.client, self.model)
        else:
            self.reflector = None
        
        logger.info(f"MiniAgent initialized with model {self.model}, temperature {self.temperature}, top_p {self.top_p}, system_prompt {self.system_prompt}, use_reflector {self.use_reflector}")

    # TODO: implement the rest of the methods