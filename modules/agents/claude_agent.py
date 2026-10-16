import anthropic

class ClaudeAgent:
    def __init__(self, model_name):
        self.model_name = model_name

        try:
            with open("creds/univ2_claude_key", 'r') as f:
                api_key = f.readline()[:-1]
            self.client = anthropic.Anthropic(api_key=api_key)
        except FileNotFoundError:
            self.client = anthropic.Anthropic()

    def generate(self, messages):
        # Concatenate all 'content' values from messages with role='system'
        system = "".join([msg["content"] for msg in messages if msg.get("role") == "system"])
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=1000,
            system=system,
            messages=user_messages)
        return response.content[0].text