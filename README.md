<div align="center">

```
                                  -
                                 :@:   .
                                 -@..=**:
              -+*****+=:         +@%%+.
            =%@%+%@@@@@@%:      .%@#.
          :@@@@@#@@@##@@@@.    :@@+
           -+++++-:.  +@@@=   =@@=
                    .+@@@@:  =@@:    :
                 .=#@@@@#.  =@@: :+##+
               -#@@@@%+:   =@@*=%%*:
              *@@@%=.     +@@@@#-
             +@@@*       .@@@@+-***+-.
             *@@@-     ..+@@@+=@@@@@@@#.
             :@@@@#+==##-@@@# :...:+@@@@.
              .*@@@@@@@:*@@@-       *@@@-
                 :=+++=.@@@#       :%@@@:
              .:::...  :###+    .-*@@@@=
           :*%@@@@@@@@@%##****#%@@@@@#.
          +@@@@#++++*#%@@@@@@@@@@%#=.
         =@@@*.       +++=-----:.
         +@@@.       *@@@-
         .%@@@*=-== =@@@*
           =#@@@%*:+@@@@.=*-.  .:
              ...-%@@@@@:.%@@@@@*
                :==----=- .-===:
   _                                  _
  | |_ _ __ ___  ___ ___ _ __   __ _| | _____
  | __| '__/ _ \/ _ \/ __| '_ \ / _` | |/ / _ \
  | |_| | |  __/  __/\__ \ | | | (_| |   <  __/
   \__|_|  \___|\___||___/_| |_|\__,_|_|\_\___|
```

**Scan your directory tree. Feed it to an LLM. Ship faster.**

</div>

---

treesnake scans a directory tree and exports its structure and file contents in formats optimized for humans, LLMs, or machines. Use it to instantly copy your entire codebase into a prompt, save it to a file, or pipe it wherever you need.

## Features

- **Three output formats** — human-readable tree, LLM-optimized text, or JSON
- **Three output destinations** — stdout, file, or clipboard
- **Flexible filtering** — exclude dirs, files, or just their content via patterns, globs, or regex
- **Config file support** — store your settings in `.env`, `.yml`, `.toml`, or `.json`
- **Cross-platform** — Windows, macOS, Linux
- **Single binary** — ships as a standalone `.exe` / binary, no Python required

## Installation

### Download binary (recommended)

Grab the latest binary for your platform from [Releases](https://github.com/yourname/treesnake/releases):

| Platform | File |
|----------|------|
| Windows  | `treesnake.exe` |
| macOS    | `treesnake-macos` |
| Linux    | `treesnake-linux` |

### From source

```bash
git clone https://github.com/yourname/treesnake
cd treesnake
pip install -e .
```

## Quick start

```bash
# Scan current directory and print to console
treesnake scan .

# Copy your codebase to clipboard for an LLM prompt
treesnake scan . --fmt llm --output clipboard

# Save to file
treesnake scan . --fmt llm --output file --out-file context.txt
```

## Commands

### `scan`

Scan a directory and output its structure.

```
treesnake scan [PATH] [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--config PATH` | `-c` | Path to a config file. Overrides inline options. |
| `--fmt` | `-f` | Output format: `default`, `llm`, `json` |
| `--output` | `-o` | Destination: `stdout`, `file`, `clipboard` |
| `--out-file PATH` | | Output file path (required when `--output=file`) |
| `--exclude-dir` | `-ed` | Exclude a directory entirely. Repeatable. |
| `--exclude-file` | `-ef` | Exclude a file entirely. Repeatable. |
| `--no-content-dir` | `-ncd` | Include directory name but not its contents. Repeatable. |
| `--no-content-file` | `-ncf` | Include file name but not its contents. Repeatable. |

**Output formats:**

- `default` — indented tree with file sizes, human-readable
- `llm` — token-efficient format with file paths as headers, ideal for LLM context
- `json` — structured JSON, useful for piping into other tools

**Filtering patterns:**

Patterns support exact names, globs, and regex:

```bash
# Exact match
--exclude-dir .git

# Glob
--exclude-file "*.pyc"

# Regex (prefix with re: or regex:)
--exclude-file "re:^\\..*"   # all hidden files
```

Multiple values can be passed in a single option using spaces:

```bash
--exclude-file "*.pyc *.exe .env"
--exclude-dir ".git venv __pycache__"
```

**Examples:**

```bash
# Minimal scan with inline filters
treesnake scan . \
  --exclude-dir ".git venv __pycache__" \
  --exclude-file "*.pyc .env poetry.lock" \
  --fmt llm \
  --output clipboard

# Scan a specific path, save to file
treesnake scan ./src \
  --fmt llm \
  --output file \
  --out-file context.txt

# Use a config file, override format from CLI
treesnake scan . --config treesnake.toml --fmt json
```

---

### `init`

Create a default config file in the given directory.

```
treesnake init [PATH] [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--fmt` | `-f` | Config format: `env`, `json`, `yaml`, `toml` (default: `env`) |

```bash
treesnake init .                  # creates .env.treesnake
treesnake init . --fmt toml       # creates treesnake.toml
treesnake init ./myproject --fmt yaml
```

---

### `version`

Print the current version.

```bash
treesnake version
# treesnake 1.0.0
```

---

### `art`

Print the treesnake ASCII art.

```bash
treesnake art
```

## Config file

Run `treesnake init . --fmt toml` to generate a config file, then edit it:

```toml
mode = "--llm"
output = "--file"
out_file = "context.txt"

[config]
exclude_dirs = [".git", "venv", "__pycache__", "dist", "build"]
exclude_files = [".env", "*.pyc", "poetry.lock", "*.exe"]
exclude_content_dirs = []
exclude_content_files = ["*.log", "*.lock"]
```

All fields in the config can be overridden from the CLI — CLI options always take precedence.

Supported formats: `.env`, `.yml`, `.yaml`, `.toml`, `.json`.

## Patterns reference

| Pattern | Example | Matches |
|---------|---------|---------|
| Exact | `.git` | Only `.git` |
| Glob | `*.pyc` | Any `.pyc` file |
| Regex | `re:^\\..*` | Any hidden file/dir |

## Building from source

Requires Python 3.11+ and PyInstaller:

```bash
pip install -e ".[dev]"
python build.py
```

Output binary will be at `dist/treesnake` (or `dist/treesnake.exe` on Windows).

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run from source
python src/main.py scan .
```

## License

MIT