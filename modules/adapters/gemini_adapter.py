from collections.abc import Sequence

import time
import json

from .adapter import Adapter
from modules.logger import Logger
from .response import Response

from modules.agents.gemini_agent import GeminiAgent


class GeminiAdapter(Adapter):
    DEFAULT_API_KEY_NAME = "GEMINI_API_KEY"
    AVAILABLE_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]
    MAX_TOKENS = 2000

    def __init__(self, model_name, api_key=None, api_key_env=None, api_key_file=None):
        super().__init__(model_name, api_key, api_key_env, api_key_file)
        self.model_name = model_name
        self.client = GeminiAgent(model_name, api_key=api_key)
        self.logger = Logger()

    def execute(self, document_id=None):
        system = []
        for ctx in self.context:
            entry = {"role": "system", "content": ctx["content"]}
            system.append(entry)
        # Only user messages
        user_messages = []
        for msg in self.messages:
            entry = {"role": "user"}
            if msg.get("role") == "assistant":
                entry["role"] = "assistant"

            if isinstance(msg["content"], str):  # shorthand message
                entry["content"] = msg["content"]
            elif isinstance(msg["content"], Sequence):
                content_blocks = []
                for content_block in msg["content"]:
                    if content_block["type"] == "text":
                        element = content_block["text"]
                    elif content_block["type"] == "document":
                        element = content_block["data"]
                    else:
                        raise
                        # if 'context' in content_block:
                        #    element['context'] = content_block['context']
                    content_blocks.append(element)
                entry["content"] = '\n'.join(content_blocks)
            user_messages.append(entry)

        system.extend(user_messages)
        start_time = time.time()

        raw_response = self.client.generate(system)
        # raw_response = self.client.responses.create(
        #     model=self.model_name,
        #     input=system,
        #     max_output_tokens=self.MAX_TOKENS
        # )
        elapsed_time = time.time() - start_time
        self.logger.debug(f"GeminiAdapter response: {raw_response}. Time: {elapsed_time}")
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
        response = Response(raw_response['id'], raw_response['output_text'], raw_response['status'],
                            raw_response['error'])
        response.set_attributes("assistant", self.model_name, 'unknown')  # raw_response.service_tier)
        response.set_usage(
            raw_response['input_tokens'],
            raw_response['output_tokens'],
            raw_response['cached_tokens'],
            None,  # NO writes in OpenAI
            raw_response['reasoning_tokens']
        )
        return response

    def execute_batch(self, messages):
        results = []
        for msg in messages:
            self.messages = [msg]
            results.append(self.execute())
        return results

# TODO: add cache
# https://ai.google.dev/api/caching

# with open('creds/gemini.txt', 'r') as f:
#     api_key = f.read()[:-1]
#
# from google import genai
# from google.genai import types
#
# client = genai.Client(api_key=api_key)
#
# # document = client.files.upload(file=media / "a11.txt")
#
# model_name = "gemini-2.5-flash"
#
# cache = client.caches.create(
#     model=model_name,
#     config=types.CreateCachedContentConfig(
#         contents=['Test myfail ' * 1000],
#         system_instruction="You are an expert analyzing transcripts.",
#     ),
# )
# print(cache)
#
# response = client.models.generate_content(
#     model=model_name,
#     contents="Please summarize this transcript",
#     config=types.GenerateContentConfig(cached_content=cache.name),
# )
# print(response.text)
