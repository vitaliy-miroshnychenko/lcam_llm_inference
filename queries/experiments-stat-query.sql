SELECT
  e.id,
  e.strategy,
  e.model,
  ROUND(elapsed_time/60, 2) as time,
  e.estimated_cost as cost,
  acc.value as acc,
  at_least_one.value as 1match,
  one_code.value as 1c_acc,
  one_code_prec.value as 1c_prec,
  many_codes_prec.value as mp_prec,
  minus_one.value as minus1_acc,
  docs.value as docs,
  inv.value as inv
FROM
  experiment e
LEFT JOIN
  experiment_metric acc ON acc.experiment_id=e.id AND acc.name='full_accuracy'
LEFT JOIN
  experiment_metric at_least_one ON at_least_one.experiment_id=e.id AND at_least_one.name='at_least_one'
LEFT JOIN
  experiment_metric one_code ON one_code.experiment_id=e.id AND one_code.name='accuracy_among_one_code'
LEFT JOIN
  experiment_metric one_code_prec ON one_code_prec.experiment_id=e.id AND one_code_prec.name='precision_among_one_code'
LEFT JOIN
  experiment_metric many_codes_prec  ON many_codes_prec.experiment_id=e.id AND many_codes_prec.name='precision_among_many_codes'
LEFT JOIN
  experiment_metric minus_one  ON minus_one.experiment_id=e.id AND minus_one.name='at_least_one_minus_one_digit'
LEFT JOIN
  experiment_metric docs  ON docs.experiment_id=e.id AND docs.name='total_documents'
LEFT JOIN
  experiment_metric inv  ON inv.experiment_id=e.id AND inv.name='percent_of_invalid_documents'
#WHERE e.id>28 AND strategy='one_shot_per_document';
