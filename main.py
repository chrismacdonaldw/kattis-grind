import typer
import random
import os
import re
import requests
import sys
import time
from typing import Optional
from lxml.html import fragment_fromstring

# kattis-grind modules
import scraper
import config as cfg
import status
import language
import constants

app = typer.Typer(name="kattis-grind", add_completion=False)
config_app = typer.Typer(help="Manage the .kattisrc configuration file.")
app.add_typer(config_app, name="config")


def guess_language_from_files(files: list[str]) -> Optional[str]:
    """Guess the programming language from file list."""
    return language.guess_language_from_files(files)


def find_main_file(lang: str, files: list[str]) -> str:
    """Find the main file for submission."""
    main_file = language.find_main_file(lang, files)
    return main_file if main_file else files[0]


def guess_main_class(lang: str, files: list[str]) -> Optional[str]:
    """Guess the main class for languages that need it."""
    return language.guess_main_class(lang, files)


def find_problem_files(problem_id: str, problems_directory: str) -> list[str]:
    """Find solution files for a problem in the problems directory."""
    from pathlib import Path

    problem_dir = Path(problems_directory) / problem_id
    if not problem_dir.exists():
        return []

    solution_files = []
    for ext in constants.SUPPORTED_EXTENSIONS.keys():
        potential_file = problem_dir / f"{problem_id}{ext}"
        if potential_file.exists():
            solution_files.append(str(potential_file))

    if not solution_files:
        for file_path in problem_dir.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix in constants.SUPPORTED_EXTENSIONS
            ):
                if not (
                    file_path.name.startswith("sample-") or file_path.suffix == ".html"
                ):
                    solution_files.append(str(file_path))

    return solution_files


def get_primary_extension_for_language(lang_name: str) -> str:
    """Get the primary file extension for a language name."""
    lang_info = language.get_language_info(lang_name)
    if lang_info and lang_info.extensions:
        return sorted(lang_info.extensions)[0]

    fallback_mapping = {
        "python": ".py",
        "cpp": ".cpp",
        "c++": ".cpp",
        "java": ".java",
        "javascript": ".js",
        "c": ".c",
        "go": ".go",
        "rust": ".rs",
        "ruby": ".rb",
        "kotlin": ".kt",
        "scala": ".scala",
        "swift": ".swift",
        "haskell": ".hs",
        "c#": ".cs",
        "bash": ".sh",
    }

    return fallback_mapping.get(lang_name.lower(), f".{lang_name}")


def login_to_kattis(kattis_config: cfg.KattisConfig) -> requests.Response:
    """Log in to Kattis using config credentials."""
    login_args = {
        "user": kattis_config.user.username,
        "script": "true",
        "token": kattis_config.user.token,
    }

    return requests.post(
        kattis_config.kattis.loginurl, data=login_args, headers=constants.HEADERS
    )


def submit_solution(
    submit_url: str,
    cookies,
    problem: str,
    language: str,
    files: list[str],
    mainclass: str = "",
) -> requests.Response:
    """Submit solution files to Kattis."""
    data = {
        "submit": "true",
        "submit_ctr": 2,
        "language": language,
        "mainclass": mainclass,
        "problem": problem,
        "tag": "",
        "script": "true",
    }

    sub_files = []
    for f in files:
        with open(f, "rb") as sub_file:
            sub_files.append(
                (
                    "sub_file[]",
                    (os.path.basename(f), sub_file.read(), "application/octet-stream"),
                )
            )

    return requests.post(
        submit_url,
        data=data,
        files=sub_files,
        cookies=cookies,
        headers=constants.HEADERS,
    )


def get_submission_url(
    submit_response: str, kattis_config: cfg.KattisConfig
) -> Optional[str]:
    """Extract submission URL from submit response."""
    m = re.search(r"Submission ID: (\d+)", submit_response)
    if m:
        submission_id = m.group(1)
        return kattis_config.kattis.get_submissions_url(submission_id)
    return None


def get_submission_status(submission_url: str, cookies) -> dict:
    """Get current status of a submission."""
    reply = requests.get(
        submission_url + "?json", cookies=cookies, headers=constants.HEADERS
    )
    return reply.json()




