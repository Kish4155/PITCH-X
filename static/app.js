// =========================
// CREATE MATCH
// =========================
function createMatch() {
    const team1 = document.getElementById("team1").value;
    const team2 = document.getElementById("team2").value;
    const target = document.getElementById("target").value;

    fetch('/create_match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team1, team2, target })
    })
    .then(res => res.json())
    .then(data => {
        alert("Match created! ID: " + data.match_id);
    });
}


// =========================
// UPDATE SCORE
// =========================
function updateScore(matchId, runs) {
    fetch(`/update_score/${matchId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ runs })
    });
}

const run0 = id => updateScore(id, 0);
const run1 = id => updateScore(id, 1);
const run2 = id => updateScore(id, 2);
const run4 = id => updateScore(id, 4);
const run6 = id => updateScore(id, 6);


// =========================
// NAVIGATION
// =========================
function openScoreboard() {
    const id = document.getElementById("openMatch").value;
    window.location.href = `/scoreboard/${id}`;
}

function openDetails() {
    const id = document.getElementById("openMatch").value;
    window.location.href = `/match_details/${id}`;
}


// =========================
// LIVE SCOREBOARD
// =========================
function startLiveScoreboard(id) {
    async function fetchData() {
        try {
            const res = await fetch(`/match/${id}`);
            const data = await res.json();

            if (data.error) {
                document.getElementById("board").innerHTML = `<h2>Match not found</h2>`;
                return;
            }

            document.getElementById("board").innerHTML = `
                <h2>${data.team1} vs ${data.team2}</h2>
                <p>Score: ${data.current_score}</p>
                <p>Balls: ${data.balls}</p>
                <p>CRR: ${data.crr}</p>
                <p>RRR: ${data.rrr}</p>
                <h3>${data.result}</h3>
            `;
        } catch (e) {
            console.error(e);
        }
    }

    fetchData();
    setInterval(fetchData, 3000);
}


// =========================
// MATCH DETAILS
// =========================
function loadDetails(id) {
    async function fetchData() {
        try {
            const res = await fetch(`/match/${id}`);
            const data = await res.json();

            if (data.error) {
                document.getElementById("teams").innerText = "Match not found";
                document.getElementById("summary").innerText = "";
                document.getElementById("balls").innerHTML = "";
                document.getElementById("stats").innerText = "";
                return;
            }

            document.getElementById("teams").innerText =
                `${data.team1} vs ${data.team2}`;

            document.getElementById("summary").innerText =
                `Score: ${data.current_score} | Balls: ${data.balls}`;

            const list = document.getElementById("balls");
            list.innerHTML = "";

            if (data.history) {
                data.history.forEach((run, i) => {
                    const li = document.createElement("li");
                    li.innerText = `Ball ${i + 1}: ${run}`;
                    list.appendChild(li);
                });
            }

            document.getElementById("stats").innerText =
                `4s: ${data.fours} | 6s: ${data.sixes}`;
        } catch (e) {
            console.error(e);
        }
    }

    fetchData();
    setInterval(fetchData, 3000);
}