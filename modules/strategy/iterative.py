import pandas as pd
import time
from modules.logger import Logger
from .strategy import Strategy
from modules.adapters.adapter_factory import AdapterFactory
import re

from tqdm import tqdm
from sklearn.utils import shuffle

class Iterative(Strategy):
    STRATEGY_NAME = "iterative"
    instruction_code = """
Ти - спеціаліст у галузі цивільного права та цивільного процесуального права України. 
У нас є процесуальні документи, постановлені судом під час розгляду справи на різних стадіях провадження у справі в порядку цивільного судочинства.

Задача: визначити код кожного процесуального документу відповідно до кодів процесуальних рішень

Обов'язково дотримуйся вимог:
- Написати лише код процесуального рішення, що відповідає документу
- Повертай лише номер рядка! 
- Переконайся, що повертаєш лише числовий код без букв або інших символів
- Якщо не вдається категоризувати документ, повертай -1
"""

    def __init__(self):
        from modules.logger import Logger
        self.logger = Logger()
        self.documents = []
        self.categories = []
        self.classification_config = None

    def execute(self):
        # Create Adapter
        self.adapter = AdapterFactory.get_adapter(
            self.config["model_name"],
            self.config.get_api_key()
        )
        self.adapter.set_storage(self.storage)
        self.logger.debug(f"Using model: {self.config['model_name']}")

        if self.adapter is None:
            raise ValueError("Adapter must be set before executing the strategy.")

        result = []
        documents = self.storage.load_data()
        if len(documents) == 0:
            self.logger.debug("No documents to classify.")
            return result

        documents = shuffle(documents)
        # documents = sorted(documents, key=lambda x: str(x['case_number']))
        tq_docs = tqdm(documents)

        for idx, document in enumerate(documents):
            print(idx)
            # print(document)
            start_time = time.time()
            res = self.classify_document(document, document['judgment_code'])
            elapsed_time = time.time() - start_time
            self.logger.log(
                f"Classification result: for document {document['document_id']}: {res['code']}. True category: {document.get('true_category', 'N/A')}")
            self.logger.debug(res)
            result.append(res)

            # Prepare data for classification_result table
            data = {
                "document_id": res.get("document_id"),
                "predicted_category": res.get("code"),
                "experiment_id": getattr(self.storage, "experiment_id", None),
                "case_number": getattr(document, "case_number", None) if hasattr(document,
                                                                                 "case_number") else document.get(
                    "case_number", None),
                "true_category": getattr(document, "true_category", None) if hasattr(document,
                                                                                     "true_category") else document.get(
                    "true_category", None),
                "elapsed_time": elapsed_time
            }
            self.storage.write_record("result", data)
            tq_docs.update()

        return result

    def classify_document(self, document, index):
        taxonomy = self.storage.load_taxonomy(index)

        running_head = ""
        code = index
        while len(taxonomy) > 0:
            code = self.classify_next_level(document, taxonomy, running_head, code)
            # print('codes', [el['code'] for el in taxonomy])
            print("code", "'{}'".format(code))
            selected_titles = [el['title'] for el in taxonomy if el['code'] == code]
            # print("selected_titles", selected_titles)
            if len(selected_titles) == 0:
                break
            title = selected_titles[0]

            running_head += " " + title
            taxonomy = self.storage.load_taxonomy(code)
            # print('taxonomy', taxonomy)
            print('title', title)
        print("=" * 200)

        return {'document_id': document['document_id'], 'code': code}

    def classify_next_level(self, document, taxonomy, running_head, current_code):

        options = [f"{element['code'].replace(str(current_code) + '.', '')} {running_head}{element['title']}" for
                   element in taxonomy]
        # options = [f"{element['code']} {running_head}{element['title']}" for element in taxonomy]
        # print(options)

        context1 = {
            "type": "text",
            "content": self.instruction_code,
        }
        context2 = {
            "type": "text",
            "content": "Текст документу для аналізу:\n\n " + document['html'],
            "cache": True
        }
        context3 = {
            "type": "text",
            "content": "Коди процесуальних рішень: " + ",\n".join(options),
            "cache": True
        }
        self.adapter.context = []
        self.adapter.messages = []

        self.adapter.add_context(context1)
        self.adapter.add_context(context2)
        self.adapter.add_context(context3)
        # message = {"role": "user", "content": "Визнач код процесуального рішення для цього документу відповідно до наданих варіантів: " + ",\n".join(options)}
        message = {"role": "user",
                   "content": "Визнач код процесуального рішення для цього документу відповідно до наданих варіантів. Поверни лише числове значення без букв або інших символів. Не пиши обгрунтування, лише код."}

        self.adapter.add_message(message)
        response = self.adapter.execute(document['document_id'])
        code = response.get_output()
        # code = response.output_text
        # code = response.content[0].text
        # print('Code', code)
        self.logger.debug(f"Received response: {code}")
        code = code.replace(" ", '').replace('\n', '')
        code = f"{current_code}.{code}"
        print("Code", code)
        return code

    def try_again(self, document, options, wrong_code):
        context1 = {
            "type": "text",
            "content": self.instruction_code,
        }
        context2 = {
            "type": "text",
            "content": "Текст документу для аналізу:\n\n " + document['html'],
            "cache": True
        }
        context3 = {
            "type": "text",
            "content": "Коди процесуальних рішень: " + ",\n".join(options),
            "cache": True
        }
        self.adapter.context = []
        self.adapter.messages = []

        self.adapter.add_context(context1)
        self.adapter.add_context(context2)
        self.adapter.add_context(context3)
        message = {"role": "assistant", "content": str(wrong_code)}
        self.adapter.add_message(message)

        message = {"role": "user",
                   "content": f"Значення {wrong_code} не знайдено серед варіантів. Спробуй ще раз. Визнач код процесуального рішення для цього документу відповідно до наданих варіантів. Поверни лише числове значення без букв або інших символів. Не пиши обгрунтування, лише код."}
        self.adapter.add_message(message)

        response = self.adapter.execute()
        code = response.content[0].text

        self.logger.debug(f"Received response: {code}")
        if len(code) > 1:
            code = re.sub(r'[^\d]', '', code)

        return code
