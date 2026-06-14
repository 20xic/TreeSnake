# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1.2] - 2025-06-14

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

## [0.2.1.1] - ...

- Initial patch release