import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
USERS_FILE = BASE_DIR / "users.json"
SIGNUP_BONUS = 50


def load_users() -> dict:
    """Loads user data from storage."""
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_users(users: dict) -> None:
    """Saves user data to storage."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


def register_user(username: str) -> tuple[bool, str]:
    """Registers a new user and grants 50 bonus coins."""
    username = username.strip().lower()
    if not username:
        return False, "Username cannot be empty."

    users = load_users()
    if username in users:
        return False, f"User '{username}' already exists!"

    # Create user account with 50 signup bonus coins
    users[username] = {"coins": SIGNUP_BONUS, "matches_joined": []}

    save_users(users)
    return True, f"Account created! You received {SIGNUP_BONUS} bonus coins."


def get_user(username: str) -> dict | None:
    """Retrieves user profile data."""
    users = load_users()
    return users.get(username.strip().lower())