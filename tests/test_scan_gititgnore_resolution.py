import json

import pytest
from typer.testing import CliRunner

from cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _disable_update_check(monkeypatch):
    # `scan` kicks off a real background update-check network call on every
    # invocation (see core/update_checker.py); neutralize it here so these
    # CLI tests are fast and deterministic regardless of the environment's
    # actual network access, instead of relying on the silent-failure path.
    monkeypatch.setattr("core.update_checker.UpdateChecker.check", lambda self: None)


def _subdir_names(output: str) -> set[str]:
    data = json.loads(output)
    return {s["name"] for s in data["subdirectories"]}


class TestScanUseGitignoreResolution:
    def _make_project(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print(1)", encoding="utf-8")
        (tmp_path / "secret_stuff").mkdir()
        (tmp_path / "secret_stuff" / "data.txt").write_text("x", encoding="utf-8")
        (tmp_path / ".gitignore").write_text("secret_stuff/\n", encoding="utf-8")

    def test_default_applies_gitignore(self, tmp_path):
        self._make_project(tmp_path)

        result = runner.invoke(
            app, ["scan", str(tmp_path), "--fmt", "json", "--output", "stdout"]
        )

        assert result.exit_code == 0
        assert _subdir_names(result.stdout) == {"src"}

    def test_no_gitignore_flag_keeps_secret_stuff(self, tmp_path):
        self._make_project(tmp_path)

        result = runner.invoke(
            app,
            ["scan", str(tmp_path), "--no-gitignore", "--fmt", "json", "--output", "stdout"],
        )

        assert result.exit_code == 0
        assert _subdir_names(result.stdout) == {"src", "secret_stuff"}

    def test_config_use_gitignore_false_is_respected_without_cli_flag(self, tmp_path):
        self._make_project(tmp_path)
        (tmp_path / "treesnake.json").write_text(
            json.dumps({"config": {}, "use_gitignore": False}), encoding="utf-8"
        )

        result = runner.invoke(
            app,
            [
                "scan",
                str(tmp_path),
                "-c",
                str(tmp_path / "treesnake.json"),
                "--fmt",
                "json",
                "--output",
                "stdout",
            ],
        )

        assert result.exit_code == 0
        assert _subdir_names(result.stdout) == {"src", "secret_stuff"}

    def test_cli_flag_overrides_config_use_gitignore_false(self, tmp_path):
        self._make_project(tmp_path)
        (tmp_path / "treesnake.json").write_text(
            json.dumps({"config": {}, "use_gitignore": False}), encoding="utf-8"
        )

        result = runner.invoke(
            app,
            [
                "scan",
                str(tmp_path),
                "-c",
                str(tmp_path / "treesnake.json"),
                "--gitignore",
                "--fmt",
                "json",
                "--output",
                "stdout",
            ],
        )

        assert result.exit_code == 0
        assert _subdir_names(result.stdout) == {"src"}

    def test_cli_flag_overrides_config_use_gitignore_true(self, tmp_path):
        self._make_project(tmp_path)
        (tmp_path / "treesnake.json").write_text(
            json.dumps({"config": {}, "use_gitignore": True}), encoding="utf-8"
        )

        result = runner.invoke(
            app,
            [
                "scan",
                str(tmp_path),
                "-c",
                str(tmp_path / "treesnake.json"),
                "--no-gitignore",
                "--fmt",
                "json",
                "--output",
                "stdout",
            ],
        )

        assert result.exit_code == 0
        assert _subdir_names(result.stdout) == {"src", "secret_stuff"}