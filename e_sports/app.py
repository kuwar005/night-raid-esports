import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import io
import json
import os
import requests
import uuid

import matplotlib
matplotlib.use('Agg')  # Prevents server crashes on headless environments like Render
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "night_raid_dev_secret_key")

MATCHES_FILE = "matches.json"

def load_matches():
    """Load matches safely and normalize match IDs."""
    if not os.path.exists(MATCHES_FILE):
        save_matches([])
        return []
    with open(MATCHES_FILE, "r") as f:
        try:
            matches = json.load(f)
            for match in matches:
                match["id"] = str(match.get("id", "")).strip()
                if "players" not in match or not isinstance(match["players"], list):
                    match["players"] = []
                if "room_id" not in match:
                    match["room_id"] = ""
                if "room_pass" not in match:
                    match["room_pass"] = ""
                if "game" not in match:
                    match["game"] = "BGMI"
                if "status" not in match:
                    match["status"] = "UPCOMING"
                if "fee" not in match:
                    match["fee"] = "0"
                if "prize_1st" not in match:
                    match["prize_1st"] = "100"
            return matches
        except (json.JSONDecodeError, Exception):
            return []

def save_matches(matches):
    """Persist matches to disk and sync directly to GitHub if GITHUB_TOKEN is present."""
    with open(MATCHES_FILE, "w") as f:
        json.dump(matches, f, indent=4)

    github_token = os.environ.get("GITHUB_TOKEN")
    repo_owner = os.environ.get("GITHUB_REPO_OWNER", "kuwar005")
    repo_name = os.environ.get("GITHUB_REPO_NAME", "night-raid-esports")
    file_path = "e_sports/matches.json"

    if github_token:
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            get_res = requests.get(url, headers=headers)
            sha = get_res.json().get("sha") if get_res.status_code == 200 else None

            content_bytes = json.dumps(matches, indent=4).encode('utf-8')
            encoded_content = base64.b64encode(content_bytes).decode('utf-8')

            data = {
                "message": "Auto-update matches.json [Night Raid Engine]",
                "content": encoded_content
            }
            if sha:
                data["sha"] = sha

            requests.put(url, headers=headers, json=data)
        except Exception as e:
            print(f"GitHub Sync Notice: {e}")

def generate_player_chart(player_ign, categories, values):
    """Generates styled Matplotlib bar chart with valid hex/alpha formatting."""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_facecolor('#080C14')
    ax.set_facecolor('#04060A')

    bars = ax.bar(categories, values, color='#00F0FF', edgecolor='#FF2E63', linewidth=1.5)
    ax.set_title(f"TACTICAL STATS: {player_ign}", color='#00F0FF', fontsize=12, fontweight='bold', pad=15)
    ax.tick_params(colors='#FFFFFF', labelsize=9)

    for spine in ax.spines.values():
        spine.set_color('#00F0FF')
        spine.set_alpha(0.2)

    ax.grid(axis='y', linestyle='--', alpha=0.15, color='#00F0FF')

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.3, int(yval), ha='center', va='bottom', color='#FFFFFF', fontsize=9)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close(fig)

    return base64.b64encode(image_png).decode('utf-8')

@app.route('/login', methods=['POST'])
def user_login():
    player_name = request.form.get('player_name', '').strip()
    if player_name:
        session['user_ign'] = player_name
        flash(f"Welcome back, Operative {player_name}!", "success")
    else:
        flash("Please enter a valid Gamer ID.", "error")
    return redirect(url_for('index'))

