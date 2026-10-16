# Project description
This repository contains code, configs and desription of experiments run for the LCAM project

Project link: [https://probability.knu.ua/lcam/index.html](https://probability.knu.ua/lcam/index.html)

###Project Title:
Legal Case Law Analytics: Exploring Big Data Insights through AI-Driven Statistical Modeling

### Project Acronym:
LCAM

### Type of Project:
Cooperation Project

### Main Applicant Organisation:
Linnæus University (LNU), Kalmar/Växjö, Sweden

### Project Leader / Contact Person:
Assoc. Prof. Wolfgang Bock

🎯 Overall Aim
Analyze Ukrainian case-law datasets using advanced statistical methods/AI, predict case outcomes & evaluate factors affecting judicial procedures, promote justice, strengthen democracy.

⚖️ The Challenge
Ukrainian courts handle over 4 million cases yearly, significantly impacting citizens' trust in both the judiciary and state authorities... Ukraine ranks 3rd in complaints lodged with the ECtHR, with about one-third citing violations regarding court proceedings' duration or enforcing decisions.

The Unified State Register of Court Decisions publishes all court decisions in open access, totaling over 100 million records... However, the Register lacks effective search tools and structured information access.

🧠 The LCAM Approach
LCAM will investigate innovative tools for analyzing big data from publicly-available court decisions... to collect, analyze, and summarize empirical data on judicial proceedings, informing future transformations of the national judiciary model.

This analysis aims to uncover persistent inefficiencies in the judicial system, predict case outcomes, and identify factors affecting its proper functioning, ultimately ensuring equal access to justice for all citizens.

🇪🇺 EU Integration Contribution
LCAM will contribute to Ukraine’s efforts to integrate into the EU through the following activities and results: by gathering and analyzing big data from over 100 million Ukrainian court decisions via innovative statistical analysis methods and AI algorithms.

Ukraine’s integration into the EU necessitates transparent/effective monitoring of national judicial practice, as well as uniform approaches to the application of EU law by national courts.

# how to run experiment


## 0. Prerequisites

- create `creds` folder and place there tour credential files
- create `etc` folder and palace there `mysql-config.json`
- place `ssh_creds.py` into `etc` folder to establish ssh tunnel for local experiment run

## 1. Generate-experiment

Run `python generate-experiment.py pipeline_configs/<path to .json config> PROFILE 4`. It will create **experiment id**.
Save it or find in experiment database

## 2. Classify  

Put your **experiment id** (integer) into argument  
Run `python classify.py --experiment <experiment id>`  
like `python classify.py --experiment 1232132131`

## 3. Update metric

Run `python update-metrics.py --experiment <experiment_id>` to count metrics for the experiment. Add flag `--save` to
save them into metadata database. Add `--override` to override ext id>`  
like `python classify.py --experiment 1232132131`

## 3. Update metric

Run `python update-metrics.py --experiment <experiment_id>` to count metrics for the experiment. Add flag `--save` to
save them into metadata database. Add `--override` to override existing experiment metrics. Add `--count-invalid` to add
invalid predictions into a metric evaluation

# Experiment log (draft):
- 31 - gemini flash
- 33 - gemini pro
- 
- 41 - iterative ollama gemma3 12b # Evaluation, THE BEST ~25% accuracy
- 50 - iterative ollama gemma3 27b # Evaluation, THE BEST 36% accuracy
- 51 - iterative ollama gemma3 12b # predict all 20k documents # 28472 documents totally
- 52 - iterative ollama gemma3 12b # predict all 20k documents # 28472 documents totally

- 56 - iterative ollama gemma3 12b # predict only category_code 40381 (about children). 1157 document 
- 57 - oneshot claud sonnet    # predict only category_code 40381 (about children). 1157 document 
- 58 - iterative ollama gemma3 27b # predict all 20k documents # 28472 documents totally

- 75 - iterative ollama gemma4 31b # predict all 20k documents # 28472 documents totally
- 76 - iterative ollama gemma4 31b # Evaluation, THE BEST 49% accuracy

