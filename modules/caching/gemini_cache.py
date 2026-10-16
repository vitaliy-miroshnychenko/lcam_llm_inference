import datetime
import hashlib

from google import genai
from google.genai import types


def create_cach_name(model_name, experiment_id, system_instruction):
    instr_hash = hashlib.sha256(system_instruction.encode('utf-8')).hexdigest()
    return "{}; experiment-id:{}; hash:{}".format(model_name, experiment_id, instr_hash)


class GeminiCache:
    def __init__(self, api_key, model_name, system_instruction):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name  # "gemini-2.5-flash"
        self.system_instruction = system_instruction

    def create_cache(self, experiment_id, context_to_cache):
        cache = self.cache_exists(experiment_id)
        if not cache:
            print("Cache does not exist")
            cache = self.client.caches.create(
                model=self.model_name,
                config=types.CreateCachedContentConfig(
                    display_name=create_cach_name(self.model_name, experiment_id, self.system_instruction),
                    contents=[context_to_cache],
                    expire_time=str(datetime.datetime.now() + datetime.timedelta(days=2)).split('.')[0] + 'Z'
                    # system_instruction=system_instruction, # TODO: do we need this?
                ),
            )
        else:
            print("Cache exists")
        return cache

    def cache_exists(self, experiment_id):
        for i in self.client.caches.list():
            display_name = create_cach_name(self.model_name, experiment_id, self.system_instruction)
            if i.display_name == display_name:
                return i
        return False


if __name__ == '__main__':
    model_name = "gemini-2.5-flash"
    with open('creds/gemini.txt', 'r') as f:
        api_key = f.read()[:-1]

    instruction = 'test'
    cache = GeminiCache(api_key, model_name, instruction)

    cache.create_cache('test cache', 'inst test' * 600)