@app.route('/logout')
def user_logout():
    session.pop('user_ign', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    matches = load_matches()
    
    if request.method == 'POST':
        match_id = str(request.form.get('match_id', '')).strip()
        player_ign = request.form.get('player_ign', '').strip() or session.get('user_ign', '')
        custom_note = request.form.get('custom_note', '').strip()

        if match_id and player_ign:
            match_found = False
            for match in matches:
                if str(match.get('id', '')).strip() == match_id:
                    match_found = True
                    if match.get('status') == 'COMPLETED':
                        flash("This tournament match has ended!", "error")
                        break

                    if 'players' not in match or not isinstance(match['players'], list):
                        match['players'] = []
                    
                    existing_igns = [p.get('ign', '').lower() for p in match['players']]
                    if player_ign.lower() in existing_igns:
                        flash(f"Player '{player_ign}' is already deployed in this match!", "error")
                        break

                    match['players'].append({
                        "ign": player_ign,
                        "note": custom_note,
                        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_matches(matches)
                    
                    if 'registered_matches' not in session:
                        session['registered_matches'] = []
                    if match_id not in session['registered_matches']:
                        session['registered_matches'].append(match_id)
                    
                    session['user_ign'] = player_ign
                    session.modified = True
                    
                    flash(f"Deployment Confirmed for {match.get('match_name', 'Tournament')}!", "success")
                    break
            
            if not match_found:
                flash("Invalid Tournament ID.", "error")
        else:
            flash("Enter your In-Game ID to register.", "error")

        return redirect(url_for('index'))

    registered_ids = session.get('registered_matches', [])
    user_mp = (len(registered_ids) * 50) + 100
    current_user = session.get('user_ign', None)

    return render_template('index.html', matches=matches, registered_ids=registered_ids, user_mp=user_mp, current_user=current_user)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        upi_id = request.form.get('upi_id', '').strip()
        amount_mp = request.form.get('amount', '').strip()
        if upi_id and amount_mp:
            flash(f"Withdrawal request of {amount_mp} Mana Points (MP) submitted for account: {upi_id}!", "success")
        else:
            flash("Provide valid redemption details and MP amount.", "error")
        return redirect(url_for('withdraw'))
        
    return render_template('withdraw.html')

@app.route('/stats/<player_ign>')
def player_stats(player_ign):
    matches = load_matches()
    matches_joined = 0

    for match in matches:
        for p in match.get('players', []):
            if p.get('ign', '').lower() == player_ign.lower():
                matches_joined += 1

    categories = ['Kills', 'Matches', 'Wins', 'Top 10s']
    values = [
        matches_joined * 4 if matches_joined > 0 else 0,
        matches_joined,
        max(0, matches_joined // 2),
        matches_joined + 1 if matches_joined > 0 else 0
    ]

    chart_base64 = generate_player_chart(player_ign, categories, values)
    return render_template('stats.html', player_ign=player_ign, chart_base64=chart_base64, matches_joined=matches_joined)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
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
                <title>Admin Access — Night Raid Esports</title>
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Space+Grotesk:wght@500&display=swap" rel="stylesheet">
                <style>
                    body { background: #04060A; color: #fff; font-family: 'Space Grotesk', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                    .login-box { background: #080C14; padding: 40px; border-radius: 16px; border: 1px solid #00F0FF; text-align: center; width: 90%; max-width: 380px; box-shadow: 0 0 30px rgba(0,240,255,0.2); }
                    h2 { font-family: 'Orbitron', sans-serif; font-size: 1.3rem; color: #00F0FF; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; }
                    input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px; background: #04060A; color: #fff; box-sizing: border-box; outline: none; }
                    input:focus { border-color: #00F0FF; }
                    button { width: 100%; background: #FF2E63; color: #fff; border: none; padding: 12px; border-radius: 8px; font-weight: bold; font-family: 'Orbitron', sans-serif; cursor: pointer; transition: 0.3s; box-shadow: 0 0 15px rgba(255,46,99,0.4); }
                    button:hover { background: #e01e4f; }
                </style>
            </head>
            <body>
                <div class="login-box">
                    <h2>Command Center</h2>
                    <form method="POST">
                        <input type="password" name="password" placeholder="Enter Admin Passcode" required autocomplete="off">
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
            prize_1st = request.form.get('prize_1st', '100').strip()
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
                    "status": "UPCOMING",
                    "players": []
                }
                matches.append(new_match)
                save_matches(matches)
                flash("Tournament match deployed!", "success")
            else:
                flash("Match name required.", "error")
            
        elif action == 'update_room':
            match_id = str(request.form.get('match_id', '')).strip()
            room_id = request.form.get('room_id', '').strip()
            room_pass = request.form.get('room_pass', '').strip()
            status = request.form.get('status', 'UPCOMING').strip()
            
            for match in matches:
                if str(match.get('id', '')).strip() == match_id:
                    match['room_id'] = room_id
                    match['room_pass'] = room_pass
                    match['status'] = status
                    save_matches(matches)
                    flash(f"Credentials & Status updated for {match.get('match_name')}!", "success")
                    break

        return redirect(url_for('admin'))

    return render_template('admin.html', matches=matches)

@app.route('/admin/delete/<match_id>', methods=['POST'])
def delete_match(match_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    matches = load_matches()
    target_id = str(match_id).strip()
    
    updated_matches = [m for m in matches if str(m.get('id', '')).strip() != target_id]
    
    save_matches(updated_matches)
    flash("Tournament deleted permanently.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)