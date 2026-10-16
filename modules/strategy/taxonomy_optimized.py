import json

from pandas import options
from modules.adapters.adapter_factory import AdapterFactory
from .strategy import Strategy
import re
from modules.logger import Logger
from modules.anonymization import anonymize


class TaxonomyOptimized(Strategy):
    STRATEGY_NAME = "taxonomy_optimized"
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
        self.documents = []
        self.categories = []
        self.classification_config = None
        self.enable_citations = False
        self.enable_case_summary = False
        self.enable_motivation = False
        self.logger = Logger()


    def execute(self):
        self.adapter = AdapterFactory.get_adapter(
            self.config["model_name"],
            self.config.get_api_key(),
            # self.config.get("api_key_env"),
            # self.config.get("api_key_file")
        )
        self.adapter.set_storage(self.storage)
        self.logger.debug(f"Using model: {self.config['model_name']}") 

        # if self.config.get("enable_citations"):
        #     self.enable_citations = True
        self.enable_citations = False

        result = []
        documents = self.storage.load_data()

        if len(documents) == 0:
            self.logger.log("No documents to classify.")
            return result

        for idx, document in enumerate(documents):
            res = self.classify_document(document)
            self.logger.log(f"Classification result: for document {document['document_id']}: {res['code']}. True category: {document.get('true_category', 'N/A')}")
            result.append(res)

            # Prepare data for classification_result table
            data = {
                "document_id": res.get("document_id"),
                "predicted_category": res.get("code"),
                "experiment_id": getattr(self.storage, "experiment_id", None),
                "case_number": getattr(document, "case_number", None) if hasattr(document, "case_number") else document.get("case_number", None),
                "true_category": getattr(document, "true_category", None) if hasattr(document, "true_category") else document.get("true_category", None),
                "response": res.get("response", None)
            }
            self.storage.write_record("result", data)

        self.storage.update_experiment_accuracy()
        return result

    def classify_document(self, document):
        index = int(document['judgment_code'])
        
        if index == 5:
            return self.classify_ruling(document)

        selected_option = None
        options = self.storage.load_taxonomy(index)
        requested_taxonomy = self.generate_requested_taxonomy(index, 1, True)

        indent = 0
        self.adapter.reset()
        context1 = {"type": "text", "content": self.instruction_code}
        self.adapter.add_context(context1)

        document_content_block = {
            "type": "document",
            "content_type": "text",
            "media_type": "text/plain",
            "data": anonymize(document['html']),
            "title": f"Документ {document['document_id']}",
            "context": "Документ для аналізу",
            "caching": True
        }
        if self.config.get("enable_citations"):
            document_content_block["citations"] = True

        codes_content_block = {
            "type": "text",
            "text": "Коди процесуальних рішень: " + ",\n".join(requested_taxonomy),
            "caching": True
        }

        request_content_block = {
            "type": "text",
            "text": "Визнач один або декілька кодів процесуальних рішеннь для цього документу відповідно до наданих варіантів. Поверни лише числові значення через кому. Не пиши обгрунтування, лише коди.",
            "caching": True
            #"text": "Визнач тип процесуального рішення"
        }
        
        message = {
            "type": "user",
            "content": [
                codes_content_block,
                document_content_block,
                request_content_block
            ]
        }
        
        self.adapter.add_message(message)

        response = self.adapter.execute()
        codes = response.get_output()
        result = {'document_id': document['document_id'], 'code': codes}

        if self.config.get("enable_citations"):
            self.adapter.reset()
            self.adapter.add_context(context1)
            self.adapter.add_message(message)
            self.adapter.add_message({"role": "assistant", "content": str(codes)})
            self.adapter.add_message({"role": "user", "content": "Поясни свою відповідь"})
            response = self.adapter.execute() 
            response_message = json.dumps(response.__dict__, default=str, ensure_ascii=False)
            result['response'] = response_message

        return result

    def classify_ruling(self, document):
        context = {"type": "text", "content": self.instruction_code}
        document_content_block = {
            "type": "document",
            "content_type": "text",
            "media_type": "text/plain",
            "data": anonymize(document['html']),
            "title": f"Документ {document['document_id']}",
            "context": "Документ для аналізу",
            "caching": True
        }
        # if self.config.get("enable_citations"):
        #     document_content_block["citations"] = True
        
        open_codes = self.classify_open_ruling(document, context, document_content_block)
        closing_codes = self.classify_closing_ruling(document, context, document_content_block)
        expenses_codes = self.classify_expenses(document, context, document_content_block)
        execution_codes = self.classify_execution(document, context, document_content_block)
        separate_proceedings_codes = self.classify_separate_proceedings(document, context, document_content_block)
        interlocutory_ruling_codes = self.classify_interlocutory_ruling(document, context, document_content_block)

        codes = [code.splitlines()[0] for code in [open_codes, closing_codes, expenses_codes, execution_codes, separate_proceedings_codes, interlocutory_ruling_codes] if code is not None and not code.startswith("0")]
        codes = ", ".join(codes)
        codes = re.sub(r"[^\d\., ]", "", codes).strip()
        result = {'document_id': document['document_id'], 'code': codes}

        return result


    def classify_open_ruling(self, document, context, document_content_block):
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи містить дана ухвала інформацію про відкриття провадження у справі? Якщо так, то поверни 1 для відкриття позовного провадження, 2 для окремого провадження, 3 для наказного провадження, 4 для апеляційного провадження, 5 для касаційного провадження, 6 для перегляду судового рішення за нововиявленими обставинами. Якщо ухвала не містить інформації про відкриття провадження, то поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        #print("Ухвали про відкриття провадження:", response.content)
        opening_result = response.get_output()

        known_codes = {"1": "5.1.1.1", "2": "5.1.1.2", "3": "5.1.1.3(?)", "4": "5.1.2", "5": "5.1.3", "6": "5.1.4"}
        if opening_result == "0" or not opening_result in known_codes:
            return None
        return known_codes[opening_result]

    def classify_closing_ruling(self, document, context, document_content_block):
        self.adapter.reset()
        self.adapter.add_context(context)

        options = self.generate_requested_taxonomy("5.2")

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала такою, що завершує рух у справі або перешкоджає подальшому провадженню? Якщо ні - то поверни 0. Якщо так, то поверни код ухвали відповідно до наданих варіантів: " + ",\n".join(options) + ". Повертай лише код, без пояснень.",
            "caching": True
        }
        
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        #print("Ухвали про закриття провадження:", response.content)
        closing_result = response.get_output()

        if closing_result.startswith("5.2."):
            subtypes = self.generate_requested_taxonomy(closing_result)
            self.adapter.reset()
            self.adapter.add_context(context)
            self.adapter.add_message(message)
            self.adapter.add_message({"role": "assistant", "content": str(closing_result)})
            self.adapter.add_message({"role": "user", "content": "Уточни, до якого підтипу належить дана ухвала? " + ",\n".join(subtypes) + ". Поверни лише код, без пояснень."})
            subtype_response = self.adapter.execute()
            #print("Уточнення підтипу ухвали:", subtype_response.content)
            closing_result = subtype_response.get_output()

        return closing_result

    def classify_expenses(self, document, context, document_content_block):
        self.adapter.reset()
        self.adapter.add_context(context)

        options = self.generate_requested_taxonomy("5.4")

        request_content_block = {
            "type": "text",
            "text": "Чи містить дана ухвала інформацію про витрати на судовий процес? Якщо так, то поверни код ухвали відповідно до наданих варіантів: " + ",\n".join(options) + ". Якщо ухвала не містить інформації про витрати, то поверни 0. Повертай лише код без пояснень.",
        }
        
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        #print("Ухвали про витрати:", response.content)
        expenses_result = response.get_output()
        return expenses_result


    def classify_execution(self, document, context, document_content_block):
        self.adapter.reset()
        self.adapter.add_context(context)

        options = self.generate_requested_taxonomy("5.5")

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою про виконання судового рішення? Якщо так, то поверни код ухвали відповідно до наданих варіантів: " + ",\n".join(options) + ". Якщо ухвала не містить інформації про виконання, то поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        #print("Ухвали про виконання:", response.content)
        execution_result = response.get_output()
        return execution_result
    
    def classify_separate_proceedings(self, document, context, document_content_block):
        self.adapter.reset()
        self.adapter.add_context(context)

        options = self.generate_requested_taxonomy("5.7")

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою про окреме провадження? Якщо так, то поверни код ухвали відповідно до наданих варіантів: " + ",\n".join(options) + ". Якщо ухвала не містить інформації про окреме провадження, то поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        #print("Ухвали про окреме провадження:", response.content)
        separate_proceedings_result = response.get_output()
        return separate_proceedings_result

    def classify_interlocutory_ruling(self, document, context, document_content_block):
        ################################ Закриття провадження
        self.adapter.reset()
        self.adapter.add_context(context)

        #options = self.generate_requested_taxonomy("5.6")
        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою про закриття підготовчого провадження та призначення справи до судового розгляду? Якщо так то поверни 1, якщо ні то поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code1 = "5.3.1.1" if response.get_output().startswith("1 ") else None
        #print("Ухвали про закриття підготовчого провадження:", response.content)

        ################################# Відвід
        options = self.generate_requested_taxonomy("5.3.2")
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою про відвід? Якщо так, то поверни код ухвали відповідно до наданих варіантів: " + ",\n".join(options) + ". Якщо ухвала не містить інформації про відвід, то поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code2 = response.get_output()
        #print("Ухвали про відвід:", response.content)

        ################################## щодо залучення /відмову у залученні учасників судового процесу
        options = self.generate_requested_taxonomy("5.3.4")
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою щодо залучення /відмову у залученні учасників судового процесу? Якщо так, то поверни код ухвали відповідно до наданих варіантів: " + ",\n".join(options) + ". Інакше поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code3 = response.get_output()
        #print("Ухвали щодо залучення учасників судового процесу:", response.content)

       ################################## про зловживання процесуальними правами
        options = self.generate_requested_taxonomy("5.3.5")
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою щодо зловживання процесуальними правами? Якщо так, то поверни код ухвали відповідно до наданих варіантів: " + ",\n".join(options) + ". Інакше поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code4 = response.get_output()
        #print("Ухвали про зловживання процесуальними правами:", response.content)

        ################################## Ухвали про особливості судового розгляду справи
        options = self.generate_requested_taxonomy("5.3.6")
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала одією з наступних ухвал: " + ",\n".join(options) + ". Якщо так, то поверни відповідний код ухвали. Інакше поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code5 = response.get_output()
        #print("Ухвали про рух судового провадження:", response.content)

        ################################## Ухвали про рух судового провадження
        options = self.generate_requested_taxonomy("5.3.7")
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала одією з наступних ухвал: " + ",\n".join(options) + ". Якщо так, то поверни відповідний код ухвали. Інакше поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code6 = response.get_output()
        #print("Ухвали про рух судового провадження:", response.content)


        ################################## Ухвали про передачу справи з одного суду до іншого
        options = self.generate_requested_taxonomy("5.3.8")
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою про передачу справи з одного суду до іншого? Якщо так, то поверни код відповідно до наступного списку: " + ",\n".join(options) + ".  Інакше поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code7 = response.get_output()
        #print("Ухвали про передачу справи з одного суду до іншого:", response.content)


        ################################## Ухвали щодо доказів
        options = self.generate_requested_taxonomy("5.3.9")
        self.adapter.reset()
        self.adapter.add_context(context)

        request_content_block = {
            "type": "text",
            "text": "Чи є дана ухвала ухвалою щодо доказів? Якщо так, то поверни код відповідно до наступного списку: " + ",\n".join(options) + ".  Інакше поверни 0. Повертай лише код без пояснень.",
            "caching": True
        }
        message = {
            "type": "user",
            "content": [
                document_content_block,
                request_content_block
            ]
        }
        self.adapter.add_message(message)
        response = self.adapter.execute()
        code8 = response.get_output()
        #print("Ухвали щодо доказів:", response.content)


        codes = [code.splitlines()[0] for code in [code1, code2, code3, code4, code5, code6, code7, code8] if code and not code.startswith("0")]
        #print("Ухвали про процесуальні дії:", codes)
        return ", ".join(codes) if codes else None

    # def generate_requested_taxonomy(self, index, indent = 1, recursive = False):
    #     CODES = { '3': 'рішення', '2': 'постанова', '6': 'окрема ухвала', '4': 'судовий наказ', '5': 'ухвала'}
    #     taxonomy = []
    #     if len(str(index)) == 1:
    #         taxonomy.append(f"{index}. {CODES[str(index)]}")
    #
    #     options = self.storage.load_taxonomy(index)
    #     for i, option in enumerate(options):
    #         taxonomy.append(f"{'  ' * indent}{option['code']}. {option['title']}")
    #         if recursive:
    #             sub_taxonomy = self.generate_requested_taxonomy(option['code'], indent * 4, recursive)
    #             taxonomy.extend(sub_taxonomy)
    #     return taxonomy

    def generate_requested_taxonomy(self, index, indent=1):
        CODES = {'3': 'рішення', '2': 'постанова', '6': 'окрема ухвала', '4': 'судовий наказ', '5': 'ухвала'}
        taxonomy = []
        if len(str(index)) == 1:
            taxonomy.append(f"{index}. {CODES[str(index)]}")
        print("generate_requested_taxonomy.index", index)
        options = self.storage.load_taxonomy(index)
        for i, option in enumerate(options):
            taxonomy.append(f"{'  ' * indent}{option['code']}. {option['title']}")
            sub_taxonomy = self.generate_requested_taxonomy(option['code'], indent + 1)
            taxonomy.extend(sub_taxonomy)
        return taxonomy
    
