from flask import Flask, request, jsonify, render_template
import json
import os

app = Flask(__name__)
DATA_FILE = "matches.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"matches": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def balls_to_overs(balls):
    overs = balls // 6
    rem = balls % 6
    return float(f"{overs}.{rem}")


def overs_to_balls(overs_float):
    overs = int(overs_float)
    balls = round((overs_float - overs) * 10)
    return overs * 6 + balls


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/scoreboard/<int:match_id>")
def scoreboard(match_id):
    return render_template("scoreboard.html", match_id=match_id)


# CREATE MATCH
@app.route("/create_match", methods=["POST"])
def create_match():
    data = load_data()
    body = request.json

    match = {
        "id": len(data["matches"]) + 1,
        "team1": body["team1"],
        "team2": body["team2"],
        "target": body["target"],
        "current_score": 0,
        "balls": 0,
        "crr": 0,
        "rrr": 0,
        "result": "In Progress"
    }

    data["matches"].append(match)
    save_data(data)
    return jsonify(match)


# UPDATE BALL
@app.route("/update_ball", methods=["POST"])
def update_ball():
    data = load_data()
    body = request.json

    match_id = body["id"]
    runs = int(body["runs"])

    for match in data["matches"]:
        if match["id"] == match_id:

            match["balls"] += 1
            match["current_score"] += runs

            overs = match["balls"] / 6
            match["crr"] = round(match["current_score"] / overs, 2) if overs > 0 else 0

            remaining_runs = match["target"] - match["current_score"]
            remaining_balls = (20 * 6) - match["balls"]  # assuming 20 overs match

            if remaining_balls > 0:
                match["rrr"] = round((remaining_runs / remaining_balls) * 6, 2)
            else:
                match["rrr"] = 0

            # Result logic
            if match["current_score"] >= match["target"]:
                match["result"] = f"{match['team1']} Won"
            elif match["balls"] >= 120:
                match["result"] = f"{match['team2']} Won"
            else:
                match["result"] = "In Progress"

            break

    save_data(data)
    return jsonify({"status": "updated", "match": match})


# GET MATCH
@app.route("/match/<int:match_id>")
def get_match(match_id):
    data = load_data()
    for m in data["matches"]:
        if m["id"] == match_id:
            return jsonify(m)
    return jsonify({"error": "not found"})


if __name__ == "__main__":
    app.run(debug=True)