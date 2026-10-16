import json

class Response:
    def __init__(self, response_id, output = None, status = None, error = None):
        self.response_id = response_id
        self.output      = output
        self.status        = status
        self.error         = error
        
        self.input_tokens  = 0
        self.output_tokens = 0
        self.thinking_tokens = 0
        self.cache_read    = None
        self.cache_write   = None
        self.role          = "assistant"
        self.model         = None
        self.tier          = None
        
        self.model_specific_data = None

    def get_output(self):
        return self.output

    def set_usage(self, input_tokens, output_tokens, cache_read = None, cache_write = None, thinking_tokens = None):
        self.input_tokens  = input_tokens
        self.output_tokens = output_tokens
        self.cache_read    = cache_read
        self.cache_write   = cache_write
        self.thinking_tokens = thinking_tokens

    def set_attributes(self, role, model, tier):
        self.role  = role
        self.model = model
        self.tier  = tier
        

    def set_model_specifid_data(self, data):
        self. model_specific_data = data

    def dump(self):
        return json.dumps({
            "id":            self.response_id,
            "output":        self.output,
            "input_tokens":  self.input_tokens,
            "output_tokens": self.output_tokens,
            "thinking_tokens": self.thinking_tokens,
            "cache_read":    self.cache_read,
            "cache_write":   self.cache_write,
            "role":          self.role,
            "model":         self.model,
            "tier":          self.tier,
            "specific_data": self.model_specific_data
        })
