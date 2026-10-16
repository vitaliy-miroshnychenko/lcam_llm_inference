# classification_model_proc_type = 'gemma3:12b'
# classification_model_doc_type = 'gemma3:4b'

# classification_model_proc_type = 'gemma3:1b'
# classification_model_doc_type = 'gemma3:1b'
import os
import json

from pipeline_configs.dict2json import config

classification_model_proc_type = config['classification_model_proc_type']
classification_model_doc_type = config['classification_model_doc_type']
code_validation_model = config.get('validation_model', 'gemma3:4b')

os.makedirs('feature_store/metadata/{}/'.format(config['experiment_name']), exist_ok=True)
with open('feature_store/metadata/{}/config.json'.format(config['experiment_name']), 'w') as f:
    json.dump(config, f)

# TODO: try https://huggingface.co/SherlockAssistant/Mistral-7B-Instruct-Ukrainian

os.makedirs('feature_store/metadata/{}'.format(config['experiment_name']), exist_ok=True)
