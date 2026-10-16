from openai import OpenAI
import os
import time
from .adapter import Adapter
import json
from modules.logger import Logger
from collections.abc import Sequence
from .response import Response


class OpenaiAdapter(Adapter):
    DEFAULT_API_KEY_NAME = "OPENAI_API_KEY"
    AVAILABLE_MODELS = [
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano"
    ]
    MAX_TOKENS = 2000

    def __init__(self, model_name, api_key=None, api_key_env=None, api_key_file=None):
        super().__init__(model_name, api_key, api_key_env, api_key_file)
        self.client = OpenAI(api_key=self.api_key)
        self.logger = Logger()

    def execute(self, document_id = None):
        system = []
        for ctx in self.context:
            entry = {"role": "system",  "content": ctx["content"]}
            system.append(entry)

        # Only user messages
        user_messages = []
        for msg in self.messages:
            entry = {"role": "user"}
            if msg.get("role") == "assistant":
                entry["role"] = "assistant"
            
            if isinstance(msg["content"], str): #shorthand message
                entry["content"] = msg["content"]
            elif isinstance(msg["content"], Sequence):
                content_blocks = []
                for content_block in msg["content"]:
                    if content_block["type"] == "text":
                        element = {"type": "input_text", "text": content_block["text"]}
                    if content_block["type"] == "document":
                        element = {"type": "input_text", "text": content_block["data"]}
                        #if 'context' in content_block:
                        #    element['context'] = content_block['context']
                    content_blocks.append(element)
                entry["content"] = content_blocks
            user_messages.append(entry)

        system.extend(user_messages)
        start_time = time.time()
        raw_response = self.client.responses.create(
            model=self.model_name,
            input = system,
            max_output_tokens=self.MAX_TOKENS
        )
        elapsed_time = time.time() - start_time
        self.logger.debug(f"OpenaiAdapter response: {raw_response}. Time: {elapsed_time}")
        response = self.parse_response(raw_response)
        self.record_response(system, response, raw_response, document_id, elapsed_time)
        
        return response

    def record_response(self, system, response, raw_response, document_id, elapsed_time):
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
                "messages": json.dumps(self.messages, ensure_ascii=False),
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
        response = Response(raw_response.id, raw_response.output_text, raw_response.status, raw_response.error)
        response.set_attributes("assistant", raw_response.model, raw_response.service_tier)
        response.set_usage(
            raw_response.usage.input_tokens,
            raw_response.usage.output_tokens,
            raw_response.usage.input_tokens_details.cached_tokens,
            None, # NO writes in OpenAI
            raw_response.usage.output_tokens_details.reasoning_tokens
        )
        return response
    
    def execute_batch(self, messages):
        results = []
        for msg in messages:
            self.messages = [msg]
            results.append(self.execute())
        return results
