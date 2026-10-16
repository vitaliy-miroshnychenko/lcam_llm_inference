import Levenshtein

from collections import Counter

from modules.llm_config import classification_model_doc_type
from pipeline_configs.dict2json import INSTRUCTION_KEY, AI_AGENT

instruction = """
Ти - спеціаліст у галузі цивільного права та цивільного процесуального права України. 
У нас є процесуальні документи, постановлені судом під час розгляду справи на різних стадіях провадження у справі в порядку цивільного судочинства.

Твоя задача - визначити вид кожного процесуального документа відповідно до наступного переліку видів документів:

- рішення
- ухвала
- окрема ухвала
- постанова
- судовий наказ

Вимоги:
- дай відповідь 1 чи 2-ма словами
- відповідь - вид документу зі списку вище
"""

doc_types = ['ухвала',
             'постанова',
             "рішення",
             "судовий наказ",
             "окрема ухвала"]


def find_nearest_key(word, doc_types):
    min_distance = float('inf')
    best_key = None

    for key in doc_types:
        distance = Levenshtein.distance(word.lower(), key.lower())
        if distance < min_distance:
            min_distance = distance
            best_key = key

    return best_key


def type_classify(anonymized_hmtl):
    res = []
    N = 3
    agent = AI_AGENT(classification_model_doc_type)
    for _ in (range(N)):
        messages = [{"role": INSTRUCTION_KEY,
                     "content": instruction
                     },
                    {
                        "role": "user",
                        "content": anonymized_hmtl[:8000],
                    }]

        content = agent.generate(messages)
        res.append(find_nearest_key(content, doc_types))

    mc, counter = Counter(res).most_common(1)[0]
    return mc.lower(), round(counter / N, 2)
