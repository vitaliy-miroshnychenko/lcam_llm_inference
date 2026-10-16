import pandas as pd

from modules.anonymization import anonymize
from modules.llm_classification import type_classify
from modules.llm_proc_classification import proc_classify
from modules.llm_proc_validator import base_validate


class Processor:
    def __init__(self, database):
        self.database = database
        self.kb_data = pd.read_csv("feature_store/parsed_proc_decisions_v2.csv")
        self.kb_data = self.kb_data.set_index(['doc_type', 'code'])

    def classify_doc(self, line):
        if not self.database.contains(line, ('html_anonymized', 'ai_doc_type')):
            line['html_anonymized'] = anonymize(line['html'])
            line['ai_doc_type'], proba = type_classify(line['html_anonymized'])

            self.database.update(line.number, line.document_id,
                                 {'html': line['html'],
                                  'html_anonymized': line['html_anonymized'],
                                  'ai_doc_type': line['ai_doc_type'], 'proba': proba})
        else:
            line_info = self.database.get(line.number, line.document_id)
            line['html_anonymized'] = line_info['html_anonymized']
            line['ai_doc_type'] = line_info['ai_doc_type']
            proba = line_info.get('proba', 'UNKNOWN')

        print(line['number'], line['document_id'])
        print(line['ai_doc_type'], 'p={}'.format(proba))

    def classify_code(self, line, decision_tree):
        if not self.database.contains(line, ('ai_code_raw', 'ai_code')):
            line['ai_code_raw'], line['ai_code'] = proc_classify(line, decision_tree)

            self.database.update(line.number, line.document_id,
                                 {'ai_code_raw': line['ai_code_raw'], 'ai_code': line['ai_code']})
        else:
            line_info = self.database.get(line.number, line.document_id)
            line['ai_code_raw'] = line_info['ai_code_raw']
            line['ai_code'] = line_info['ai_code']
        return line

    def validate_code(self, line):
        if not self.database.contains(line, ('ai_decision_is_verified',)):
            is_valid_code = base_validate(line, line['ai_code_raw'], self.kb_data)
            line['ai_code'] = line['ai_code_raw'] if is_valid_code else '-1'
            line['ai_decision_is_verified'] = is_valid_code
            self.database.update(line.number, line.document_id,
                                 {'ai_decision_is_verified': line['ai_decision_is_verified'], 'ai_code': line['ai_code']})
        else:
            line_info = self.database.get(line.number, line.document_id)
            line['ai_decision_is_verified'] = line_info['ai_decision_is_verified']
        return line
    def process(self, line, decision_tree):
        self.classify_doc(line)
        self.classify_code(line, decision_tree)

        self.validate_code(line)
        return line
