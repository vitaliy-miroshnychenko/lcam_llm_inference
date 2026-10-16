import json


class MySQLDataLoader():
    def __init__(self, cursor):
        self.cursor = cursor

    def load_data(self, experiment, results_table, data_loading_mode = None):
        self.results_table     = results_table
        self.data_loading_mode = data_loading_mode
        
        """Load all documents from the database."""
        if experiment is not None:
            selection_type = experiment.get("selection_type", "PROFILE")
            print("Your experiment profile:", selection_type)
            if selection_type == "SPECIFIED_DOCUMENTS":
                return self.load_specified_documents(experiment)
            elif selection_type == "SPECIFIED_CASES":
                return self.load_specified_cases(experiment)
            elif selection_type == "PROFILE":
                return self.load_profile_documents(experiment)
        return self.load_default_data(experiment)

    def load_default_data(self, experiment):
        # Load all documents
        sql_docs = "SELECT hd.*, c.number as case_number, t.code as true_category, d.judgment_code FROM html_documents hd INNER JOIN cases c ON hd.case_id = c.id INNER JOIN documents d ON d.id=hd.document_id LEFT JOIN taxonomy t ON hd.true_taxonomy_category = t.id LIMIT 150"
        self.cursor.execute(sql_docs)
        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        docs = [dict(zip(columns, row)) for row in rows]

        # If experiment_id is set, filter out already classified documents
        experiment_id = experiment.get('id', None)
        if experiment_id is not None:
            sql_classified = f"SELECT document_id FROM {self.results_table} WHERE experiment_id = %s"
            self.cursor.execute(sql_classified, (experiment_id,))
            classified_rows = self.cursor.fetchall()
            classified_ids = set(row[0] for row in classified_rows)
            docs = [doc for doc in docs if str(doc.get('document_id')) not in classified_ids]
        return docs

    def load_specified_documents(self, experiment):
        info = json.loads(experiment.get("selection_info", "{}"))
        field = info.get("field", "document_id")
        ids = info.get("ids", [])
        if not ids:
            return []

        if self.data_loading_mode == 'override':
            self.cleanup_experiment(experiment)
        
        # Build placeholders for IN clause
        placeholders = ','.join(['%s'] * len(ids))
        sql = f"SELECT hd.*, c.number as case_number, t.code as true_category, d.judgment_code FROM html_documents hd INNER JOIN cases c ON hd.case_id = c.id INNER JOIN documents d ON d.id=hd.document_id LEFT JOIN taxonomy t ON hd.true_taxonomy_category = t.id WHERE hd.{field} IN ({placeholders})"
        self.cursor.execute(sql, tuple(ids))
        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        res = [dict(zip(columns, row)) for row in rows]
        return [dict(zip(columns, row)) for row in rows]
    
    def load_specified_cases(self, experiment):
        info = json.loads(experiment.get("selection_info", {}))
        field = info.get("field", "case_id")
        case_ids = info.get("case_ids", [])
        case_numbers = info.get("case_numbers", [])

        if self.data_loading_mode == 'override':
            self.cleanup_experiment(experiment)
        
        if len(case_ids) > 0:
            print("case_ids parts")
            field = info.get("field", "case_id")
            # Build placeholders for IN clause
            placeholders = ','.join(['%s'] * len(case_ids))
            sql = f"SELECT hd.*, c.number as case_number, t.code as true_category, d.judgment_code FROM html_documents hd INNER JOIN cases c ON hd.case_id = c.id INNER JOIN documents d ON d.id=hd.document_id LEFT JOIN taxonomy t ON hd.true_taxonomy_category = t.id WHERE {field} IN ({placeholders})"
            self.cursor.execute(sql, tuple(case_ids))
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        elif len(case_numbers) > 0:
            print("case_numbers parts")
            documents_table = info.get("table", "html_documents")
            cases_table = info.get("cases_table", "cases")
            field = info.get("field", "number")
            # Build placeholders for IN clause
            placeholders = ','.join(['%s'] * len(case_numbers))

            where = [f'c.{field} IN ({placeholders})']
            sql = f"SELECT hd.*, c.number as case_number, t.code as true_category, d.judgment_code FROM html_documents hd INNER JOIN cases c ON hd.case_id = c.id INNER JOIN documents d ON d.id=hd.document_id LEFT JOIN taxonomy t ON hd.true_taxonomy_category = t.id"

            if self.data_loading_mode == 'continue':
                sql += f" LEFT JOIN classification_result cr ON cr.document_id=hd.document_id AND cr.experiment_id={experiment['id']}"
                where.append("cr.id IS NULL")
            sql += f" WHERE {' AND '.join(where)}"
            print(sql)

            self.cursor.execute(sql, tuple(case_numbers))
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []

    def load_profile_documents(self, experiment):
        info = json.loads(experiment.get("selection_info", {}))
        profile_id = info.get("profile_id", None)
        if profile_id is None:
            return []

        if self.data_loading_mode == 'override':
            self.cleanup_experiment(experiment)
            
        sql = "SELECT hd.*, c.number as case_number, sub_true_taxonomy.codes as true_category, d.judgment_code FROM html_documents hd INNER JOIN cases c ON hd.case_id = c.id INNER JOIN documents d ON d.id=hd.document_id INNER JOIN experiment_profile_cases pc ON pc.case_id=hd.case_id LEFT JOIN (SELECT GROUP_CONCAT(code) as codes, html_document_id FROM  html_documents2taxonomy sub_p2t INNER JOIN html_documents sub_hp ON sub_hp.id=sub_p2t.html_document_id LEFT JOIN taxonomy sub_t ON sub_t.id=sub_p2t.taxonomy_id GROUP BY sub_p2t.html_document_id) sub_true_taxonomy ON sub_true_taxonomy.html_document_id=hd.id"

        where = [f"pc.experiment_profile_id={profile_id}"]
        
        if self.data_loading_mode == 'continue':
            sql += f" LEFT JOIN classification_result cr ON cr.document_id=hd.document_id AND cr.experiment_id={experiment['id']}"
            where.append("cr.id IS NULL")
            
        sql += f" WHERE {' AND '.join(where)}"
        print('sql', sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        print('len(rows)', len(rows))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]


    def cleanup_experiment(self, experiment):
        id = int(experiment.get("id", 0))
        if id == 0:
            return
        self.cursor.execute(f"DELETE FROM classification_result WHERE experiment_id='{id}'")
        self.cursor.execute(f"DELETE FROM experiment_metric WHERE experiment_id='{id}'")
        self.cursor.execute(f"DELETE FROM request_log WHERE experiment_id='{id}'")        

