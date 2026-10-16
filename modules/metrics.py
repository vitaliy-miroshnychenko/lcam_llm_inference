import re
class Metrics:
    
    def __init__(self, storage, experiment_id):
        self.storage = storage
        self.experiment_id = experiment_id
        self.metrics = None

    def calculate_metrics(self, ignore_invalid_documents = True):
        results = self.storage.load_experiment_data(self.experiment_id)
        total_number_of_documents = len(results)
        total_number_of_valid_documents = 0
        total_number_of_invalid_documents = 0

        full_accuracy = 0
        at_least_one  = 0
        at_least_one_minus_one_digit = 0
        accuracy_among_one_code = 0
        number_of_one_code_documents = 0

        precision_among_one_code   = 0
        precision_among_many_codes = 0
        number_of_document_with_predicted_one_code   = 0
        number_of_document_with_predicted_many_codes = 0

        for record in results:
            if record['true_category'] is None:
                total_number_of_invalid_documents += 1
                continue
                
            true_codes = sorted(record['true_category'].split(','))
            true_codes = [re.sub(r'\.$', '', tc) for tc in true_codes]
            pred_codes = sorted(record['predicted_category'].split(','))

            if len(true_codes) == 1 and len(self.storage.load_taxonomy(true_codes[0])) > 0:
                total_number_of_invalid_documents += 1
                continue
            total_number_of_valid_documents += 1

            if len(pred_codes) == 1:
                number_of_document_with_predicted_one_code += 1
            else:
                number_of_document_with_predicted_many_codes += 1
            
            if true_codes == pred_codes:
                full_accuracy += 1
                if len(pred_codes) == 1:
                    precision_among_one_code += 1
                else:
                    precision_among_many_codes +=1 

            if len(true_codes) == 1:
                number_of_one_code_documents += 1

            if len(true_codes) == 1 and pred_codes == true_codes:
                accuracy_among_one_code += 1

            intersect = set(true_codes).intersection(set(pred_codes))
            if len(intersect) > 0:
                at_least_one += 1
                
            for code in pred_codes:
                code_minus_last_digit = code[:-2]
                matches = [true_code for true_code in true_codes if code_minus_last_digit in true_code]
                if len(matches) > 0:
                    at_least_one_minus_one_digit += 1
                    break

        total = total_number_of_valid_documents
        if not ignore_invalid_documents:
            total = total_number_of_documents

        self.metrics = {
            "full_accuracy": round(full_accuracy/total, 2),
            "at_least_one": round(at_least_one/total, 2),
            "accuracy_among_one_code": round(accuracy_among_one_code/number_of_one_code_documents, 2),
            "precision_among_one_code": round(precision_among_one_code/number_of_document_with_predicted_one_code, 2),
            "precision_among_many_codes": round(precision_among_many_codes/number_of_document_with_predicted_many_codes, 2) if number_of_document_with_predicted_many_codes > 0 else None,            
            "at_least_one_minus_one_digit": round(at_least_one_minus_one_digit/total, 2),
            "percent_of_invalid_documents": round(total_number_of_invalid_documents/total_number_of_documents, 2),
            "total_documents": total_number_of_documents
        }
        return self.metrics

    def cleanup(self):
        self.storage.cleanup_metrics(self.experiment_id)
    
    def save(self):
        if self.metrics is None:
            raise ValueError("Metrics are not calculated yet")

        self.storage.save_metrics(self.metrics, self.experiment_id)
        
