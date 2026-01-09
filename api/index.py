import datetime as dt
import os
import requests
from flask import Flask, Response, request
from flask import jsonify
from api import contrib_svg
from api import custom

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

palette1 = {
    "grade0": "#151B23",
    "grade1": "#0e4429",
    "grade2": "#006d32",
    "grade3": "#26a641",
    "grade4": "#39d353",
}
@app.get("/")
def home():
    return "✅ Contribution Graph API is running. Use /graph/<username>"

def total_git(username: str, token: str) -> int:
    url = f"https://api.github.com/users/{username}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    created_at = response.json()["created_at"]
    return int(created_at[:4])
@app.get("/graph/<username>")
def graph(username):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return Response("Missing GITHUB_TOKEN environment variable", status=500)

    # Optional query params
    year = request.args.get("year", type=int) or dt.datetime.now().year
    text = request.args.get("text", default=None, type=str)

    if text:
        contrib_svg.TEXT_WORD = text.upper()
    if username not in ("peme969", "zmushtare"):
        return Response("nope", status=401)
    try:
        calendar = contrib_svg.fetch_contributions(username, year, token)
        svg_data = contrib_svg.build_svg(calendar, year, username)
        return Response(
            svg_data,
            mimetype="image/svg+xml",
            headers={
                # Try to reduce caching
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except Exception as e:
        return Response(f"Error generating SVG: {str(e)}", status=500)
@app.route("/custom/<username>", methods=["GET","POST"])
def customer(username):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return Response("Missing GITHUB_TOKEN environment variable", status=500)

    # Optional query params
    year = request.args.get("year", type=int) or dt.datetime.now().year
    token = request.args.get("graphql token", default=token, type=str)
    
    data = request.get_json(silent=True) or {}
    palette = data.get("palette", palette1)
    if username not in ("peme969", "zmushtare"):
        return Response("nope", status=401)
    try:
        calendar = custom.fetch_contributions(username, year, token)
        svg_data = custom.build_svg(calendar, year, username, palette)

        return Response(
            svg_data,
            mimetype="image/svg+xml",
            headers={
                # Try to reduce caching
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except Exception as e:
        return Response(f"Error generating SVG: {str(e)}", status=500)
@app.get("/graph/years/<username>")
def years(username):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return Response("Missing GITHUB_TOKEN environment variable", status=500)
    if username not in ("peme969", "zmushtare"):
        return Response("nope", status=401)
    try:
        created = int(total_git(username,token))
        total = dt.datetime.now().year - created
        current_year = dt.datetime.now().year
        years = list(range(created, current_year + 1))
        return jsonify(
            total=int(total),
            years_in_git=years
        )
    except Exception as e:
        return Response(f"Error getting yearsy: {str(e)}", status=500)