def show_judgement(submission_url: str, cookies) -> bool:
    """Show real-time judgement progress and return True if accepted."""
    while True:
        try:
            submission_status = get_submission_status(submission_url, cookies)
            status_id = submission_status["status_id"]
            testcases_done = submission_status["testcase_index"]
            testcases_total = submission_status["row_html"].count("<i") - 1

            status_info = status.get_status_info(status_id)
            status_text = status_info.name

            if (
                not status.is_final_status(status_id)
                and status_id != status.SubmissionStatus.RUNNING
            ):
                typer.echo(f"\r{status_text}...", nl=False)
            elif status_id == status.SubmissionStatus.COMPILE_ERROR:
                typer.secho(f"\r{status_text}", fg=typer.colors.RED, nl=False)
                try:
                    root = fragment_fromstring(
                        submission_status["feedback_html"], create_parent=True
                    )
                    error = root.find(".//pre").text
                    typer.secho(":", fg=typer.colors.RED)
                    typer.echo(error, nl=False)
                except:
                    pass
            else:
                typer.echo("\rTest cases: ", nl=False)
                if testcases_total == 0:
                    typer.echo("???", nl=False)
                else:
                    progress = ""
                    for i in re.findall(
                        r'<i class="([\w\- ]*)" title', submission_status["row_html"]
                    ):
                        if "is-empty" in i:
                            break
                        if "accepted" in i:
                            progress += "."
                        if "rejected" in i:
                            progress += "x"

                    if status_id == status.SubmissionStatus.RUNNING:
                        progress = progress[: 10 * (testcases_done - 1)] + "?"

                    typer.echo(
                        f'[{progress}{" " * (9*testcases_done + testcases_total - len(progress))}] {testcases_done} / {testcases_total}',
                        nl=False,
                    )

            sys.stdout.flush()

            if status.is_final_status(status_id):
                typer.echo()
                success = status.is_successful_status(status_id)
                try:
                    root = fragment_fromstring(
                        submission_status["row_html"], create_parent=True
                    )
                    cpu_time = root.xpath('.//*[@data-type="cpu"]')[0].text_content()
                    try:
                        score = re.findall(
                            r"\(([\d\.]+)\)",
                            root.xpath('.//*[@data-type="status"]')[0].text_content(),
                        )[0]
                        status_text += f" ({cpu_time}, {score})"
                    except:
                        status_text += f" ({cpu_time})"
                except:
                    pass

                if status_id != status.SubmissionStatus.COMPILE_ERROR:
                    typer.secho(
                        status_text,
                        fg=typer.colors.GREEN if success else typer.colors.RED,
                    )
                return success

            time.sleep(0.25)
        except Exception as e:
            typer.secho(f"Error checking submission status: {e}", fg=typer.colors.RED)
            return False


def _find_random_problem(
    min_diff: float,
    max_diff: float,
    seen_problems: set,
    scraper_config,
    id_only: bool = False,
):
    """Find a random problem within the difficulty range."""
    candidates = []
    max_pages_to_check = 20

    # Using random sampling to find a matching difficulty.
    # This is fast and suitable for most people using this tool.
    pages_to_check = random.sample(range(55), min(max_pages_to_check, 55))

    for page_num in pages_to_check:
        if not id_only:
            typer.echo(f"   Checking page {page_num}...")

        try:
            problems_on_page = scraper.get_problem_list(page_num, scraper_config)
            if not problems_on_page:
                continue

            page_candidates = [
                p
                for p in problems_on_page
                if min_diff <= p.difficulty <= max_diff and p.id not in seen_problems
            ]

            candidates.extend(page_candidates)

            if len(candidates) >= 5:
                break

        except Exception as e:
            if not id_only:
                typer.echo(f"   Warning: Failed to fetch page {page_num}: {e}")
            continue

    return random.choice(candidates) if candidates else None


