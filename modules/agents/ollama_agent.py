import ollama


class OllamaAgent:
    def __init__(self, model_name):
        self.model_name = model_name

    def generate(self, messages):
        response = ollama.chat(
            model=self.model_name,
            think=False,
            messages=messages)
        return response.message.content
