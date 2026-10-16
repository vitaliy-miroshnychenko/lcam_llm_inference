from fastapi import FastAPI
from modules.storage.storage_factory import StorageFactory
from modules.strategy.strategy_factory import StrategyFactory
import json


app = FastAPI()

@app.get("/models")
def list_models():
    return [
        {"model": "claude-3-5-haiku-latest", "title": "Claude Haiku", "description": "Швидка, якісна та дешева модель від Anthropic"},
        {"model": "claude-sonnet-4-20250514", "title": "Claude Sonnet", "description": "Повільніша та дорожча модель від Anthropic"},
        {"model": "openai-gpt-5", "title": "GPT-5", "description": "GPT-5 від OpenAI"},
        {"model": "openai-gpt-5-mini", "title": "GPT-5 mini", "description": "GPT-5 mini від OpenAI"}                
    ]

@app.get("/strategies")
def list_strategies():
    return [
        {"name": "one_shot_per_document", "description": "Класифікація документів шляхом одного запиту для всієї групи типу 5.*"},
        {"name": "iterative", "description": "Класифікація документів шляхом послідовних запитів на кожному рівні"},
    ]

@app.post("/analyze-case")
def analyze_case(data: dict):
    # TODO: Implement experiment creation logic
    case_number = data.get("case_number")
    if not case_number:
        return {"error": "Case number is required"}
        
    # Create Storage
    config = {
        "model_name": data.get("model", "claude-3-5-haiku-latest"),
        "strategy_name": data.get("strategy", "one_shot_per_document"),
        "enable_citations": data.get("citations", False),
        "storage_name": "mysql",
        "storage_config": {
            "host": "127.0.0.1",
            "database": data.get("database", "case_analysis"),
            "results_table": "classification_result",
            "experiment_table": "experiment"
        }
    }
    storage = StorageFactory.get_storage("mysql", config['storage_config'])
    experiment_id = storage.write_record("experiment", {"model": data["model"], "strategy": data["strategy"], "config": json.dumps(config), "selection_type": "SPECIFIED_CASES", "selection_info": json.dumps({"field": "number", "case_numbers": [case_number]})})
    storage.set_experiment_id(experiment_id)

    strategy = StrategyFactory.get_strategy(config["strategy_name"])
    strategy.set_config(config)
    strategy.set_storage(storage)
    strategy.execute()

    return {"status": "success", "experiment": experiment_id}