def _setup_problem_directory(
    problem_data: scraper.ProblemData, kattis_config: cfg.KattisConfig
):
    """Create the problem directory with samples and boilerplate files."""
    problem_dir = kattis_config.settings.problems_directory / problem_data.id

    if problem_dir.exists():
        typer.secho(
            f"Problem directory '{problem_dir}' already exists. Skipping.",
            fg=typer.colors.YELLOW,
        )
        return

    problem_dir.mkdir(parents=True)
    typer.echo(f"-> Created directory: {problem_dir}")

    html_path = problem_dir / f"{problem_data.id}.html"
    html_path.write_text(problem_data.html_content)
    typer.echo(f"   Saved problem description")

    for i, sample in enumerate(problem_data.samples, 1):
        input_path = problem_dir / f"sample-{i}.in"
        output_path = problem_dir / f"sample-{i}.ans"
        input_path.write_text(sample.input)
        output_path.write_text(sample.output)

    if problem_data.samples:
        typer.echo(f"   Saved {len(problem_data.samples)} sample case(s)")

    for lang in kattis_config.settings.languages:
        template_content = cfg.get_template_content(lang, kattis_config)
        if template_content:
            extension = get_primary_extension_for_language(lang)
            file_path = problem_dir / f"{problem_data.id}{extension}"
            file_path.write_text(template_content)
            if lang.lower() == "python" or extension == ".py":
                file_path.chmod(0o755)
            typer.echo(f"   Created {lang.upper()} boilerplate")

    cfg.add_to_seen(problem_data.id)
    typer.secho(
        f"{constants.Messages.SUCCESS_PREFIX} {constants.Messages.PROBLEM_SETUP_SUCCESS} '{problem_data.id}'",
        fg=typer.colors.GREEN,
        bold=True,
    )


@config_app.command("init")
def config_init():
    """Creates a default .kattisrc file in your home directory."""
    cfg.create_default_config()


@app.command()
def fetch(problem_id: str):
    """Fetches a problem and sets up the directory."""
    try:
        kattis_config = cfg.load_config()
    except FileNotFoundError:
        raise typer.Exit(code=1)

    scraper_config = cfg.get_scraper_config_from_kattis_config(kattis_config)

    typer.echo(f"-> Fetching '{problem_id}'...")
    problem_data = scraper.get_problem_details(
        problem_id, scraper_config, include_hints=kattis_config.settings.include_hints
    )
    if not problem_data:
        typer.secho(f"Could not fetch problem '{problem_id}'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Found problem: '{problem_data.name}'", fg=typer.colors.GREEN)
    if problem_data.hint:
        typer.secho(
            f"Hint: {problem_data.hint.problem_type} - {problem_data.hint.hint_text}",
            fg=typer.colors.CYAN,
        )
    _setup_problem_directory(problem_data, kattis_config)


