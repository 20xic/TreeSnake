from typer.testing import CliRunner

from cli.app import app
from core.config_reader import ConfigReader

runner = CliRunner()


class TestInitGitignoreFlag:
    def test_default_writes_use_gitignore_true(self, tmp_path):
        result = runner.invoke(app, ["init", str(tmp_path), "--fmt", "json"])

        assert result.exit_code == 0
        template = ConfigReader().read(str(tmp_path / "treesnake.json"))
        assert template.use_gitignore is True

    def test_no_gitignore_flag_writes_false(self, tmp_path):
        result = runner.invoke(
            app, ["init", str(tmp_path), "--fmt", "json", "--no-gitignore"]
        )

        assert result.exit_code == 0
        template = ConfigReader().read(str(tmp_path / "treesnake.json"))
        assert template.use_gitignore is False

    def test_explicit_gitignore_flag_writes_true(self, tmp_path):
        result = runner.invoke(
            app, ["init", str(tmp_path), "--fmt", "json", "--gitignore"]
        )

        assert result.exit_code == 0
        template = ConfigReader().read(str(tmp_path / "treesnake.json"))
        assert template.use_gitignore is True

    def test_flag_round_trips_through_every_format(self, tmp_path):
        cases = [
            ("env", ".env.treesnake"),
            ("yaml", "treesnake.yml"),
            ("toml", "treesnake.toml"),
        ]
        for fmt, filename in cases:
            result = runner.invoke(
                app, ["init", str(tmp_path), "--fmt", fmt, "--no-gitignore"]
            )
            assert result.exit_code == 0

            template = ConfigReader().read(str(tmp_path / filename))
            assert template.use_gitignore is False, f"failed for fmt={fmt}"