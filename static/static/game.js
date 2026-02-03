// Inside the collision check where gameActive becomes false
if (lander.y + lander.h >= moonSurface) {
    gameActive = false;
    let status = lander.vy < 2.0 ? "Success" : "Crashed";
    
    if (status === "Success") {
        const playerName = prompt("Amazing Landing! Enter your name for the ISRO Leaderboard:");
        if (playerName) {
            fetch('/save_score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: playerName,
                    fuel: lander.fuel.toFixed(2),
                    status: "Soft Landing"
                })
            });
        }
    }
    // Show game over UI...
}