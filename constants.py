import os
from pathlib import Path

KATTIS_GRIND_HOME_ENV = "KATTIS_GRIND_HOME"


def get_config_search_paths():
    """Get list of paths to search for .kattisrc file."""
    paths = []

    if KATTIS_GRIND_HOME_ENV in os.environ:
        custom_home = Path(os.environ[KATTIS_GRIND_HOME_ENV])
        paths.append(custom_home / ".kattisrc")

    paths.append(Path.home() / ".kattisrc")
    paths.append(Path(".kattisrc"))
    paths.append(Path("../.kattisrc"))
    paths.append(Path.home() / ".kattis-grind" / ".kattisrc")

    return paths


def get_problems_directory():
    """Get the directory where problems should be stored."""
    if KATTIS_GRIND_HOME_ENV in os.environ:
        custom_home = Path(os.environ[KATTIS_GRIND_HOME_ENV])
        return custom_home / "kattis_problems"

    return Path("./kattis_problems")


HEADERS = {
    "User-Agent": "kattis-grind (https://github.com/chrismacdonaldw/kattis-grind)"
}

DEFAULT_KATTIS_HOSTNAME = "open.kattis.com"
DEFAULT_LOGIN_URL = "https://{DEFAULT_KATTIS_HOSTNAME}/login"
DEFAULT_SUBMISSION_URL = "https://{DEFAULT_KATTIS_HOSTNAME}/submit"
DEFAULT_LANGUAGES = ["cpp", "python"]
DEFAULT_DIFFICULTY_RANGE = (1.5, 3.0)
DEFAULT_PROBLEMS_DIRECTORY = "kattis_problems"

DEFAULT_SCRAPER_TIMEOUT = 10
DEFAULT_SCRAPER_MAX_RETRIES = 3
DEFAULT_SCRAPER_BACKOFF_FACTOR = 0.5

SUPPORTED_EXTENSIONS = {
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c++": "cpp",
    ".py": "python",
    ".java": "java",
    ".cs": "csharp",
    ".js": "javascript",
    ".go": "go",
    ".rs": "rust",
}


class Messages:
    SUCCESS_PREFIX = "[SUCCESS]"
    ERROR_PREFIX = "[ERROR]"
    WARNING_PREFIX = "[WARNING]"
    INFO_PREFIX = "[INFO]"

    PROBLEM_SETUP_SUCCESS = "Successfully set up problem"
    PROBLEM_FETCH_SUCCESS = "Problem fetched successfully"
    LOGIN_SUCCESS = "Login successful"
    SUBMISSION_SUCCESS = "Submission completed"

    CONFIG_NOT_FOUND = "Configuration file not found"
    INVALID_CREDENTIALS = "Invalid username or token"
    NETWORK_ERROR = "Network connection failed"
    PARSE_ERROR = "Failed to parse response"
