from fastapi import FastAPI, Query, Request
import requests
from fastapi.responses import PlainTextResponse
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return PlainTextResponse(
        "You're sending commands too fast! 🧠⏱️ Try again in a few seconds.",
        status_code=429
    )

@app.get("/elo/{username}", response_class=PlainTextResponse)
@limiter.limit("10/minute") 
def get_elo(request: Request, username: str, type: Optional[str] = Query(default=None)):
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
        "rush": get_puzzle_rush,
        "puzzlerush": get_puzzle_rush,
        "puzzles": lambda: get_rating("tactics", "Puzzles")
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
        get_rating("tactics", "Puzzles"),
        get_puzzle_rush(),
    ]
    results_clean = [r for r in results if r]

    if not results_clean:
        return f"No rating data found for {username}."

    return f"{username}'s ratings:\n" + "\n".join(results_clean)

@app.get("/", response_class=PlainTextResponse)
def root():
    return "Chess ELO Bot API is running.\nUse /elo/{username} to see ratings.\nVisit /about for more info."

@app.get("/about", response_class=PlainTextResponse)
def about():
    return """Chess ELO Bot API by robotsforbrunch

    This API fetches chess ratings from Chess.com for a given username.

    Usage:
    /elo/{username}               → All ratings
    /elo/{username}?type=rapid    → Just rapid rating
    /elo/{username}?type=blitz    → Just blitz
    /elo/{username}?type=daily    → Daily
    /elo/{username}?type=rush     → Puzzle Rush score
    /elo/{username}?type=bullet   → Bullet rating
    /elo/{username}?type=puzzles  → Tactics puzzles rating

    Rate limit: 10 requests per minute per IP
    """

