import json
import os
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'cric_secret_key_changeme_2024'

# =========================
# ADMIN CREDENTIALS
# (change these before deploying)
# =========================
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'cricket123'

# =========================
# AUTH HELPERS
# =========================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


# =========================
# MEMORY STORAGE
# =========================
matches = {}
MATCHES_FILE = "matches.json"

FORMAT_OVERS = {"T20": 20, "ODI": 50}

def default_extras():
    return {"no_balls": 0, "wides": 0, "byes": 0}

def generate_match_id(team1, team2):
    """Generate a short ID from the first letter of each team name.
    e.g. 'India' vs 'Australia' -> 'IA'
    Appends a numeric suffix if the base ID already exists.
    """
    t1 = (team1.strip().split()[0][0] if team1.strip() else 'X').upper()
    t2 = (team2.strip().split()[0][0] if team2.strip() else 'X').upper()
    base = t1 + t2
    if base not in matches:
        return base
    counter = 2
    while f"{base}{counter}" in matches:
        counter += 1
    return f"{base}{counter}"

def load_matches():
    global matches
    if os.path.exists(MATCHES_FILE):
        try:
            with open(MATCHES_FILE, "r") as f:
                data = json.load(f)
                if "matches" in data:
                    for m in data["matches"]:
                        if "id" in m:
                            mid = str(m["id"])   # normalise to string
                            matches[mid] = {
                                "id":            mid,
                                "team1":         m.get("team1", "-"),
                                "team2":         m.get("team2", "-"),
                                "format":        m.get("format", "T20"),
                                "toss_winner":   m.get("toss_winner", ""),
                                "toss_choice":   m.get("toss_choice", "bat"),
                                "total_balls":   m.get("total_balls", 120),
                                "innings":       m.get("innings", 1),
                                "innings1_score":m.get("innings1_score", None),
                                "target":        m.get("target", None),
                                "current_score": m.get("current_score", 0),
                                "balls":         m.get("balls", 0),
                                "wickets":       m.get("wickets", 0),
                                "crr":           m.get("crr", 0),
                                "rrr":           m.get("rrr", 0),
                                "history":       m.get("history", []),
                                "fours":         m.get("fours", 0),
                                "sixes":         m.get("sixes", 0),
                                "extras":        m.get("extras", default_extras()),
                                "result":        m.get("result", "Live"),
                            }
        except Exception as e:
            print("Error loading matches:", e)

def save_matches():
    try:
        with open(MATCHES_FILE, "w") as f:
            json.dump({"matches": list(matches.values())}, f, indent=4)
    except Exception as e:
        print("Error saving matches:", e)

load_matches()


# =========================
# LANDING PAGE
# =========================
@app.route('/')
def landing():
    return render_template("landing.html")


# =========================
# LOGIN / LOGOUT
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "Invalid username or password. Please try again."
    return render_template("login.html", error=error)


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('landing'))


# =========================
# ADMIN PANEL (protected)
# =========================
@app.route('/admin')
@login_required
def admin():
    return render_template("admin.html")


# =========================
# LIVE SCORES (public)
# =========================
@app.route('/live')
def live():
    return render_template("live.html")


# =========================
# LIST ALL MATCHES (API - public)
# =========================
@app.route('/matches')
def list_matches():
    return jsonify({"matches": list(matches.values())})


# =========================
# CREATE MATCH (admin only)
# =========================
@app.route('/create_match', methods=['POST'])
@login_required
def create_match():
    data = request.get_json()

    fmt         = data.get("format", "T20")
    overs       = FORMAT_OVERS.get(fmt, 20)
    total_balls = overs * 6

    team1    = data.get("team1", "Team 1")
    team2    = data.get("team2", "Team 2")
    match_id = generate_match_id(team1, team2)

    matches[match_id] = {
        "id":             match_id,
        "team1":          team1,
        "team2":          team2,
        "format":         fmt,
        "toss_winner":    data.get("toss_winner", ""),
        "toss_choice":    data.get("toss_choice", "bat"),
        "total_balls":    total_balls,
        "innings":        1,
        "innings1_score": None,
        "target":         None,
        "current_score":  0,
        "balls":          0,
        "wickets":        0,
        "crr":            0,
        "rrr":            0,
        "history":        [],
        "fours":          0,
        "sixes":          0,
        "extras":         default_extras(),
        "result":         "Live",
    }
    save_matches()
    return jsonify({"match_id": match_id})


