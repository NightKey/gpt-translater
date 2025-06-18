from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any
from os import path, mkdir
from json import load, dump
from datetime import datetime

BASE_PATH = path.dirname(path.dirname(path.abspath(__file__)))
DATA_PATH = path.join(BASE_PATH, "data")
STATISTICS_PATH = path.join(DATA_PATH, "statistics.json")
SETTINGS_PATH = path.join(DATA_PATH, "settings.json")
API_SETTINGS_PATH = path.join(DATA_PATH, "api_settings.json")

class Model(Enum):
    default = "gpt-4.1"
    default_mini = "gpt-4.1-mini"
    normal = "gpt-4o"
    mini = "gpt-4o-mini"

@dataclass()
class Cost:
    in_token: float
    out_token: float

class Costs(Enum):
    default = Cost(2.0, 8.0)
    default_mini = Cost(0.4, 1.6)
    normal = Cost(2.5, 10.0)
    mini = Cost(0.15, 0.6)

@dataclass()
class Statistics:
    start_date: datetime = field(default_factory=datetime.now())
    in_tokens: int = field(default=0)
    out_tokens: int = field(default=0)

    def current_cost(self, model: Model) -> float:
        cost: Cost = Costs[model.name].value
        in_results = (self.in_tokens / 1_000_000) * cost.in_token
        out_results = (self.out_tokens / 1_000_000) * cost.out_token
        return in_results + out_results
    
    def add_tokens(self, in_tokens: int, out_tokens: int):
        if (self.start_date.year != datetime.now().year or self.start_date.month != datetime.now().month):
            self.start_date = datetime.now()
            self.in_tokens = in_tokens
            self.out_tokens = out_tokens
        else:
            self.in_tokens += in_tokens
            self.out_tokens += out_tokens

    def to_json(self) -> Dict[str, Any]:
        data = self.__dict__.copy()
        data["start_date"] = self.start_date.timestamp()
        return data

    def save(self):
        with open(STATISTICS_PATH, "w") as fp:
            dump(self.to_json(), fp)

    @staticmethod
    def load() -> "Statistics":
        if (not path.exists(STATISTICS_PATH)):
            return Statistics(datetime.now(), 0, 0)
        with open(STATISTICS_PATH, "r") as fp:
            return Statistics.from_json(load(fp))
        
    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Statistics":
        return Statistics(
            datetime.fromtimestamp(data["start_date"]),
            data["in_tokens"],
            data["out_tokens"]
        )

@dataclass()
class ApiSettings:
    name: str = field(default = "GPT Translator")
    api_key: str = field(default = "SMDB KEY HERE")
    ip: str = field(default = "127.0.0.1")
    port: int = field(default = 9600)

    def save(self):
        with open(API_SETTINGS_PATH, "w") as fp:
            dump(self.__dict__, fp)
    
    @staticmethod
    def from_json(data: Dict[str, Any]) -> "ApiSettings":
        return ApiSettings(
            data["name"],
            data["api_key"],
            data["ip"],
            data["port"]
        )

    @staticmethod
    def load() -> "ApiSettings":
        if (not path.exists(API_SETTINGS_PATH)):
            default = ApiSettings()
            default.save()
            return default
        with open(API_SETTINGS_PATH, "r") as fp:
            return ApiSettings.from_json(load(fp))

@dataclass()
class Settings:
    api_key: str
    languages: List[str]
    extra_context: str
    model: Model
    temperature: float
    max_tokens: int
    budget_limit_usd: float
    degrade: bool
    host: str
    port: int
    webUIName: str
    white_list_networks: List[str]
    
    def save(self):
        with open(SETTINGS_PATH, "w") as fp:
            dump(self.to_json(), fp)

    def to_json(self) -> Dict[str, Any]:
        result = self.__dict__.copy()
        result["model"] = self.model.name
        return result

    def valid(self) -> bool:
        return self.api_key != "API KEY HERE"

    @staticmethod
    def create_default() -> "Settings":
        default = Settings("API KEY HERE", ["English", "Hungarian"], "", Model.default, 0.7, 150, 0, False, "localhost", 8080, "GPT Translator")
        default.save()
        return default

    @staticmethod
    def load() -> "Settings":
        if (not path.exists(SETTINGS_PATH)):
            if (not path.exists(DATA_PATH)):
                mkdir(DATA_PATH)
            return Settings.create_default()
        with open(SETTINGS_PATH, "r") as fp:
            return Settings.from_json(load(fp))

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Settings":
        return Settings(
            data["api_key"],
            data["languages"],
            data["extra_context"],
            Model[data["model"]],
            data["temperature"],
            data["max_tokens"],
            data["budget_limit_usd"],
            data["degrade"],
            data["host"],
            data["port"],
            data["webUIName"],
            data["white_list_networks"]
        )
