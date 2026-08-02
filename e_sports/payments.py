import json
import os

BALANCES_FILE = 'balances.json'

def load_balances():
    if not os.path.exists(BALANCES_FILE):
        # Initial starter balances
        return {"Gamer1": 500, "admin": 2000}
    try:
        with open(BALANCES_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"Gamer1": 500, "admin": 2000}

def save_balances(balances):
    with open(BALANCES_FILE, 'w') as f:
        json.dump(balances, f, indent=4)

def check_balance(username, *args, **kwargs):
    """Returns user balance cleanly and safely accepts extra arguments."""
    balances = load_balances()
    return int(balances.get(str(username), 0))

def add_coins(username, amount, *args, **kwargs):
    """Credits Mana Points to a user."""
    balances = load_balances()
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        amount = 0

    username = str(username)
    balances[username] = balances.get(username, 0) + amount
    save_balances(balances)
    return balances[username]

def deduct_coins(username, amount, *args, **kwargs):
    """Deducts Mana Points if sufficient balance exists."""
    balances = load_balances()
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return False

    username = str(username)
    current_bal = balances.get(username, 0)
    if current_bal >= amount:
        balances[username] = current_bal - amount
        save_balances(balances)
        return True
    return False