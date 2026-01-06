import datetime as dt
import os

from flask import Flask, Response, request

from api import contrib_svg

app = Flask(__name__)


@app.get("/")
def home():
    return "✅ Contribution Graph API is running. Use /graph/<username>"


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
