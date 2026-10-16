from openai import OpenAI


class OpenaiAgent:
    def __init__(self, model_name):
        self.model_name = model_name

        with open("creds/univ2_openai_key", 'r') as f:
            self.client = OpenAI(api_key=f.readline()[:-1])

    def generate(self, messages):
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages)
        return completion.choices[0].message.content
