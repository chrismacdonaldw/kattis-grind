import configparser
import dataclasses
import os
from pathlib import Path
from typing import Set, Dict, Optional
import typer
import constants


def get_config_dir() -> Path:
    """Get the configuration directory, respecting KATTIS_GRIND_HOME if set."""
    if constants.KATTIS_GRIND_HOME_ENV in os.environ:
        return Path(os.environ[constants.KATTIS_GRIND_HOME_ENV])
    return Path.home() / ".kattis-grind"


CONFIG_DIR = get_config_dir()
CONFIG_PATH = CONFIG_DIR / ".kattisrc"
SEEN_PATH = CONFIG_DIR / "seen.txt"


@dataclasses.dataclass
class UserConfig:
    username: str
    token: str


@dataclasses.dataclass
class KattisUrls:
    hostname: str
    loginurl: str
    submissionurl: str

    def get_base_url(self) -> str:
        """Get the base URL for the Kattis instance."""
        return f"https://{self.hostname}"

    def get_problem_url(self, problem_id: str) -> str:
        """Get the URL for a specific problem."""
        return f"{self.get_base_url()}/problems/{problem_id}"

    def get_problems_list_url(
        self, page: int = 0, order: str = "difficulty_data"
    ) -> str:
        """Get the URL for the problems list page."""
        return f"{self.get_base_url()}/problems?order={order}&page={page}"

    def get_submissions_url(self, submission_id: Optional[str] = None) -> str:
        """Get the URL for submissions (optionally for a specific submission)."""
        base = f"{self.get_base_url()}/submissions"
        return f"{base}/{submission_id}" if submission_id else base

    def get_user_profile_url(self, username: str) -> str:
        """Get the URL for a user's profile."""
        return f"{self.get_base_url()}/users/{username}"


@dataclasses.dataclass
class SettingsConfig:
    languages: list[str]
    difficulty: tuple[float, float]
    problems_directory: Path
    include_hints: bool = False
    scraper_timeout: int = constants.DEFAULT_SCRAPER_TIMEOUT
    scraper_max_retries: int = constants.DEFAULT_SCRAPER_MAX_RETRIES
    scraper_backoff_factor: float = constants.DEFAULT_SCRAPER_BACKOFF_FACTOR


@dataclasses.dataclass
class KattisConfig:
    user: UserConfig
    kattis: KattisUrls
    settings: SettingsConfig
    templates: Dict[str, Path]


def load_config() -> KattisConfig:
    """Loads and parses the .kattisrc file."""
    parser = configparser.ConfigParser()

    config_paths = constants.get_config_search_paths()

    config_found = False
    for config_path in config_paths:
        if config_path.exists():
            parser.read(config_path)
            config_found = True
            break

    if not config_found:
        typer.secho(
            f"{constants.Messages.ERROR_PREFIX} {constants.Messages.CONFIG_NOT_FOUND}",
            fg=typer.colors.RED,
        )
        typer.echo("Searched in:")
        for path in config_paths:
            typer.echo(f"  - {path}")
        typer.echo(
            "Please run 'kattis-grind config init' to create one or download from Kattis."
        )
        if constants.KATTIS_GRIND_HOME_ENV not in os.environ:
            typer.secho(
                f"Tip: You can set {constants.KATTIS_GRIND_HOME_ENV} environment variable to specify a custom location.",
                fg=typer.colors.YELLOW,
            )
        raise FileNotFoundError

    def parse_difficulty(s: str) -> tuple[float, float]:
        parts = [float(p.strip()) for p in s.split("-")]
        return (parts[0], parts[1])

    config = KattisConfig(
        user=UserConfig(
            username=parser.get("user", "username", fallback=""),
            token=parser.get("user", "token", fallback=""),
        ),
        kattis=KattisUrls(
            hostname=parser.get(
                "kattis", "hostname", fallback=constants.DEFAULT_KATTIS_HOSTNAME
            ),
            loginurl=parser.get(
                "kattis", "loginurl", fallback=constants.DEFAULT_LOGIN_URL
            ),
            submissionurl=parser.get(
                "kattis", "submissionurl", fallback=constants.DEFAULT_SUBMISSION_URL
            ),
        ),
        settings=SettingsConfig(
            languages=[
                lang.strip()
                for lang in parser.get(
                    "settings",
                    "languages",
                    fallback=",".join(constants.DEFAULT_LANGUAGES),
                ).split(",")
            ],
            difficulty=parse_difficulty(
                parser.get(
                    "settings",
                    "difficulty",
                    fallback=f"{constants.DEFAULT_DIFFICULTY_RANGE[0]}-{constants.DEFAULT_DIFFICULTY_RANGE[1]}",
                )
            ),
            problems_directory=Path(
                parser.get(
                    "settings",
                    "problems_directory",
                    fallback=constants.DEFAULT_PROBLEMS_DIRECTORY,
                )
            ).expanduser(),
            include_hints=parser.getboolean(
                "settings", "include_hints", fallback=False
            ),
            scraper_timeout=parser.getint(
                "settings",
                "scraper_timeout",
                fallback=constants.DEFAULT_SCRAPER_TIMEOUT,
            ),
            scraper_max_retries=parser.getint(
                "settings",
                "scraper_max_retries",
                fallback=constants.DEFAULT_SCRAPER_MAX_RETRIES,
            ),
            scraper_backoff_factor=parser.getfloat(
                "settings",
                "scraper_backoff_factor",
                fallback=constants.DEFAULT_SCRAPER_BACKOFF_FACTOR,
            ),
        ),
        templates={},
    )

    if parser.has_section("templates"):
        config.templates = {
            lang: Path(path).expanduser()
            for lang, path in parser.items("templates")
            if lang != "DEFAULT"
        }
    else:
        config.templates = {}

    return config


