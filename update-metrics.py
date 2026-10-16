import sys
import os
import json
import pandas as pd
from modules.logger import Logger
from modules.config import Config
from modules.metrics import Metrics

from modules.storage.storage_factory import StorageFactory


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update metrics for a given experiment.")
    parser.add_argument('--experiment', required=True, help='Experiment ID')
    parser.add_argument('--count-invalid', required=False, action='store_true', help='Experiment ID')
    parser.add_argument('--save', '-s', action='store_true', required=False, help='Flag to save the metrics')
    parser.add_argument('--override', '-o', action='store_true', required=False, help='Flag to save the metrics')
    args = parser.parse_args()

    experiment_id = int(args.experiment)
    ignore_invalid = not args.count_invalid
    storage = StorageFactory().get_storage()

    metrics = Metrics(storage, experiment_id)
    result = metrics.calculate_metrics(ignore_invalid)
    print(result)

    if args.override:
        metrics.cleanup()

    if args.save or args.override:
        metrics.save()


if __name__ == "__main__":
    main()
