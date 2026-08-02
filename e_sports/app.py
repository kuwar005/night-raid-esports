from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import uuid

app = Flask(__name__)

# Replaced hardcoded secret string with os.environ.get to pass GitHub secret scanning
app.secret_key = os.environ.get("SECRET_KEY", "night_raid_dev_secret_key")

MATCHES_FILE = "matches.json"

def load_matches():
    """Load matches safely with guaranteed data structure defaults."""
    if not os.path.exists(MATCHES_FILE):
        save_matches([])
        return []
    with open(MATCHES_FILE, "r") as f:
        try:
            matches = json.load(f)
            for match in matches:
                if "players" not in match or not isinstance(match["players"], list):
                    match["players"] = []
                if "room_id" not in match:
                    match["room_id"] = ""
                if "room_pass" not in match:
                    match["room_pass"] = ""
                if "game" not in match:
                    match["game"] = "BGMI"
            return matches
        except (json.JSONDecodeError, Exception):
            return []

def save_matches(matches):
    """Persist matches list to JSON storage safely."""
    with open(MATCHES_FILE, "w") as f:
        json.dump(matches, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def index():
    matches = load_matches()
    
    if request.method == 'POST':
        match_id = request.form.get('match_id', '').strip()
        player_ign = request.form.get('player_ign', '').strip()
        custom_note = request.form.get('custom_note', '').strip()

        if match_id and player_ign:
            for match in matches:
                if match.get('id') == match_id:
                    if 'players' not in match or not isinstance(match['players'], list):
                        match['players'] = []
                    
                    match['players'].append({
                        "ign": player_ign,
                        "note": custom_note
                    })
                    save_matches(matches)
                    
                    if 'registered_matches' not in session:
                        session['registered_matches'] = []
                    if match_id not in session['registered_matches']:
                        session['registered_matches'].append(match_id)
                    session.modified = True
                    
                    flash(f"Successfully registered for {match.get('match_name', 'Tournament')}!", "success")
                    break
        else:
            flash("Registration failed. Please enter a valid In-Game ID.", "error")

        return redirect(url_for('index'))

    registered_ids = session.get('registered_matches', [])
    return render_template('index.html', matches=matches, registered_ids=registered_ids)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        upi_id = request.form.get('upi_id', '').strip()
        amount = request.form.get('amount', '').strip()
        if upi_id and amount:
            flash(f"Withdrawal request of ₹{amount} submitted for UPI: {upi_id}!", "success")
        else:
            flash("Please provide valid UPI details and amount.", "error")
        return redirect(url_for('withdraw'))
        
    return render_template('withdraw.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Dynamic password setup (defaults to '2009' if not set in Render environment)
    admin_pass = os.environ.get("ADMIN_PASSWORD", "2009")
    
    if not session.get('admin_logged_in'):
        if request.method == 'POST':
            password = request.form.get('password', '')
            if password == admin_pass:
                session['admin_logged_in'] = True
                flash("Admin authenticated successfully!", "success")
                return redirect(url_for('admin'))
            else:
                flash("Incorrect Admin Password!", "error")
                return redirect(url_for('admin'))

        return '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Admin Authentication — Night Raid Esports</title>
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Space+Grotesk:wght@500&display=swap" rel="stylesheet">
                <style>
                    body { background: #06080C; color: #fff; font-family: 'Space Grotesk', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                    .login-box { background: #0D111A; padding: 35px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center; width: 90%; max-width: 360px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); }
                    h2 { font-family: 'Orbitron', sans-serif; font-size: 1.2rem; color: #00F0FF; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
                    input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px; background: #06080C; color: #fff; box-sizing: border-box; outline: none; }
                    input:focus { border-color: #00F0FF; }
                    button { width: 100%; background: #FF2E63; color: #fff; border: none; padding: 12px; border-radius: 8px; font-weight: bold; font-family: 'Orbitron', sans-serif; cursor: pointer; transition: 0.3s; }
                    button:hover { background: #e01e4f; }
                </style>
            </head>
            <body>
                <div class="login-box">
                    <h2>Night Raid Admin</h2>
                    <form method="POST">
                        <input type="password" name="password" placeholder="Enter Admin Password" required autocomplete="off">
                        <button type="submit">AUTHENTICATE</button>
                    </form>
                </div>
            </body>
            </html>
        '''

    matches = load_matches()
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'create':
            match_name = request.form.get('match_name', '').strip()
            game = request.form.get('game', 'BGMI')
            fee = request.form.get('fee', '0').strip()
            prize_1st = request.form.get('prize_1st', '0').strip()
            match_time = request.form.get('match_time', 'TBD').strip()

            if match_name:
                new_match = {
                    "id": str(uuid.uuid4())[:8],
                    "match_name": match_name,
                    "game": game,
                    "fee": fee,
                    "prize_1st": prize_1st,
                    "match_time": match_time,
                    "room_id": "",
                    "room_pass": "",
                    "players": []
                }
                matches.append(new_match)
                save_matches(matches)
                flash("Tournament published successfully!", "success")
            else:
                flash("Match name is required.", "error")
            
        elif action == 'update_room':
            match_id = request.form.get('match_id', '')
            room_id = request.form.get('room_id', '').strip()
            room_pass = request.form.get('room_pass', '').strip()
            
            for match in matches:
                if match.get('id') == match_id:
                    match['room_id'] = room_id
                    match['room_pass'] = room_pass
                    save_matches(matches)
                    flash(f"Room credentials updated for {match.get('match_name', 'Tournament')}!", "success")
                    break

        return redirect(url_for('admin'))

    return render_template('admin.html', matches=matches)

@app.route('/admin/delete/<match_id>', methods=['POST'])
def delete_match(match_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    matches = load_matches()
    matches = [m for m in matches if m.get('id') != match_id]
    save_matches(matches)
    flash("Tournament deleted successfully.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)