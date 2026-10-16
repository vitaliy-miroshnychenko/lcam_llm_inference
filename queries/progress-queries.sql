SELECT document_id, input_tokens, output_tokens, thinking_tokens, cache_read, cache_write, elapsed_time FROM request_log WHERE experiment_id=33;
SELECT id, predicted_category, true_category, elapsed_time FROM classification_result WHERE experiment_id=33;
