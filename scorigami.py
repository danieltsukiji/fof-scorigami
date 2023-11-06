from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from jinja2 import Environment, FileSystemLoader

league_data_path = "C:\\Users\\bassl\\AppData\\Local\\Solecismic Software\\Front Office Football Eight\\leaguedata\\"


class GameType(Enum):
    EXHIBITION = "exhibition"
    REGULAR = "regular"
    WILD_CARD = "Wild Card"
    DIVISIONAL = "Divisional"
    CONFERENCE = "Conference"
    BOWL = "Bowl"


@dataclass
class GameInfo:
    id: int
    year: int
    week: str
    type: str
    winning_score: int
    winning_team: str
    losing_score: int
    losing_team: str
    home_team_id: str
    away_team_id: str
    occurrences: int = 1
    week_str: str | None = None

    def __init__(
        self,
        id: int,
        year: int,
        week: str,
        type: str,
        winning_score: int,
        winning_team: str,
        losing_score: int,
        losing_team: str,
        home_team_id: str,
        away_team_id: str,
        occurrences: int = 1,
    ):
        self.id = id
        self.year = year
        self.week = week
        self.type = type
        self.winning_score = winning_score
        self.winning_team = winning_team
        self.losing_score = losing_score
        self.losing_team = losing_team
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.occurrences = occurrences
        if type == GameType.REGULAR.value:
            self.week_str = f"Week {int(self.week) - 4}"
        else:
            self.week_str = type


@dataclass
class Scorigami:
    highest_score: int
    first_year: int
    last_year: int
    scores: dict[int, dict[int, dict]]

    def get_html(self, current_year: int | None):
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("scorigami.html")

        with open(f".\\html\\{current_year or self.last_year}.html", "w") as out:
            out.write(
                template.render(
                    first_year=self.first_year,
                    highest_score=self.highest_score,
                    scores=self.scores,
                    current_year=current_year or self.last_year,
                    last_year=self.last_year
                )
            )


@dataclass
class Index:
    league: str
    all_years: list[int]
    row_years: list[list[int]]

    def get_html(self):
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("index.html")

        with open("index.html", "w") as out:
            out.write(template.render(league=self.league, all_years=self.all_years, row_years=self.row_years))


def _parse_game_type(text: str) -> GameType:
    if text.startswith("Ex."):
        return GameType.EXHIBITION
    if text.startswith("Reg."):
        return GameType.REGULAR
    if text.startswith("Wild"):
        return GameType.WILD_CARD
    if text.startswith("Divisional"):
        return GameType.DIVISIONAL
    if text.startswith("Conference"):
        return GameType.CONFERENCE
    return GameType.BOWL


def _parse_week(text: str, game_type: GameType) -> str:
    match game_type:
        case GameType.REGULAR:
            return "{:0>2}".format(int(text.split(" ")[-1]) + 4)
        case GameType.WILD_CARD:
            return "22"
        case GameType.DIVISIONAL:
            return "23"
        case GameType.CONFERENCE:
            return "24"
        case GameType.BOWL:
            return "25"


def _map_team_id_to_city(league_name:str) -> dict[str, str]:
    csv_path = f"{league_data_path}{league_name}\\team_information.csv"
    mapping = {}

    with open(csv_path, "r") as file:
        for line in file.readlines():
            parts = line.split(",")
            mapping[parts[0]] = parts[14]

    return mapping


def _process_line(line: str, team_id_to_city_mapping: dict[str, str]) -> GameInfo | None:
    parts = line.split(",")

    if parts[2].startswith("Ex."):
        return None

    year = int(parts[0])
    id = int(parts[1])
    type = _parse_game_type(parts[2])
    week = _parse_week(parts[2], type)
    score_1 = int(parts[3])
    team_1_id = "{:0>2}".format(int(parts[4]))
    team_1 = team_id_to_city_mapping[parts[4]]
    score_2 = int(parts[5])
    team_2_id = "{:0>2}".format(parts[6])
    team_2 = team_id_to_city_mapping[parts[6]]


    if score_1 < score_2:
        return GameInfo(
            id=id,
            type=type.value,
            year=year,
            week=week,
            winning_score=score_2,
            winning_team=team_2,
            losing_score=score_1,
            losing_team=team_1,
            home_team_id=team_2_id,
            away_team_id=team_1_id,
        )
    return GameInfo(
        id=id,
        type=type.value,
        year=year,
        week=week,
        winning_score=score_1,
        winning_team=team_1,
        losing_score=score_2,
        losing_team=team_2,
        home_team_id=team_2_id,
        away_team_id=team_1_id,
    )


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
            game_info = _process_line(line, _map_team_id_to_city(league_name))
            if game_info:
                if first_year == 0:
                    first_year = game_info.year
                current_year = max(current_year, game_info.year)
                if game_info.winning_score not in scores[game_info.losing_score]:
                    scores[game_info.losing_score][game_info.winning_score] = game_info.__dict__
                    high_score = max(high_score, game_info.winning_score)
                else:
                    scores[game_info.losing_score][game_info.winning_score]["occurrences"] += 1

    return Scorigami(highest_score=high_score, first_year=first_year, last_year=current_year, scores=scores)


if __name__ == "__main__":
    scorigami = process_game_information("RZBRZB15")
    all_years = list(range(scorigami.first_year, scorigami.last_year + 1))
    index = Index(league="RZB", all_years=all_years, row_years=[all_years[i:i+5] for i in range(0, len(all_years), 5)])

    index.get_html()

    for year in all_years:
        scorigami.get_html(year)
