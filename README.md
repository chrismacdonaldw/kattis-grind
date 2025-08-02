# Kattis Grind

A modern CLI tool for competitive programming on [Kattis](https://open.kattis.com). This tool helps streamline your competitive programming workflow by automating problem fetching, solution testing, and submission processes.

## Features

- **Fetch Problems**: Download problem statements and sample test cases
- **Submit Solutions**: Submit your code directly from the command line with real-time feedback
- **Random Problem Discovery**: Find random problems within specified difficulty ranges
- **Multi-language Support**: Supports C++, Python, Java, C#, Go, Rust, and many more
- **Template System**: Automatic boilerplate code generation for your preferred languages
- **Problem Hints**: Optional integration with Steve Halim's cpbook.net for problem type hints and solving strategies

## Installation

### Option 1: Install directly from GitHub

```bash
pip install git+https://github.com/chrismacdonaldw/kattis-grind.git
```

This installs the `kattis-grind` command globally, allowing you to use it from anywhere.

### Option 2: Local development setup

1. Clone the repository:
```bash
git clone https://github.com/chrismacdonaldw/kattis-grind.git
cd kattis-grind
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### If installed via pip (Option 1):

1. **Initialize Configuration**:
```bash
kattis-grind config init
```

2. **Edit your configuration** with your Kattis credentials:
   - Download your `.kattisrc` file from [Kattis](https://open.kattis.com/download/kattisrc)
   - Place it in your home directory or edit the generated one

3. **Fetch a problem**:
```bash
kattis-grind fetch hello
```

4. **Submit a solution**:
```bash
kattis-grind submit solution.py
```

### If running locally (Option 2):

1. **Initialize Configuration**:
```bash
python main.py config init
```

2. **Edit your configuration** with your Kattis credentials:
   - Download your `.kattisrc` file from [Kattis](https://open.kattis.com/download/kattisrc)
   - Place it in your home directory or edit the generated one

3. **Fetch a problem**:
```bash
python main.py fetch hello
```

4. **Submit a solution**:
```bash
python main.py submit solution.py
```

## Commands

*Note: Replace `kattis-grind` with `python main.py` if running locally instead of installing via pip.*

### `fetch <problem_id>`
Downloads a problem and sets up a directory with:
- Problem description (HTML file)
- Sample input/output files
- Boilerplate code templates for configured languages

```bash
kattis-grind fetch hello
kattis-grind fetch twostones
```

### `submit <files...>`
Submits your solution to Kattis with real-time feedback.

```bash
# Submit a single file
kattis-grind submit solution.py

# Submit multiple files
kattis-grind submit main.cpp helper.h

# Specify problem and language explicitly
kattis-grind submit solution.java --problem hello --language Java
```

**Options:**
- `--problem, -p`: Specify the problem ID (auto-detected from filename if not provided)
- `--language, -l`: Specify the programming language (auto-detected from extension if not provided)
- `--mainclass, -m`: Specify the main class name (for languages that require it)
- `--force, -f`: Skip confirmation prompt

### `rand`
Finds a random problem within your configured difficulty range.

```bash
# Find a random problem
kattis-grind rand

# Specify difficulty range
kattis-grind rand --min 1.5 --max 2.0

# Fetch immediately
kattis-grind rand --fetch

# Output only the problem ID
kattis-grind rand --id-only
```

**Options:**
- `--min`: Minimum difficulty (uses config default if not specified)
- `--max`: Maximum difficulty (uses config default if not specified)
- `--fetch, -f`: Automatically fetch the problem
- `--id-only, -i`: Output only the problem ID (useful for scripting)

### `config init`
Creates a default configuration file in your home directory.

```bash
kattis-grind config init
```

## Configuration

The tool uses a `.kattisrc` configuration file, which should be placed in your home directory. You should use the `templates/default_kattisrc` which can be generated with the `config init` command shown above.

### Configuration File Structure

```ini
[user]
# Found at https://<hostname>/downloads/kattisrc
username = YOUR_USERNAME_HERE
token = YOUR_TOKEN_HERE

[kattis]
hostname = open.kattis.com
loginurl = https://open.kattis.com/login
submissionurl = https://open.kattis.com/submit

[settings]
# Preferred programming languages (comma-separated)
languages = python,cpp
# Difficulty range for random problem selection (min-max)
difficulty = 1.5-3.0
# Directory where problems will be saved (supports ~ for home directory)
problems_directory = kattis_problems
# Whether to fetch hints from Steve Halim's cpbook.net site
include_hints = false

[templates]
# Template Examples:
# cpp = ~/.kattis-grind/templates/cpp_template.cpp
# py = ~/.kattis-grind/templates/py_template.py
```

### Configuration Options

#### Custom Problems Directory
You can configure where problems are saved using the `problems_directory` setting:

```ini
[settings]
problems_directory = kattis_problems

# Or using ~ as a root:
problems_directory = ~/competitive_programming/kattis
```

#### Problem Hints
Enable hints from Steve Halim's [cpbook.net](https://cpbook.net) to get problem type information and solving strategies:

```ini
[settings]
include_hints = true
```

When enabled, the tool will display hints like:
- **Problem Type**: Classification (e.g., "1.4a, One-Liner I/O")
- **Hint Text**: Solving strategy (e.g., "just print 'Hello World!'")

This feature helps you:
- Understand what type of problem you're solving
- Get hints about the approach or algorithm needed
- Learn problem classification for competitive programming

### Environment Variables

- `KATTIS_GRIND_HOME`: Override the default configuration directory

## Project Structure

After fetching problems, your directory structure will look like:

```
kattis_problems/
├── hello/
│   ├── hello.html          # Problem description
│   ├── sample-1.in         # Sample input
│   ├── sample-1.ans        # Expected output
│   ├── hello.py            # Python template
│   └── hello.cpp           # C++ template
└── twostones/
    ├── twostones.html
    ├── sample-1.in
    ├── sample-1.ans
    ├── twostones.py
    └── twostones.cpp
```

## Acknowledgments

This project uses the [official Kattis CLI](https://github.com/Kattis/kattis-cli) as a starting point. The original Kattis CLI provided the foundation for understanding the Kattis API and submission process.
