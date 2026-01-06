import os
import datetime as dt
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler
import contrib_svg

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Missing GITHUB_TOKEN environment variable")
            return

        # Parse query params
        # Example: /api/graph?user=peme969&year=2026&text=PEME
        query = parse_qs(self.path.split("?", 1)[-1]) if "?" in self.path else {}

        username = query.get("user", [None])[0]
        if not username:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Missing required query param: user")
            return

        year = int(query.get("year", [dt.datetime.now().year])[0])
        text = query.get("text", [None])[0]
        if text:
            contrib_svg.TEXT_WORD = text.upper()

        try:
            calendar = contrib_svg.fetch_contributions(username, year, token)
            svg_data = contrib_svg.build_svg(calendar, year, username)

            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(svg_data.encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error generating SVG: {str(e)}".encode("utf-8"))
