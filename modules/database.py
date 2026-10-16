import pickle as pkl

from modules.llm_config import config


def create_empty_cell():
    return {'html_anonymized': None, 'html': None,
            'ai_doc_type': None, 'ai_code_raw': None, 'ai_code': None,
            'llm_versions': None, 'ai_decision_is_verified': None}


class Database:
    def __init__(self, data):
        self.db_path = "feature_store/metadata/{}/db.pkl".format(config['experiment_name'])
        try:  # TODO: create a database class
            with open(self.db_path, 'rb') as f:
                self.database = pkl.load(f)
        except:
            self.database = {}
            for number, doc_id, html in data[['number', 'document_id', 'html']].values:
                self.database[(number, doc_id)] = create_empty_cell()
                self.database[(number, doc_id)]['html'] = html
            self.commit()

    def update(self, number, document_id, dict_with_updates, on_exist='update'):
        # self.database[(number. document_id)] = create_empty_cell()
        if on_exist == 'update':
            try:
                self.database[(number, document_id)].update(dict_with_updates)
            except:
                print("KEY is NONE")
        else:
            self.database[(number, document_id)] = create_empty_cell()
            self.database[(number, document_id)].update(dict_with_updates)

        self.commit()

    def contains(self, line, fields):
        key = (line.number, line.document_id)
        if key not in self.database:
            return False

        at_least_one_none = bool(max([self.database[(line.number, line.document_id)].get(i, None) is None for i in fields]))
        return not at_least_one_none

    def commit(self):
        with open(self.db_path, 'wb') as f:
            pkl.dump(self.database, f)

    def get(self, number, document_id):
        return self.database[number, document_id]
