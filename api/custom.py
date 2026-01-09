"""
GitHub-style contribution SVG with a tooltip functionality so you can you see exactly what you did on that day.
"""
import datetime as dt,sys,os,textwrap,requests
GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
DARK_PALETTE = {
    "grade0": "#151B23",
    "grade1": "#0e4429",
    "grade2": "#006d32",
    "grade3": "#26a641",
    "grade4": "#39d353",
}
def _day_suffix(day: int) -> str:
    if 11 <= day <= 13:
        return "th"
    last = day % 10
    if last == 1:
        return "st"
    if last == 2:
        return "nd"
    if last == 3:
        return "rd"
    return "th"
def format_tooltip(count: int, date_str: str) -> str:
    d = dt.date.fromisoformat(date_str)
    month_name = d.strftime("%B")
    day = d.day
    suffix = _day_suffix(day)
    year = d.year
    if count == 0:
        prefix = "No contributions"
    elif count == 1:
        prefix = "1 contribution"
    else:
        prefix = f"{count} contributions"

    return f"{prefix} on {month_name} {day}{suffix}, {year}"
def fetch_contributions(login: str, year: int, token: str):
    start = dt.datetime(year, 1, 1, 0, 0, 0)
    end = dt.datetime(year, 12, 31, 23, 59, 59)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                weekday
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "login": login,
        "from": start.isoformat() + "Z",
        "to": end.isoformat() + "Z",
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        GITHUB_GRAPHQL_ENDPOINT,
        headers=headers,
        json={"query": query, "variables": variables},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GitHub GraphQL error: {data['errors']}")
    try:
        calendar = data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]
    except TypeError:
        raise RuntimeError("User not found or contributions unavailable")
    return calendar

# ----------------- SVG -----------------
def build_svg(
    calendar: dict,
    year: int,
    username: str,
    palette: dict,
    text_color: str = "#8b949e",
) -> str:

    weeks = calendar["weeks"]
    CELL_SIZE = 11
    CELL_GAP = 3
    CARD_PADDING_LEFT = 46
    CARD_PADDING_TOP = 38
    CARD_PADDING_RIGHT = 22
    CARD_PADDING_BOTTOM = 36
    TITLE_X = 24
    TITLE_Y = 30

    NUM_WEEKS = len(weeks)
    NUM_DAYS = 7

    card_width = (
        CARD_PADDING_LEFT
        + CARD_PADDING_RIGHT
        + NUM_WEEKS * (CELL_SIZE + CELL_GAP)
        - CELL_GAP
    )
    card_height = (
        CARD_PADDING_TOP
        + CARD_PADDING_BOTTOM
        + NUM_DAYS * (CELL_SIZE + CELL_GAP)
        - CELL_GAP
    )

    SVG_PADDING = 20
    width = card_width + SVG_PADDING * 2
    height = card_height + SVG_PADDING * 2 + 20

    CARD_X = SVG_PADDING
    CARD_Y = TITLE_Y + 18

    background_color = "#00000000"
    card_color = "#0d1117"
    border_color = "#30363d"

    FONT_FAMILY = "system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"

    svg_parts = []

    # Background
    svg_parts.append(
        f'<rect width="{width}" height="{height}" fill="{background_color}" />'
    )

    # Title (no <b>, SVG doesn't support HTML tags)
    svg_parts.append(
        f'<text x="{TITLE_X}" y="{TITLE_Y}" '
        f'font-family="{FONT_FAMILY}" font-size="18" fill="{text_color}">'
        f'{year}: <tspan font-weight="700">{calendar["totalContributions"]}</tspan> contributions'
        f'</text>'
    )

    # Card container
    svg_parts.append(
        f'<rect x="{CARD_X}" y="{CARD_Y}" '
        f'width="{card_width}" height="{card_height}" '
        f'rx="10" ry="10" fill="{card_color}" '
        f'stroke="{border_color}" stroke-width="1" />'
    )

    inner_left = CARD_X + CARD_PADDING_LEFT
    inner_top = CARD_Y + CARD_PADDING_TOP

    # Weekday labels
    weekday_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for weekday, label in weekday_labels.items():
        y = inner_top + weekday * (CELL_SIZE + CELL_GAP) + CELL_SIZE - 1
        svg_parts.append(
            f'<text x="{CARD_X + 6}" y="{y}" '
            f'font-family="{FONT_FAMILY}" font-size="12" fill="#8b949e">'
            f'{label}</text>'
        )

    # Month labels
    last_month = None
    for week_index, week in enumerate(weeks):
        if not week["contributionDays"]:
            continue

        first_date_str = week["contributionDays"][0]["date"]
        first_date = dt.date.fromisoformat(first_date_str)
        month_name = first_date.strftime("%b")

        if month_name != last_month:
            last_month = month_name
            x = inner_left + week_index * (CELL_SIZE + CELL_GAP)
            svg_parts.append(
                f'<text x="{x}" y="{CARD_Y + 20}" '
                f'font-family="{FONT_FAMILY}" font-size="14" fill="#e6edf3">'
                f'{month_name}</text>'
            )

    # Contribution cells (STATIC)
    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            weekday = day["weekday"]
            level = day["contributionLevel"]
            count = day["contributionCount"]
            date_str = day["date"]

            # choose fill color
            if count == 0:
                fill = palette["grade0"]
            else:
                fill = palette.get(level, palette["grade1"])

            x = inner_left + week_index * (CELL_SIZE + CELL_GAP)
            y = inner_top + weekday * (CELL_SIZE + CELL_GAP)

            tooltip = format_tooltip(count, date_str)

            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="3" ry="3" fill="{fill}">'
                f'<title>{tooltip}</title>'
                f'</rect>'
            )

    # Legend
    legend_y = CARD_Y + card_height - 10
    legend_x = inner_left - 6

    svg_parts.append(
        f'<text x="{legend_x}" y="{legend_y}" '
        f'font-family="{FONT_FAMILY}" font-size="14" fill="#8b949e">Less</text>'
    )

    legend_colors = [
        palette["grade0"],
        palette["grade1"],
        palette["grade2"],
        palette["grade3"],
        palette["grade4"],
    ]

    square_x = legend_x + 40
    for c in legend_colors:
        svg_parts.append(
            f'<rect x="{square_x}" y="{legend_y - 11}" width="14" height="14" '
            f'rx="3" ry="3" fill="{c}" />'
        )
        square_x += 18

    svg_parts.append(
        f'<text x="{square_x + 6}" y="{legend_y}" '
        f'font-family="{FONT_FAMILY}" font-size="14" fill="#8b949e">More</text>'
    )

    # Final SVG
    svg = textwrap.dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg"
             width="{width}" height="{height}"
             viewBox="0 0 {width} {height}">
          {" ".join(svg_parts)}
        </svg>
        """
    )

    return svg
