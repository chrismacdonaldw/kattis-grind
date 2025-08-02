import dataclasses
import requests
import time
import typer
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from urllib.parse import urljoin
import constants


@dataclasses.dataclass
class ScraperConfig:
    """Configuration for the scraper."""

    base_url: str
    timeout: int = constants.DEFAULT_SCRAPER_TIMEOUT
    max_retries: int = constants.DEFAULT_SCRAPER_MAX_RETRIES
    backoff_factor: float = constants.DEFAULT_SCRAPER_BACKOFF_FACTOR
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = constants.HEADERS


@dataclasses.dataclass
class Problem:
    """Represents a single problem from the Kattis problem list."""

    id: str
    name: str
    url: str
    difficulty: float


@dataclasses.dataclass
class Sample:
    """Represents a single sample case (input and output)."""

    input: str
    output: str


@dataclasses.dataclass
class Hint:
    """Represents a hint for a problem from Steve Halim's site."""

    problem_type: str
    hint_text: str


@dataclasses.dataclass
class ProblemData:
    """Represents the full details of a fetched problem."""

    id: str
    name: str
    html_content: str
    samples: List[Sample]
    hint: Optional[Hint] = None


class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


def _make_request_with_retry(url: str, config: ScraperConfig) -> requests.Response:
    """Make a HTTP request with retry logic and exponential backoff."""
    last_exception = None

    for attempt in range(config.max_retries):
        try:
            response = requests.get(url, headers=config.headers, timeout=config.timeout)
            response.raise_for_status()
            return response

        except requests.RequestException as e:
            last_exception = e
            if attempt < config.max_retries - 1:
                sleep_time = config.backoff_factor * (2**attempt)
                time.sleep(sleep_time)

    raise ScraperError(
        f"Failed to fetch {url} after {config.max_retries} attempts: {last_exception}"
    )


def _validate_problem_data(problem: Problem) -> bool:
    """Validate that a Problem object has all required fields."""
    if not problem.id or not problem.id.strip():
        return False
    if not problem.name or not problem.name.strip():
        return False
    if not problem.url or not problem.url.startswith("http"):
        return False
    if not isinstance(problem.difficulty, (int, float)) or problem.difficulty < 0:
        return False
    return True


def _extract_samples(problem_body) -> List[Sample]:
    """Extract sample cases from the problem body."""
    samples = []

    sample_selectors = [
        "table.sample",
        'table[class*="sample"]',
        ".sample-data table",
        "div.sample table",
    ]

    for selector in sample_selectors:
        tables = problem_body.select(selector)
        if tables:
            break
    else:
        return samples

    for table in tables:
        try:
            # Look for pre tags containing input/output
            pre_tags = table.find_all("pre")

            if len(pre_tags) >= 2:
                # Standard case: input and output in separate pre tags
                input_text = pre_tags[0].get_text().strip()
                output_text = pre_tags[1].get_text().strip()

                if input_text or output_text:  # At least one should have content
                    samples.append(Sample(input=input_text, output=output_text))

            elif len(pre_tags) == 1:
                content = pre_tags[0].get_text().strip()
                if content:
                    samples.append(Sample(input=content, output=""))

        except Exception:
            continue

        table.decompose()

    return samples


def get_problem_list(
    page: int = 0, config: ScraperConfig = None
) -> Optional[List[Problem]]:
    """
    Scrapes a single page of the problem list, ordered by difficulty.
    """
    if config is None:
        typer.secho("Error: ScraperConfig is required", fg=typer.colors.RED)
        return None

    if page < 0:
        page = 0

    url = f"{config.base_url}/problems?order=difficulty_data&page={page}"

    try:
        response = _make_request_with_retry(url, config)
    except ScraperError as e:
        typer.secho(
            f"Failed to fetch problem list page {page}: {e}", fg=typer.colors.RED
        )
        return None

    try:
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.select_one('section[data-cy="problems-table"] tbody')

        if not table:
            return None

        problems = []

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            try:
                link = cells[0].find("a")
                if not link or not link.get("href"):
                    continue

                problem_id = link["href"].split("/")[-1]
                problem_name = link.get_text().strip()
                problem_url = urljoin(config.base_url, link["href"])

                # Extract difficulty
                difficulty_span = cells[6].find("span")
                if not difficulty_span:
                    continue

                difficulty_str = difficulty_span.get_text().strip()
                difficulty = float(difficulty_str.split("-")[0].strip())

                # Create and validate problem object
                problem = Problem(
                    id=problem_id,
                    name=problem_name,
                    url=problem_url,
                    difficulty=difficulty,
                )

                if _validate_problem_data(problem):
                    problems.append(problem)

            except (AttributeError, ValueError, IndexError):
                continue

        return problems

    except Exception as e:
        typer.secho(f"Failed to parse problem list: {e}", fg=typer.colors.RED)
        return None


def get_hint_for_problem(problem_id: str) -> Optional[Hint]:
    """
    Fetches hint information for a problem from Steve Halim's cpbook.net site.
    """
    if not problem_id or not problem_id.strip():
        return None

    problem_id = problem_id.strip()
    url = "https://cpbook.net/methodstosolve?oj=kattis&topic=all&quality=all"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"id": "problemtable"})

        if not table:
            return None

        tbody = table.find("tbody")
        if not tbody:
            return None

        rows = tbody.find_all("tr")

        for row in rows:
            tds = row.find_all("td")
            if len(tds) >= 4:
                row_problem_id = tds[0].get_text().strip()
                if row_problem_id == problem_id:
                    problem_type = tds[2].get_text().strip()  # 3rd column (index 2)
                    hint_text = tds[3].get_text().strip()  # 4th column (index 3)

                    if problem_type and hint_text:
                        return Hint(problem_type=problem_type, hint_text=hint_text)

        return None

    except Exception:
        # Silently fail for hints - they're optional
        return None


def get_problem_details(
    problem_id: str, config: ScraperConfig = None, include_hints: bool = False
) -> Optional[ProblemData]:
    """
    Fetches the full problem description and sample cases for a given problem_id.
    """
    if config is None:
        typer.secho("Error: ScraperConfig is required", fg=typer.colors.RED)
        return None

    if not problem_id or not problem_id.strip():
        typer.secho("Error: Empty problem_id provided", fg=typer.colors.RED)
        return None

    problem_id = problem_id.strip()
    url = f"{config.base_url}/problems/{problem_id}"

    try:
        response = _make_request_with_retry(url, config)
    except ScraperError as e:
        typer.secho(
            f"Failed to fetch problem details for {problem_id}: {e}",
            fg=typer.colors.RED,
        )
        return None

    try:
        soup = BeautifulSoup(response.content, "html.parser")

        problem_body = soup.find("div", class_="problembody")
        name_header = soup.find("h1")

        if not problem_body:
            typer.secho(f"No problem body found for {problem_id}", fg=typer.colors.RED)
            return None

        if not name_header:
            problem_name = problem_id
        else:
            problem_name = name_header.get_text().strip()

        samples = _extract_samples(problem_body)
        html_content = str(problem_body)

        # Fetch hints if requested
        hint = None
        if include_hints:
            hint = get_hint_for_problem(problem_id)

        return ProblemData(
            id=problem_id,
            name=problem_name,
            html_content=html_content,
            samples=samples,
            hint=hint,
        )

    except Exception as e:
        typer.secho(
            f"Failed to parse problem details for {problem_id}: {e}",
            fg=typer.colors.RED,
        )
        return None
