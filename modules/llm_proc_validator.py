import Levenshtein
import numpy as np

from collections import Counter

from modules.llm_config import code_validation_model
from pipeline_configs.dict2json import INSTRUCTION_KEY, AI_AGENT

instruction_code = """
Ти - спеціаліст у галузі цивільного права та цивільного процесуального права України. 
У нас є процесуальний документ, постановлений судом під час розгляду справи на різних стадіях провадження у справі в порядку цивільного судочинства.

Задача: відповісти чи надане процесуальне рішення відповідає тексту документу

Обов'язково дотримуйся вимог:
- Повертай лише одне слово з набору (так, ні)
- Відповідь - одне слово
"""


def generate_messages(instruction_code, code_description, line):
    return [{"role": INSTRUCTION_KEY,
             "content": instruction_code
             },
            {
                "role": "system",
                "content": 'Процесуальне рішення:{}'.format(code_description),
            },
            {
                "role": "user",
                "content": line.html_anonymized,
            },
            ]


RESPONSES = ['ні', 'так']


def find_nearest_key(word):
    min_distance = float('inf')
    best_key = None

    for key in RESPONSES:
        distance = Levenshtein.distance(word.lower(), key.lower())
        if distance < min_distance:
            min_distance = distance
            best_key = key

    return best_key


WRONG_CODE = 'WRONG CODE'


def get(line, code, kb_data):
    print('Code:', code)
    if code in set(kb_data.reset_index()['code']):
        try:
            return kb_data.loc[line.ai_doc_type].loc[code].description
        except Exception as e:
            print(e)
            return WRONG_CODE
    else:
        return WRONG_CODE


def base_validate(line, code, kb_data):
    code_description = get(line, code, kb_data)
    print('Code description:', code_description)
    if code_description == WRONG_CODE:
        print("{}: {}".format(WRONG_CODE, code))
        return False

    res = []
    agent = AI_AGENT(code_validation_model)
    messages = generate_messages(instruction_code, code_description, line)
    for _ in (range(3)):
        content = agent.generate(messages).replace('\n', '')
        res.append(content)

    print("Validation", Counter(res))
    mc = Counter(res).most_common(1)[0][0]
    print('\tValidation decision: "{}"'.format(mc))
    return mc == RESPONSES[True]
