import sys
import os
import json
import pandas as pd
import argparse
import time

from modules.logger import Logger
from modules.config import Config

from modules.strategy.strategy_factory import StrategyFactory
from modules.storage.storage_factory import StorageFactory


def main():
    parser = argparse.ArgumentParser(description="Run classification experiment.")
    parser.add_argument('--config', required=False, help='Config file path (mandatory)')
    parser.add_argument('--experiment', required=False, help='Experiment ID (optional)')
    parser.add_argument('--execution', required=False, default='continue', choices=['append', 'override', 'continue'],
                        help='Execution mode')
    parser.add_argument('--debug', action='store_true', required=False, help='Debug flag')
    args = parser.parse_args()

    config_path = args.config
    experiment_id = args.experiment
    execution_mode = args.execution

    logger = Logger()
    logger.set_logger_type("print")
    logger.set_debug_mode(args.debug)

    # Create Storage
    storage = StorageFactory().get_storage()
    storage.set_data_loading_mode(execution_mode)

    config = Config()

    if experiment_id:
        storage.set_experiment_id(experiment_id)
        config.load_experiment_config(storage, experiment_id)
    else:
        print(config)
        experiment_id = storage.write_record("experiment",
                                             {"model": config["model_name"], "strategy": config["strategy_name"],
                                              "config": json.dumps(config)})
        storage.set_experiment_id(experiment_id)
    logger.debug(f"Experiment ID: {experiment_id}")

    # Create Strategy
    strategy = StrategyFactory.get_strategy(config["strategy_name"])
    strategy.set_config(config)
    strategy.set_storage(storage)

    logger.debug(f"Using strategy: {config['strategy_name']} and model {config['model_name']}")

    start_time = time.time()
    strategy.execute()
    elapsed_time = time.time() - start_time
    storage.update_experiment_record(experiment_id, {'elapsed_time': elapsed_time})


if __name__ == "__main__":
    main()
