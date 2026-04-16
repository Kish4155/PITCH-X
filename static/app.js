function startLiveScoreboard(matchId) {

    async function loadMatch() {
        const res = await fetch(`/match/${matchId}`);
        const data = await res.json();

        document.getElementById("board").innerHTML = `
            <div class="card">

                <h2>${data.team1} vs ${data.team2}</h2>

                <div class="score">
                    ${data.current_score} / ${Math.floor(data.balls / 6)}.${data.balls % 6}
                </div>

                <div class="stats">

                    <div class="stat-box">
                        <h3>CRR</h3>
                        <p>${data.crr}</p>
                    </div>

                    <div class="stat-box">
                        <h3>RRR</h3>
                        <p>${data.rrr}</p>
                    </div>

                    <div class="stat-box">
                        <h3>Target</h3>
                        <p>${data.target}</p>
                    </div>

                    <div class="stat-box">
                        <h3>Balls</h3>
                        <p>${data.balls}</p>
                    </div>

                </div>

                <div class="result">
                    ${data.result}
                </div>

            </div>
        `;
    }

    loadMatch();
    setInterval(loadMatch, 1500);
}