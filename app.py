import os
import datetime as dt
from flask import Flask, Response, request
import contrib_svg

app = Flask(__name__)

@app.get("/graph/<username>")
def graph(username):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return Response("Missing GITHUB_TOKEN environment variable", status=500)

    # Optional query params
    year = request.args.get("year", type=int) or dt.datetime.now().year
    text = request.args.get("text", default=None, type=str)

    # If you want TEXT_WORD to be customizable at runtime
    if text:
        contrib_svg.TEXT_WORD = text.upper()

    try:
        calendar = contrib_svg.fetch_contributions(username, year, token)
        svg_data = contrib_svg.build_svg(calendar, year, username)

        return Response(
            svg_data,
            mimetype="image/svg+xml",
            headers={
                # GitHub caches aggressively; this helps reduce stale images
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                # CORS can help if embedded elsewhere
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        return Response(f"Error generating graph: {str(e)}", status=500)


@app.get("/")
def home():
    return "✅ Contribution Graph API running. Try /graph/<username>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