# =========================
# END INNINGS (admin only)
# =========================
@app.route('/end_innings/<string:match_id>', methods=['POST'])
@login_required
def end_innings(match_id):
    match = matches.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    if match["innings"] != 1:
        return jsonify({"error": "Already in 2nd innings"}), 400

    innings1_score = match["current_score"]
    target         = innings1_score + 1

    match["innings1_score"] = innings1_score
    match["target"]         = target
    match["innings"]        = 2
    match["current_score"]  = 0
    match["balls"]          = 0
    match["wickets"]        = 0
    match["crr"]            = 0
    match["rrr"]            = round((target / match["total_balls"]) * 6, 2)
    match["fours"]          = 0
    match["sixes"]          = 0
    match["extras"]         = default_extras()
    match["history"]        = []
    match["result"]         = "Live"

    save_matches()
    return jsonify(match)


# =========================
# UPDATE SCORE (admin only)
# =========================
@app.route('/update_score/<string:match_id>', methods=['POST'])
@login_required
def update_score(match_id):
    data        = request.get_json()
    runs        = data.get("runs", 0)
    ball_type   = data.get("type", "normal")
    is_wicket   = data.get("is_wicket", False)
    wicket_type = data.get("wicket_type", None)

    match = matches.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    if match["result"] not in ("Live", "Rain Delay"):
        return jsonify({"error": "Match is not in play"}), 400

    if "extras"  not in match: match["extras"]  = default_extras()
    if "wickets" not in match: match["wickets"] = 0

    total_balls = match.get("total_balls", 120)
    is_legal    = ball_type not in ("no_ball", "wide")
    if is_legal:
        match["balls"] += 1

    if ball_type == "no_ball":
        match["extras"]["no_balls"] += 1
        match["current_score"] += 1 + runs
    elif ball_type == "wide":
        match["extras"]["wides"] += 1
        match["current_score"] += 1 + runs
    elif ball_type == "bye":
        match["extras"]["byes"] += runs
        match["current_score"] += runs
    else:
        match["current_score"] += runs

    if is_wicket:
        match["wickets"] += 1

    if ball_type != "wide":
        if runs == 4: match["fours"] += 1
        if runs == 6: match["sixes"] += 1

    entry = {"runs": runs, "type": ball_type, "is_wicket": is_wicket}
    if wicket_type:
        entry["wicket_type"] = wicket_type
    match["history"].append(entry)

    if match["balls"] > 0:
        match["crr"] = round((match["current_score"] / match["balls"]) * 6, 2)

    target = match.get("target")
    if target and match["innings"] == 2 and match["result"] == "Live":
        remaining_runs  = target - match["current_score"]
        remaining_balls = total_balls - match["balls"]

        if remaining_runs <= 0:
            match["result"] = f"{match['team2']} won!"
            match["rrr"]    = 0
        elif match["wickets"] >= 10:
            match["result"] = f"{match['team1']} won! (all out)"
            match["rrr"]    = 0
        elif remaining_balls <= 0:
            match["result"] = f"{match['team1']} won! (overs)"
            match["rrr"]    = 0
        else:
            match["rrr"] = round((remaining_runs / remaining_balls) * 6, 2)

    save_matches()
    return jsonify(match)


# =========================
# UPDATE MATCH STATUS (admin only)
# =========================
@app.route('/update_status/<string:match_id>', methods=['POST'])
@login_required
def update_status(match_id):
    data   = request.get_json()
    status = data.get("status", "Live")

    allowed = ("Live", "Rain Delay", "Abandoned")
    if status not in allowed:
        return jsonify({"error": f"status must be one of {allowed}"}), 400

    match = matches.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    match["result"] = status
    save_matches()
    return jsonify(match)


# =========================
# GET MATCH (public read)
# =========================
@app.route('/match/<string:match_id>')
def get_match(match_id):
    match = matches.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404
    return jsonify(match)


# =========================
# SCOREBOARD PAGE (public)
# =========================
@app.route('/scoreboard/<string:match_id>')
def scoreboard(match_id):
    return render_template("scoreboard.html", match_id=match_id)


# =========================
# MATCH DETAILS PAGE (public)
# =========================
@app.route('/match_details/<string:match_id>')
def match_details(match_id):
    return render_template("match_details.html", match_id=match_id)


# =========================
# DELETE MATCH (admin only)
# =========================
@app.route('/delete_match/<string:match_id>', methods=['DELETE'])
@login_required
def delete_match(match_id):
    if match_id not in matches:
        return jsonify({"error": "Match not found"}), 404
    del matches[match_id]
    save_matches()
    return jsonify({"success": True, "deleted_id": match_id})


if __name__ == '__main__':
    app.run(debug=True)