@app.command()
def submit(
    files_or_problem: list[str] = typer.Argument(
        ..., help="Solution files to submit OR problem ID (if only one argument)"
    ),
    problem: Optional[str] = typer.Option(
        None, "--problem", "-p", help="Problem ID to submit to"
    ),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Programming language"
    ),
    mainclass: Optional[str] = typer.Option(
        None, "--mainclass", "-m", help="Main class name"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """
    Submits your solution to Kattis.

    Usage:
      kattis-grind submit <problem_id>           # Auto-find files in problems directory
      kattis-grind submit <file1> [file2...]     # Submit specific files
    """
    try:
        kattis_config = cfg.load_config()
    except FileNotFoundError:
        typer.secho(
            "Configuration not found. Please run 'kattis-grind config init' first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    if not kattis_config.user.username or not kattis_config.user.token:
        typer.secho(
            "Username or token not configured. Please edit your .kattisrc file.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    files = files_or_problem
    if len(files_or_problem) == 1 and not os.path.exists(files_or_problem[0]):
        potential_problem_id = files_or_problem[0]
        found_files = find_problem_files(
            potential_problem_id, str(kattis_config.settings.problems_directory)
        )

        if found_files:
            if len(found_files) == 1:
                typer.echo(
                    f"-> Found solution file for problem '{potential_problem_id}': {found_files[0]}"
                )
                files = found_files
            else:
                typer.echo(
                    f"-> Found multiple solution files for problem '{potential_problem_id}':"
                )
                for i, f in enumerate(found_files, 1):
                    file_lang = guess_language_from_files([f])
                    typer.echo(f"   {i}. {f} ({file_lang or 'unknown'})")

                preferred_file = None
                for preferred_lang in kattis_config.settings.languages:
                    for f in found_files:
                        if guess_language_from_files([f]) == preferred_lang:
                            preferred_file = f
                            break
                    if preferred_file:
                        break

                if preferred_file and not force:
                    use_preferred = typer.confirm(
                        f"Use {preferred_file} ({guess_language_from_files([preferred_file])})?",
                        default=True,
                    )
                    if use_preferred:
                        files = [preferred_file]
                        typer.echo(f"-> Using: {preferred_file}")
                    else:
                        choice = typer.prompt("Enter file number to submit", type=int)
                        if 1 <= choice <= len(found_files):
                            files = [found_files[choice - 1]]
                            typer.echo(f"-> Using: {files[0]}")
                        else:
                            typer.secho("Invalid choice.", fg=typer.colors.RED)
                            raise typer.Exit(code=1)
                elif preferred_file:
                    files = [preferred_file]
                    typer.echo(
                        f"-> Auto-selected: {preferred_file} ({guess_language_from_files([preferred_file])})"
                    )
                else:
                    if force:
                        files = [found_files[0]]
                        typer.echo(
                            f"-> Auto-selected: {files[0]} ({guess_language_from_files(files) or 'unknown'})"
                        )
                    else:
                        choice = typer.prompt("Enter file number to submit", type=int)
                        if 1 <= choice <= len(found_files):
                            files = [found_files[choice - 1]]
                            typer.echo(f"-> Using: {files[0]}")
                        else:
                            typer.secho("Invalid choice.", fg=typer.colors.RED)
                            raise typer.Exit(code=1)

            if not problem:
                problem = potential_problem_id
        else:
            typer.secho(
                f"No solution files found for problem '{potential_problem_id}' in {kattis_config.settings.problems_directory}",
                fg=typer.colors.RED,
            )
            typer.secho(
                f"Expected directory: {kattis_config.settings.problems_directory / potential_problem_id}",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)

    for file_path in files:
        if not os.path.exists(file_path):
            typer.secho(f"File not found: {file_path}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    if not problem:
        problem = os.path.splitext(os.path.basename(files[0]))[0].lower()

    if not language:
        language = guess_language_from_files(files)
        if not language:
            ext = os.path.splitext(files[0])[1]
            typer.secho(
                f"Could not guess language from extension '{ext}'. Please specify with --language.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

    if not mainclass:
        mainclass = guess_main_class(language, files) or ""

    typer.echo(f"Problem: {problem}")
    typer.echo(f"Language: {language}")
    typer.echo(f"Files: {', '.join(files)}")
    if mainclass:
        import language as lang_module

        lang_info = lang_module.get_language_info(language)
        if lang_info and lang_info.needs_mainfile:
            typer.echo(f"Main file: {mainclass}")
        else:
            typer.echo(f"Mainclass: {mainclass}")

    if not force:
        if not typer.confirm("Submit (y/N)?", default=False):
            typer.echo("Submission cancelled.")
            raise typer.Exit(code=0)

    try:
        login_reply = login_to_kattis(kattis_config)
    except requests.exceptions.RequestException as err:
        typer.secho(f"Login connection failed: {err}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if login_reply.status_code != 200:
        typer.secho("Login failed.", fg=typer.colors.RED)
        if login_reply.status_code == 403:
            typer.secho("Incorrect username or token (403)", fg=typer.colors.RED)
            typer.secho("This could happen if:", fg=typer.colors.YELLOW)
            typer.secho("  - Your token has expired", fg=typer.colors.YELLOW)
            typer.secho(
                "  - You need to download a fresh .kattisrc from Kattis",
                fg=typer.colors.YELLOW,
            )
        elif login_reply.status_code == 404:
            typer.secho("Incorrect login URL (404)", fg=typer.colors.RED)
        else:
            typer.secho(f"Status code: {login_reply.status_code}", fg=typer.colors.RED)
            typer.secho(
                f"Response: {login_reply.text[:200]}...", fg=typer.colors.YELLOW
            )
        raise typer.Exit(code=1)

    typer.secho("Login successful", fg=typer.colors.GREEN)

    typer.echo("-> Submitting solution...")
    try:
        result = submit_solution(
            kattis_config.kattis.submissionurl,
            login_reply.cookies,
            problem,
            language,
            files,
            mainclass,
        )
    except requests.exceptions.RequestException as err:
        typer.secho(f"Submit connection failed: {err}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if result.status_code != 200:
        typer.secho("Submission failed.", fg=typer.colors.RED)
        if result.status_code == 403:
            typer.secho("Access denied (403)", fg=typer.colors.RED)
        elif result.status_code == 404:
            typer.secho("Incorrect submit URL (404)", fg=typer.colors.RED)
        else:
            typer.secho(f"Status code: {result.status_code}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    plain_result = result.content.decode("utf-8").replace("<br />", "\n")
    typer.echo(plain_result)

    # Get submission URL and show live judgement
    submission_url = get_submission_url(plain_result, kattis_config)
    if submission_url:
        typer.echo(f"-> Watching submission: {submission_url}")
        success = show_judgement(submission_url, login_reply.cookies)
        if not success:
            raise typer.Exit(code=1)
    else:
        typer.secho(
            "Could not extract submission URL for live tracking.",
            fg=typer.colors.YELLOW,
        )


@app.command()
def rand(
    min_diff: Optional[float] = typer.Option(None, "--min", help="Minimum difficulty"),
    max_diff: Optional[float] = typer.Option(None, "--max", help="Maximum difficulty"),
    do_fetch: bool = typer.Option(
        False, "--fetch", "-f", help="Fetch the problem immediately"
    ),
    id_only: bool = typer.Option(
        False, "--id-only", "-i", help="Output only the problem ID"
    ),
):
    """Find a random unfetched problem within a difficulty range."""
    try:
        kattis_config = cfg.load_config()
    except FileNotFoundError:
        raise typer.Exit(code=1)

    scraper_config = cfg.get_scraper_config_from_kattis_config(kattis_config)

    min_d = min_diff if min_diff is not None else kattis_config.settings.difficulty[0]
    max_d = max_diff if max_diff is not None else kattis_config.settings.difficulty[1]

    if min_d > max_d:
        typer.secho(
            "Error: Minimum difficulty cannot be greater than maximum difficulty.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    if not id_only:
        typer.echo(f"-> Searching for problem with difficulty [{min_d}, {max_d}]...")

    seen_problems = cfg.get_seen_problems()
    chosen_problem = _find_random_problem(
        min_d, max_d, seen_problems, scraper_config, id_only
    )

    if not chosen_problem:
        typer.secho("No matching problems found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if id_only:
        typer.echo(chosen_problem.id)
        raise typer.Exit()

    typer.secho(
        f"\nFound: {chosen_problem.name} (ID: {chosen_problem.id}, Difficulty: {chosen_problem.difficulty})",
        fg=typer.colors.CYAN,
        bold=True,
    )

    should_fetch = do_fetch or typer.confirm(
        "Fetch this problem now?", default=False, abort=True
    )

    if should_fetch:
        typer.echo(f"-> Fetching '{chosen_problem.id}'...")
        problem_data = scraper.get_problem_details(
            chosen_problem.id,
            scraper_config,
            include_hints=kattis_config.settings.include_hints,
        )
        if not problem_data:
            typer.secho(
                f"Error: Could not fetch problem details for '{chosen_problem.id}'.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        if problem_data.hint:
            typer.secho(
                f"Hint: {problem_data.hint.problem_type} - {problem_data.hint.hint_text}",
                fg=typer.colors.CYAN,
            )
        _setup_problem_directory(problem_data, kattis_config)


if __name__ == "__main__":
    app()
