import json

from modules.agents.ollama_agent import OllamaAgent
from modules.agents.openai_agent import OpenaiAgent
from modules.agents.test_agent import TestAgent
from modules.agents.claude_agent import ClaudeAgent

# config = {
#     'experiment_name': 'claude',
#     'classification_model_doc_type': 'claude-3-5-haiku-latest',
#     'classification_model_proc_type': 'claude-3-5-haiku-latest',
#     'validation_model': 'claude-3-5-haiku-latest'
# }

config = {
    'experiment_name': 'ollama_anonymization_test',
    'classification_model_doc_type': 'gemma3:1b',
    'classification_model_proc_type': 'gemma3:1b',
    'validation_model': 'gemma3:1b'
}

with open('{}.json'.format(config['experiment_name']), 'w') as f:
    json.dump(config, f)

AGENT_TYPE = None
for name in ['openai', 'test', 'ollama', 'claude']:
    if name in config['experiment_name']:
        AGENT_TYPE = name

assert AGENT_TYPE is not None, "Please add prefix to your experiment"

INSTRUCTION_KEY = {'test': 'test', 'openai': 'developer', 'ollama': 'system', 'claude': 'system'}.get(AGENT_TYPE)

AI_AGENT = {'test': TestAgent, 'openai': OpenaiAgent, 'ollama': OllamaAgent, 'claude': ClaudeAgent}.get(AGENT_TYPE)
