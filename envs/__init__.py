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
    "GorillaFileSystem": {"name": "file_system", "path": "envs.tools.file_system"},
    "MathAPI": "",
    "MessageAPI": "",
    "TwitterAPI": "",
    "TicketAPI": "",
    "TradingBot": "",
    "TravelAPI": "",
    "VehicleControlAPI": "",
}

# These classes are stateless and do not require any initial configuration
STATELESS_CLASSES = [
    "MathAPI",
]