from core.config_discovery import ConfigDiscovery


class TestConfigDiscovery:
    def test_finds_config_in_start_directory(self, tmp_path):
        (tmp_path / "treesnake.json").write_text("{}", encoding="utf-8")

        result = ConfigDiscovery().find(str(tmp_path))

        assert result == str(tmp_path / "treesnake.json")

    def test_finds_config_walking_up_parent_directories(self, tmp_path):
        (tmp_path / "treesnake.json").write_text("{}", encoding="utf-8")
        nested = tmp_path / "src" / "core"
        nested.mkdir(parents=True)

        result = ConfigDiscovery().find(str(nested))

        assert result == str(tmp_path / "treesnake.json")

    def test_returns_none_when_nothing_found(self, tmp_path):
        nested = tmp_path / "src"
        nested.mkdir()

        result = ConfigDiscovery().find(str(nested))

        assert result is None

    def test_respects_priority_order(self, tmp_path):
        (tmp_path / "treesnake.toml").write_text("", encoding="utf-8")
        (tmp_path / "treesnake.json").write_text("{}", encoding="utf-8")

        result = ConfigDiscovery().find(str(tmp_path))

        assert result == str(tmp_path / "treesnake.json")

    def test_falls_back_to_treesnakeignore_when_nothing_else_present(self, tmp_path):
        (tmp_path / ".treesnakeignore").write_text("*.pyc\n", encoding="utf-8")

        result = ConfigDiscovery().find(str(tmp_path))

        assert result == str(tmp_path / ".treesnakeignore")

    def test_closer_config_wins_over_one_higher_up(self, tmp_path):
        (tmp_path / "treesnake.json").write_text('{"config": {"exclude_dirs": ["outer"]}}', encoding="utf-8")
        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "treesnake.json").write_text('{"config": {"exclude_dirs": ["inner"]}}', encoding="utf-8")

        result = ConfigDiscovery().find(str(nested))

        assert result == str(nested / "treesnake.json")

    def test_accepts_a_file_path_as_starting_point(self, tmp_path):
        (tmp_path / "treesnake.json").write_text("{}", encoding="utf-8")
        some_file = tmp_path / "src" / "main.py"
        some_file.parent.mkdir(parents=True)
        some_file.write_text("", encoding="utf-8")

        result = ConfigDiscovery().find(str(some_file))

        assert result == str(tmp_path / "treesnake.json")