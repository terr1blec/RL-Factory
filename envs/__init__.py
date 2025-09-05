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

CLASS_FILE_PATH_MAPPING = {
    "SearchAPI": {"name": "search", "path": "envs.tools.search"}, 
    "GorillaFileSystem": {"name": "file_system", "path": "envs.tools.file_system"},
    "MathAPI": {"name": "math_api", "path": "envs.tools.math_api"},
    "MessageAPI": {"name": "message_api", "path": "envs.tools.message_api"},
    "TwitterAPI": {"name": "twitter_api", "path": "envs.tools.twitter_api"},
    "TicketAPI": {"name": "ticket_api", "path": "envs.tools.ticket_api"},
    "TradingBot": {"name": "trading_bot", "path": "envs.tools.trading_bot"},
    "TravelAPI": {"name": "travel_api", "path": "envs.tools.travel_api"},
    "VehicleControlAPI": {"name": "vehicle_control_api", "path": "envs.tools.vehicle_control_api"},
}

# These classes are stateless and do not require any initial configuration
STATELESS_CLASSES = [
    "MathAPI",
]