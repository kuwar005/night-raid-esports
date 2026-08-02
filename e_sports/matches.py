import json
import os

MATCHES_FILE = 'matches.json'

def get_all_matches():
    if not os.path.exists(MATCHES_FILE):
        return {}
    try:
        with open(MATCHES_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_matches(matches):
    with open(MATCHES_FILE, 'w') as f:
        json.dump(matches, f, indent=4)

def add_tournament(name, game, fee, match_time, prize_1st=0, prize_2nd=0, prize_3rd=0):
    matches = get_all_matches()
    match_id = f"m{len(matches) + 1}"
    
    matches[match_id] = {
        "id": match_id,
        "match_name": name,
        "game": game,
        "fee": fee,
        "match_time": match_time,
        "participant_count": 0,
        "is_joined": False,
        "prize_1st": prize_1st,
        "prize_2nd": prize_2nd,
        "prize_3rd": prize_3rd,
        "status": "Upcoming"
    }
    save_matches(matches)
    return match_id

def get_match_details(match_id):
    matches = get_all_matches()
    return matches.get(str(match_id))

def delete_tournament(match_id):
    matches = get_all_matches()
    if str(match_id) in matches:
        del matches[str(match_id)]
        save_matches(matches)

def join_tournament(username, match_id):
    matches = get_all_matches()
    m = matches.get(str(match_id))
    if not m:
        return False, "Match not found."
    
    from payments import check_balance, deduct_coins
    try:
        fee = int(m.get('fee', 0))
    except ValueError:
        fee = 0

    if check_balance(username) < fee:
        return False, "insufficient_mana"
        
    if deduct_coins(username, fee):
        m['participant_count'] = m.get('participant_count', 0) + 1
        save_matches(matches)
        return True, "joined"
    return False, "insufficient_mana"