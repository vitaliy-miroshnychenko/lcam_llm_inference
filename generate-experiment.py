import sys
import json
import mysql.connector
# from modules.storage.mysql_data_loader import MySQLDataLoader
from modules.storage.storage_factory import StorageFactory
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# python generate-experiment.py pipeline_configs/claude_haiku_context_iterative.json SPECIFIED_DOCUMENTS 40371,5872735,39854,5188865,305110,5805008,305110
# python generate-experiment.py pipeline_configs/claude_haiku_context_iterative.json SPECIFIED_CASES "322/1138/20,308/13549/20,652/692/20"
# python generate-experiment.py pipeline_configs/claude_haiku_one_shot.json PROFILE 4
# python generate-experiment.py claude-3-5-haiku-latest/iterative PROFILE 4

def main():
    if len(sys.argv) != 4:
        logger.info("Usage: python generate-experiment.py <config_file> <data_loader_type> <selection_details>")
        sys.exit(1)

    config_argument = sys.argv[1]
    data_loader_type = sys.argv[2]
    selection_details = sys.argv[3]

    if config_argument.endswith('.json'):
        # Load config
        with open(config_argument, 'r') as f:
            config = json.load(f)
    else:
        # parse config as model/strategy
        chunks = config_argument.split("/")
        config = {'model_name': chunks[0], 'strategy_name': chunks[1]}

    logger.info("Config loaded: {}".format(config))
    # Create Storage
    logger.info("Creating storage")
    storage = StorageFactory().get_storage()

    if data_loader_type == "SPECIFIED_CASES":
        if not selection_details:
            raise ValueError("Selection details must be provided for SPECIFIED_CASES data loader type.")
        selection_details = json.dumps({"field": "number", "case_numbers": selection_details.split(",")})
    elif data_loader_type == "SPECIFIED_DOCUMENTS":
        if not selection_details:
            raise ValueError("Selection details must be provided for SPECIFIED_DOCUMENTS data loader type.")
        selection_details = json.dumps({"field": "document_id", "ids": selection_details.split(",")})
    elif data_loader_type == "PROFILE":
        if (not selection_details) or (int(selection_details) <= 0):
            raise ValueError("Profile id must be provided")
        selection_details = json.dumps({"profile_id": int(selection_details)})
    elif data_loader_type == "ALL_DECISIONS":
        data_loader_type = "SPECIFIED_CASES"
        with open('feature_store/cases_v001.pkl', 'rb') as f:
            import pickle
            selection_details = pickle.load(f)
        selection_details = json.dumps({"field": "number", "case_numbers": selection_details.split(",")})
        # selection_details = json.dumps({"field": "number", "file_path": 'feature_store/cases_v001.pkl'})

    logger.info("Writing record about experiment ...")
    experiment_id = storage.write_record("experiment",
                                         {"model": config["model_name"], "strategy": config["strategy_name"],
                                          "config": json.dumps(config), "selection_type": data_loader_type,
                                          "selection_info": selection_details})
    logger.info(f"Generated experiment with ID: {experiment_id}")


if __name__ == "__main__":
    main()
