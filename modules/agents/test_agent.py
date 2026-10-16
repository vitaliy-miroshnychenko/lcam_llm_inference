import numpy as np


class TestAgent:
    def __init__(self, model_name):
        self.model_name = model_name

    def generate(self, messages):
        return str(np.random.rand() > 0.5)
