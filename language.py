import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class LanguageInfo:
    """Information about a programming language."""

    name: str
    extensions: Set[str]
    needs_mainclass: bool = False
    needs_mainfile: bool = False
    main_patterns: List[str] = None
    comment_patterns: List[str] = None

    def __post_init__(self):
        if self.main_patterns is None:
            self.main_patterns = []
        if self.comment_patterns is None:
            self.comment_patterns = []


LANGUAGES = {
    "C": LanguageInfo(
        name="C",
        extensions={".c"},
        main_patterns=[r"\bmain\s*\("],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "C++": LanguageInfo(
        name="C++",
        extensions={".cpp", ".cc", ".cxx", ".c++", ".C"},
        main_patterns=[r"\bmain\s*\("],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "C#": LanguageInfo(
        name="C#",
        extensions={".cs"},
        needs_mainclass=True,
        main_patterns=[r"\bstatic\s+void\s+Main\s*\("],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "Go": LanguageInfo(
        name="Go",
        extensions={".go"},
        main_patterns=[r"\bfunc\s+main\s*\("],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "Haskell": LanguageInfo(
        name="Haskell",
        extensions={".hs"},
        main_patterns=[r"\bmain\s*=", r"\bmain\s*::"],
        comment_patterns=[r"--.*", r"\{-.*?-\}"],
    ),
    "Java": LanguageInfo(
        name="Java",
        extensions={".java"},
        needs_mainclass=True,
        main_patterns=[
            r"\bpublic\s+static\s+void\s+main\s*\(",
            r"\bstatic\s+public\s+void\s+main\s*\(",
        ],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "JavaScript (Node.js)": LanguageInfo(
        name="JavaScript (Node.js)",
        extensions={".js"},
        needs_mainfile=True,
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "Kotlin": LanguageInfo(
        name="Kotlin",
        extensions={".kt"},
        needs_mainclass=True,
        main_patterns=[r"\bfun\s+main\s*\("],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "Python 3": LanguageInfo(
        name="Python 3",
        extensions={".py"},
        needs_mainfile=True,
        main_patterns=[r'if\s+__name__\s*==\s*["\']__main__["\']'],
        comment_patterns=[r"#.*", r'""".*?"""', r"'''.*?'''"],
    ),
    "Python 2": LanguageInfo(
        name="Python 2",
        extensions={".py2"},
        needs_mainfile=True,
        main_patterns=[r'if\s+__name__\s*==\s*["\']__main__["\']'],
        comment_patterns=[r"#.*", r'""".*?"""', r"'''.*?'''"],
    ),
    "Ruby": LanguageInfo(
        name="Ruby", extensions={".rb"}, needs_mainfile=True, comment_patterns=[r"#.*"]
    ),
    "Rust": LanguageInfo(
        name="Rust",
        extensions={".rs"},
        needs_mainfile=True,
        main_patterns=[r"\bfn\s+main\s*\("],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "Scala": LanguageInfo(
        name="Scala",
        extensions={".scala"},
        needs_mainclass=True,
        main_patterns=[r"\bdef\s+main\s*\("],
        comment_patterns=[r"//.*", r"/\*.*?\*/"],
    ),
    "Swift": LanguageInfo(
        name="Swift", extensions={".swift"}, comment_patterns=[r"//.*", r"/\*.*?\*/"]
    ),
    "Bash": LanguageInfo(
        name="Bash", extensions={".sh"}, needs_mainfile=True, comment_patterns=[r"#.*"]
    ),
}

_EXTENSION_TO_LANGUAGE = {}
for lang_name, lang_info in LANGUAGES.items():
    for ext in lang_info.extensions:
        _EXTENSION_TO_LANGUAGE[ext] = lang_name


def guess_language_from_extension(file_path: str) -> Optional[str]:
    """
    Guess programming language from file extension.
    """
    if file_path.startswith(".") and "/" not in file_path and "\\" not in file_path:
        ext = file_path.lower()
    else:
        ext = Path(file_path).suffix.lower()

    if file_path.endswith(".C"):
        return "C++"

    if ext == ".h":
        return None  # Will be handled by guess_language_from_files

    return _EXTENSION_TO_LANGUAGE.get(ext)


def guess_language_from_files(files: List[str]) -> Optional[str]:
    """
    Guess programming language from a list of files.
    """
    if not files:
        return None

    extension_counts = {}
    has_header = False

    for file_path in files:
        ext = Path(file_path).suffix.lower()
        if ext == ".h":
            has_header = True
            continue

        lang = guess_language_from_extension(file_path)
        if lang:
            extension_counts[lang] = extension_counts.get(lang, 0) + 1

    if has_header and not extension_counts:
        c_files = [f for f in files if f.endswith(".c")]
        if c_files:
            return "C"
        else:
            return "C++"

    if extension_counts:
        return max(extension_counts.items(), key=lambda x: x[1])[0]

    return None


def find_main_file(language: str, files: List[str]) -> Optional[str]:
    """
    Find the main file for a given language and list of files.
    """
    if language not in LANGUAGES:
        return files[0] if files else None

    lang_info = LANGUAGES[language]

    for file_path in files:
        basename = Path(file_path).stem
        if basename.lower() in ["main"]:
            return file_path

    if lang_info.main_patterns:
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for pattern in lang_info.main_patterns:
                        if re.search(pattern, content, re.MULTILINE):
                            return file_path
            except (UnicodeDecodeError, IOError, OSError):
                continue

    return files[0] if files else None


def guess_main_class(language: str, files: List[str]) -> Optional[str]:
    """
    Guess the main class name for languages that require it.
    """
    if language not in LANGUAGES:
        return None

    lang_info = LANGUAGES[language]

    if lang_info.needs_mainfile and len(files) > 1:
        main_file = find_main_file(language, files)
        if main_file:
            return Path(main_file).name

    if lang_info.needs_mainclass:
        main_file = find_main_file(language, files)
        if main_file:
            name = Path(main_file).stem

            if language == "Kotlin":
                return name[0].upper() + name[1:] + "Kt" if name else None

            return name

    return None


def get_language_info(language: str) -> Optional[LanguageInfo]:
    """Get language information for a given language name."""
    return LANGUAGES.get(language)


def get_supported_languages() -> List[str]:
    """Get list of all supported language names."""
    return list(LANGUAGES.keys())


def get_supported_extensions() -> Set[str]:
    """Get set of all supported file extensions."""
    extensions = set()
    for lang_info in LANGUAGES.values():
        extensions.update(lang_info.extensions)
    return extensions


def is_source_file(file_path: str) -> bool:
    """Check if a file is a recognized source code file."""
    ext = Path(file_path).suffix.lower()
    return ext in get_supported_extensions() or file_path.endswith(".C")
