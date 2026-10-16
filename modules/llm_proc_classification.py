from collections import Counter

from modules.llm_config import classification_model_proc_type
from pipeline_configs.dict2json import INSTRUCTION_KEY, AI_AGENT

instruction_code = """
Ти - спеціаліст у галузі цивільного права та цивільного процесуального права України. 
У нас є процесуальні документи, постановлені судом під час розгляду справи на різних стадіях провадження у справі в порядку цивільного судочинства.

Задача: визначити код кожного процесуального документу відповідно до кодів процесуальних рішень

Обов'язково дотримуйся вимог:
- Написати лише код процесуального рішення, що відповідає документу
- Якщо не вдається категоризувати документ, повертай -1
- Повертай лише номер строки! (він - до символа ":")
"""

CELLS_NUM = {
    'рішення': '3',
    'постанова': '2',
    'окрема ухвала': '6',
    'судовий наказ': '4',
    'ухвала': '5'
}


def generate_messages(instruction_code, doc_type_instruction, line):
    return [{"role": INSTRUCTION_KEY,
             "content": instruction_code
             },
            {
                "role": INSTRUCTION_KEY,
                "content": 'Коди процесуальних рішень:{}'.format(doc_type_instruction),
            },
            {
                "role": "user",
                "content": line.html_anonymized[:8000],
            }]


def base_classify(line, doc_type_instruction):
    messages = generate_messages(instruction_code, doc_type_instruction, line)
    agent = AI_AGENT(classification_model_proc_type)
    res = []
    for _ in (range(3)):
        content = agent.generate(messages).replace('\n', '')
        res.append(content)

    print("Base classify", Counter(res))
    mc = Counter(res).most_common(1)[0][0]
    print('\tLLM decision: "{}"'.format(mc))
    return mc


def proc_classify(line, kb_tree):
    doc_type = line.ai_doc_type

    if doc_type in ['рішення', 'постанова', 'окрема ухвала', 'судовий наказ', 'ухвала']:
        next_cell = CELLS_NUM[doc_type]
        tree = kb_tree
        decision_code = [next_cell]

        while tree[next_cell][2] == 'root':
            tree = tree[next_cell][0]
            local_taxonomy = '\n'.join([str(k + 1) + ':' + tree[c][1] for k, c in enumerate(tree)])
            print('\t\tlocal_taxonomy\n', local_taxonomy)
            next_cell = base_classify(line, local_taxonomy)
            decision_code.append(next_cell)
            if next_cell == '-1' or next_cell not in tree:
                return '.'.join(decision_code), '.'.join(decision_code)

        if next_cell == '-1':
            return '.'.join(decision_code), '.'.join(decision_code)

        return '.'.join(decision_code), '.'.join(decision_code)
    return '-1', '-1'