def get_seen_problems() -> Set[str]:
    """Reads the set of fetched problem IDs from the seen file."""
    if not SEEN_PATH.exists():
        return set()
    return set(SEEN_PATH.read_text().splitlines())


def add_to_seen(problem_id: str):
    """Adds a problem ID to the seen file."""
    CONFIG_DIR.mkdir(exist_ok=True)
    with SEEN_PATH.open("a") as f:
        f.write(f"{problem_id}\n")


def get_template_content(language: str, config: KattisConfig) -> str:
    """Get template content for a language from custom template."""
    if language in config.templates:
        template_path = config.templates[language]
        if template_path.is_file():
            try:
                return template_path.read_text(encoding="utf-8")
            except (IOError, UnicodeDecodeError):
                pass

    return ""


def create_default_config():
    """Creates a default .kattisrc file if one doesn't exist."""
    CONFIG_DIR.mkdir(exist_ok=True)
    if CONFIG_PATH.exists():
        typer.secho(f"'{CONFIG_PATH}' already exists. Doing nothing.", fg=typer.colors.YELLOW)
        return

    template_path = Path(__file__).parent / "templates" / "default_kattisrc"

    try:
        default_config_text = template_path.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError) as e:
        typer.secho(f"Error reading default config template: {e}", fg=typer.colors.RED)
        typer.echo("Creating a minimal config file instead.")
        default_config_text = f"""\
[user]
username = YOUR_USERNAME_HERE
token = YOUR_TOKEN_HERE

[kattis]
hostname = {constants.DEFAULT_KATTIS_HOSTNAME}
loginurl = {constants.DEFAULT_LOGIN_URL}
submissionurl = {constants.DEFAULT_SUBMISSION_URL}

[settings]
languages = {', '.join(constants.DEFAULT_LANGUAGES)}
difficulty = {constants.DEFAULT_DIFFICULTY_RANGE[0]}-{constants.DEFAULT_DIFFICULTY_RANGE[1]}
problems_directory = {constants.DEFAULT_PROBLEMS_DIRECTORY}

[templates]
"""

    CONFIG_PATH.write_text(default_config_text)
    typer.secho(f"Created default configuration file at: {CONFIG_PATH}", fg=typer.colors.GREEN)
    typer.echo("Edit it with your username and token.")


def validate_config(config: KattisConfig) -> list[str]:
    """
    Validate the configuration and return a list of issues found.
    """
    issues = []

    if not config.user.username or config.user.username == "YOUR_USERNAME_HERE":
        issues.append("Username not configured")

    if not config.user.token or config.user.token == "YOUR_TOKEN_HERE":
        issues.append("Token not configured")

    if not config.kattis.hostname:
        issues.append("Hostname not configured")

    if not config.kattis.loginurl or not config.kattis.loginurl.startswith("http"):
        issues.append("Invalid login URL")

    if not config.kattis.submissionurl or not config.kattis.submissionurl.startswith(
        "http"
    ):
        issues.append("Invalid submission URL")

    if not config.settings.languages:
        issues.append("No languages configured")

    if (
        len(config.settings.difficulty) != 2
        or config.settings.difficulty[0] > config.settings.difficulty[1]
    ):
        issues.append("Invalid difficulty range")

    if not config.settings.problems_directory:
        issues.append("Problems directory not configured")

    return issues


def get_scraper_config_from_kattis_config(kattis_config: KattisConfig):
    """
    Convert KattisConfig to ScraperConfig for use with the scraper module.
    """
    import scraper

    return scraper.ScraperConfig(
        base_url=kattis_config.kattis.get_base_url(),
        timeout=kattis_config.settings.scraper_timeout,
        max_retries=kattis_config.settings.scraper_max_retries,
        backoff_factor=kattis_config.settings.scraper_backoff_factor,
        headers=constants.HEADERS,
    )
