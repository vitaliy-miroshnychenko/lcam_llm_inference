from google import genai
from google.genai import types

from modules.caching.gemini_cache import GeminiCache


# with open('creds/gemini.txt', 'r') as f:
#     api_key = f.read()[:-1]


class GeminiAgent:
    def __init__(self, model_name, api_key):
        self.model_name = model_name
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)
        self.cache = None
        self.cache_name = None

    def generate(self, messages_all):
        system_instruction = "Instruction:" + '\n'.join(
            [i['content'] for i in messages_all if i['role'] != 'user']) + "\n\n"
        # print('chars', len(system_instruction))
        # print('words', len(system_instruction.split(' ')))

        if self.cache is None:
            self.cache = GeminiCache(self.api_key, self.model_name, system_instruction)
            cache_object = self.cache.create_cache(self.model_name, system_instruction)
            self.cache_name = str(cache_object.name)
            print("Cache created")
            print(cache_object)

        message = "Context: " + '\n'.join([i['content'] for i in messages_all if i['role'] == 'user'])
        messages = system_instruction + message

        response = self.client.models.generate_content(
            model=self.model_name,  # "gemini-2.5-flash"
            contents=messages,
            config=types.GenerateContentConfig(cached_content=self.cache_name),
        )

        # response = Response
        # (raw_response.id, raw_response.output_text, raw_response.status, raw_response.error)
        # response.set_attributes("assistant", raw_response.model, raw_response.service_tier)
        # response.set_usage(
        #     raw_response.usage.input_tokens,
        #     raw_response.usage.output_tokens,
        #     raw_response.usage.input_tokens_details.cached_tokens,
        #     None,  # NO writes in OpenAI
        #     raw_response.usage.output_tokens_details.reasoning_tokens
        # )

        return {'id': response.response_id, 'output_text': response.text,
                'status': "Done", 'error': "None",
                'input_tokens': response.usage_metadata.prompt_token_count,
                'output_tokens': response.usage_metadata.candidates_token_count,
                'cached_tokens': 0,
                'reasoning_tokens': response.usage_metadata.thoughts_token_count
                }
