import importlib
import pkgutil
import inspect
from . import strategy
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyFactory:
    @staticmethod
    def get_strategy(name):
        import os
        strategies = []
        strategy_dir = os.path.dirname(__file__)
        for filename in os.listdir(strategy_dir):
            if filename.endswith('.py') and filename not in ('strategy.py', '__init__.py'):
                modname = filename[:-3]
                module = importlib.import_module(f"modules.strategy.{modname}")
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, strategy.Strategy) and obj is not strategy.Strategy:
                        strategies.append(obj)
        logger.info("Valid strategies: {}".format(strategies))
        for strat_cls in strategies:
            if getattr(strat_cls, "STRATEGY_NAME", None) == name:
                return strat_cls()
        raise ValueError(f"No strategy found with name: {name}")
