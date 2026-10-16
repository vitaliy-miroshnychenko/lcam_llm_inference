import anthropic
import time
import sys
import os
from .adapter import Adapter
from .response import Response
import json
from modules.logger import Logger
from collections.abc import Sequence



class ClaudeAdapter(Adapter):
    DEFAULT_API_KEY_NAME = "ANTHROPIC_API_KEY"
    AVAILABLE_MODELS = [
        "claude-opus-4-1-20250805",
        "claude-opus-4-1",
        "claude-opus-4-20250514",
        "claude-opus-4-0",
        "claude-sonnet-4-20250514",
        "claude-sonnet-4-0",
        "claude-3-7-sonnet-20250219",
        "claude-3-7-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]

    def __init__(self, model_name, api_key=None, api_key_env=None, api_key_file=None):
        super().__init__(model_name, api_key, api_key_env, api_key_file)
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.logger = Logger()

    def execute(self, document_id = None):
        # Concatenate all 'content' values from context with role='system'
        system = [] #"".join([ctx["content"] for ctx in self.context if ctx.get("role") == "system"])
        for ctx in self.context:
            entry = {"type": "text", "text": ctx["content"]}
            if ctx.get("cache"):
                entry["cache_control"] = {"type": "ephemeral"}
            system.append(entry)

        # Only user messages
        user_messages = []
        for msg in self.messages:
            entry = {"role": "user"}
            if msg.get("role") == "assistant":
                entry["role"] = "assistant"
            
            if isinstance(msg["content"], str): #shorthand message
                entry["content"] = msg["content"]
                if msg.get("cache"):
                    entry["cache_control"] = {"type": "ephemeral"}
            elif isinstance(msg["content"], Sequence):
                content_blocks = []
                for content_block in msg["content"]:
                    if content_block["type"] == "text":
                        element = {"type": "text", "text": content_block["text"]}
                    if content_block["type"] == "document":
                        element = {
                            "type": "document",
                            "source": {
                                "type":       content_block["content_type"],
                                "media_type": content_block["media_type"],
                                "data":       content_block["data"]
                            }
                        }
                        if content_block.get("citations"):
                            element["citations"] = {"enabled": True}
                        if 'title' in content_block:
                            element["title"] = content_block['title']
                        if 'context' in content_block:
                            element['context'] = content_block['context']
                    if "cache" in content_block and content_block["cache"]:
                        element["cache_control"] = {"type": "ephemeral"}
                    content_blocks.append(element)
                    
                entry["content"] = content_blocks
            user_messages.append(entry)

        start_time = time.time()
        try:
            raw_response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.MAX_TOKENS,
                system=system,
                messages=user_messages
            )
        except anthropic.APIStatusError as e:
            if e.status_code == 429:
                # The 'response' attribute of APIStatusError holds the httpx.Response object
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    print(f"Rate limited. Retry after: {retry_after} seconds.")
                    # Implement your custom waiting logic here, e.g., time.sleep(int(retry_after))
                else:
                    print("Rate limited, but no Retry-After header found.")
            else:
                print(f"An API error occurred: {e}")
            raise e
        except httpx.HTTPStatusError as e:
            # This might catch lower-level httpx errors if not wrapped by anthropic.APIStatusError
            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    print(f"Rate limited (HTTPStatusError). Retry after: {retry_after} seconds.")
            raise e
                    
        elapsed_time = time.time() - start_time
        self.logger.debug(f"ClaudeAdapter response: {raw_response}; Time: {elapsed_time}")
        response = self.parse_response(raw_response)
        self.record_response(system, user_messages, response, raw_response, document_id, elapsed_time)

        return response

    def record_response(self, system, user_messages, response, raw_response, document_id, elapsed_time):
        # Store response in request_log table
        if hasattr(self, 'storage') and self.storage is not None:
            try:
                response_json = json.dumps(raw_response.__dict__, default=str)
            except Exception:
                response_json = str(raw_response)
            log_data = {
                "document_id": document_id,
                "model": self.model_name,
                "context": json.dumps(system, ensure_ascii=False),
                "messages": json.dumps(user_messages, ensure_ascii=False),
                "response": response_json,
                "response_id": response.response_id,
                "output": response.output,
                "status": response.status,
                "error": response.error,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "thinking_tokens": response.thinking_tokens,
                "cache_read": response.cache_read,
                "cache_write": response.cache_write,
                "tier": response.tier,
                "model_specific_data": json.dumps(response.model_specific_data),
                "elapsed_time": elapsed_time
            }
            self.storage.write_record("request_log", log_data)

    
    def parse_response(self, raw_response):
        response = Response(raw_response.id, raw_response.content[0].text)
        response.set_attributes(raw_response.role, raw_response.model, raw_response.usage.service_tier)
        response.set_usage(raw_response.usage.input_tokens, raw_response.usage.output_tokens,
                           raw_response.usage.cache_read_input_tokens, raw_response.usage.cache_creation_input_tokens)
        return response
        
    def execute_batch(self, messages):
        results = []
        for msg in messages:
            self.messages = [msg]
            results.append(self.execute())
        return results
