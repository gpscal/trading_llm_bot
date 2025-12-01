import os
import json
from typing import Dict, Any
from config.config import CONFIG

PROFILES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'profiles.json')

SENSITIVE_KEYS = [
    'api_key',
    'api_secret',
    'discord_bot_token',
    'discord_channel_id'
]

def _ensure_dir_exists(path: str) -> None:
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

def load_profiles() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(PROFILES_PATH):
        return {}
    try:
        with open(PROFILES_PATH, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_profile(name: str, values: Dict[str, Any]) -> None:
    profiles = load_profiles()
    profiles[name] = {k: v for k, v in values.items() if k in SENSITIVE_KEYS}
    _ensure_dir_exists(PROFILES_PATH)
    with open(PROFILES_PATH, 'w') as f:
        json.dump(profiles, f)

def apply_profile(name: str) -> Dict[str, Any]:
    profiles = load_profiles()
    profile = profiles.get(name)
    if not profile:
        raise ValueError('Profile not found')
    # Update environment
    for k, v in profile.items():
        if v is None:
            continue
        if k == 'api_key':
            os.environ['API_KEY'] = str(v)
            CONFIG['api_key'] = str(v)
        elif k == 'api_secret':
            os.environ['API_SECRET'] = str(v)
            CONFIG['api_secret'] = str(v)
        elif k == 'discord_bot_token':
            os.environ['DISCORD_BOT_TOKEN'] = str(v)
            CONFIG['discord_bot_token'] = str(v)
        elif k == 'discord_channel_id':
            os.environ['DISCORD_CHANNEL_ID'] = str(v)
            CONFIG['discord_channel_id'] = str(v)
    return profile

def mask_value(value: str) -> str:
    if not value:
        return ''
    s = str(value)
    if len(s) <= 6:
        return '*' * len(s)
    return s[:3] + '*' * (len(s) - 6) + s[-3:]


