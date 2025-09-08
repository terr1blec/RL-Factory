from .base import Env as BaseEnv
from .mmbase import MMEnv
from .search import SearchEnv
from .vision import VisionEnv
from .reward_rollout_example import RewardRolloutEnv


__all__ = ['BaseEnv', 'SearchEnv', 'RewardRolloutEnv', 'VisionEnv', 'MMEnv']

TOOL_ENV_REGISTRY = {
    'base': BaseEnv,
    'mmbase': MMEnv,
    'search': SearchEnv,
    'reward_rollout': RewardRolloutEnv,
    'vision': VisionEnv
}

CLASS_NAME_MAPPING = {
    "SearchAPI": "search",
    "GorillaFileSystem": "file_system",
    "MathAPI": "math_api",
    "MessageAPI": "message_api",
    "TwitterAPI": "twitter_api",
    "TicketAPI": "ticket_api",
    "TradingBot": "trading_bot",
    "TravelAPI": "travel_api",
    "VehicleControlAPI": "vehicle_control_api",
}

NAME_CLASS_MAPPING = {v: k for k, v in CLASS_NAME_MAPPING.items()}

# These classes are stateless and do not require any initial configuration
STATELESS_CLASSES = [
    "SearchAPI",
    "MathAPI",
]