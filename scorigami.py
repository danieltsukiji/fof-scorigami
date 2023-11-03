from collections import defaultdict
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader

league_data_path = "C:\\Users\\bassl\\AppData\\Local\\Solecismic Software\\Front Office Football Eight\\leaguedata\\"


@dataclass
class Scorigami:
    highest_score: int
    first_year: int
    current_year: int
    scores: dict[int, dict[int, int]]

    def get_html(self, current_year: int | None):
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("scorigami.html")

        with open(f".\\html\\{current_year}.html", "w") as out:
            out.write(
                template.render(highest_score=self.highest_score, scores=self.scores, current_year=current_year or self.current_year))


@dataclass
class Index:
    league: str
    years: list[int]

    def get_html(self):
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("index.html")

        with open("index.html", "w") as out:
            out.write(template.render(league=self.league, years=self.years))


def _process_line(line: str) -> tuple[int, int, int] | None:
    parts = line.split(",")

    if parts[2].startswith("Ex."):
        return None

    year = int(parts[0])
    score_1 = int(parts[3])
    score_2 = int(parts[5])

    if score_1 < score_2:
        return score_1, score_2, year
    return score_2, score_1, year


def process_game_information(league_name: str) -> Scorigami:
    csv_path = f"{league_data_path}{league_name}\\game_information.csv"
    high_score = 0
    first_year = 0
    current_year = 0

    with open(csv_path, "r") as csv_file:
        lines = csv_file.readlines()
        scores = defaultdict(defaultdict)
        lines.reverse()

        for line in lines[:-1]:
            processed = _process_line(line)
            if processed:
                losing_score, winning_score, year = processed
                if not first_year:
                    first_year = year
                current_year = max(current_year, year)
                if winning_score not in scores[losing_score]:
                    scores[losing_score][winning_score] = year
                    high_score = max(high_score, winning_score)

    return Scorigami(highest_score=high_score, first_year=first_year, current_year=current_year, scores=scores)


if __name__ == "__main__":
    scorigami = process_game_information("RZBRZB15")
    years = range(scorigami.first_year, scorigami.current_year + 1)
    index = Index(league="RZB", years=list(years))

    index.get_html()

    for year in years:
        scorigami.get_html(year)
