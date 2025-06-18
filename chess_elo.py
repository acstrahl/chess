from fastapi import FastAPI, Query
import requests
from fastapi.responses import PlainTextResponse
from typing import Optional

app = FastAPI()

@app.get("/elo/{username}", response_class=PlainTextResponse)
def get_elo(username: str, type: Optional[str] = Query(default=None)):
    url = f"https://api.chess.com/pub/player/{username}/stats"
    headers = {
        "User-Agent": "TwitchEloBot/1.0 (contact: robotsforbrunch@email.com)"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        return f"Error fetching stats for {username}: {str(e)}"

    type = (type or "").lower()

    def get_rating(section, label):
        rating = data.get(section, {}).get("last", {}).get("rating")
        return f"{label}: {rating}" if rating is not None else None

    def get_puzzle_rush():
        rush_score = data.get("puzzle_rush", {}).get("best", {}).get("score")
        return f"Puzzle Rush: {rush_score}" if rush_score is not None else None

    type_map = {
        "bullet": lambda: get_rating("chess_bullet", "Bullet"),
        "blitz": lambda: get_rating("chess_blitz", "Blitz"),
        "rapid": lambda: get_rating("chess_rapid", "Rapid"),
        "daily": lambda: get_rating("chess_daily", "Daily"),
        "puzzle": get_puzzle_rush,
        "rush": get_puzzle_rush,
        "puzzlerush": get_puzzle_rush,
    }

    if type and type in type_map:
        result = type_map[type]()
        return result or f"No data for {type} rating."

    # Default: show all
    results = [
        get_rating("chess_bullet", "Bullet"),
        get_rating("chess_blitz", "Blitz"),
        get_rating("chess_rapid", "Rapid"),
        get_rating("chess_daily", "Daily"),
        get_puzzle_rush(),
    ]
    results_clean = [r for r in results if r]

    if not results_clean:
        return f"No rating data found for {username}."

    return f"{username}'s ratings — " + ", ".join(results_clean)
