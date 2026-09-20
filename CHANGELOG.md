# Changelog

All notable changes to this project will be documented in this file.
Entries are generated from [Conventional Commits](https://www.conventionalcommits.org/) by `cz bump`.

## v0.5.2 (2026-09-20)

### Perf

- **scanner**: read file contents in a thread pool

## v0.5.1 (2026-09-20)

### Perf

- **formatter**: stream output instead of building the whole string in memory

## v0.5.0 (2026-09-20)

### Feat

- **scanner**: sort directory entries by name for deterministic output

### Refactor

- **models**: plain dataclasses for File/Directory, move rule compilation to core

## v0.4.3 (2026-09-20)

### Perf

- **scanner**: walk with os.scandir, stat once per file, sniff binaries early

## v0.4.2 (2026-09-20)

### Fix

- **cli**: force UTF-8 stdout/stderr so redirected output does not crash on Windows

## v0.4.1 (2026-09-20)

### Added
- `xml` output format (`--fmt xml` / `mode = "xml"`): nested
  `<project>`/`<directory>`/`<file>` tree with full `path` on every file
  and content kept verbatim in CDATA — makes the project hierarchy
  explicit for LLM consumption

## v0.4 (2026-06-19)

### Feat
- **config**: add `use_gitignore` setting to config templates

## v0.3.1 (2026-06-18)

### Fix
- **update-checker**: explicitly bound the wait for the background check
  instead of `join(timeout=0)`

## v0.3 (2026-06-18)

### Feat
- **scan**: add `--max-depth`, `--max-file-size`, `--include-dir`/`--include-file`
  and background update check

### Refactor
- clean up scan command and template model
- inline `ScanContext` into `ScanConfig`, fix `ConfigReader` routing
- separate serialization, fix version source, harden scan errors, fix typo

## v0.2.2 (2026-06-14)

### Added
- `scan` command now prints scan stats to stderr after every scan:
  file count, dir count, and total elapsed time
- `--stat` flag for `scan` command: shows detailed timing breakdown
  of scan, format, and write stages

### Performance
- `LLMFormatter` and `DefaultFormatter`: replaced string accumulation
  with `io.StringIO` buffer, reducing format time ~100x on large trees
  (46000ms → 276ms on 6688 files)

## v0.2.1.2 (2026-06-14)

### Fixed
- `LLMFormatter`: directories listed in `exclude_content_dirs` now appear
  in output without their contents (previously produced empty string and
  disappeared)
- `template_creator`: typo `exclude_contend_dirs` → `exclude_content_dirs`
  in default template (pydantic silently ignored the unknown field)
- `test_template_creator`: same typo fixed in template fixture

### Added
- `init` command now creates or updates `.gitignore` with treesnake-related
  entries (`treesnake`, `treesnake.exe`, `treesnake.json`, etc.)
- New `GitignoreManager` in `core`: appends only missing entries under a
  `# treesnake` section, preserves all existing content

### Changed
- Default exclude list extended with treesnake config filenames:
  `treesnake.json`, `treesnake.toml`, `treesnake.env`,
  `treesnake.yaml`, `treesnake.yml`, `treesnake.exe`

## v0.2.1.1 (2026-06-14)

- Initial patch release
