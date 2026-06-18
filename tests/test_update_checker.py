import json
import time
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from core.update_checker import UpdateChecker


@pytest.fixture
def cache_path(tmp_path):
    return tmp_path / "update_check.json"


class TestUpdateChecker:
    def test_no_update_when_versions_match(self, cache_path):
        checker = UpdateChecker("1.0.0", cache_path=cache_path)
        checker.latest_version = "1.0.0"

        assert checker.has_update() is False

    def test_has_update_when_latest_is_greater(self, cache_path):
        checker = UpdateChecker("1.0.0", cache_path=cache_path)
        checker.latest_version = "1.1.0"

        assert checker.has_update() is True

    def test_no_update_when_latest_is_older(self, cache_path):
        checker = UpdateChecker("1.0.0", cache_path=cache_path)
        checker.latest_version = "0.9.0"

        assert checker.has_update() is False

    def test_no_update_when_local_version_is_ahead_of_latest_release(self, cache_path):
        # Регрессия: локальная dev-версия новее последнего опубликованного релиза
        # (например, "0.3" в разработке, а на GitHub ещё "0.2.2").
        checker = UpdateChecker("0.3", cache_path=cache_path)
        checker.latest_version = "0.2.2"

        assert checker.has_update() is False

    def test_no_update_when_versions_differ_only_in_length(self, cache_path):
        checker = UpdateChecker("0.2.2.1", cache_path=cache_path)
        checker.latest_version = "0.2.2"

        assert checker.has_update() is False

    def test_has_update_when_patch_segment_is_greater(self, cache_path):
        checker = UpdateChecker("0.2.2", cache_path=cache_path)
        checker.latest_version = "0.2.10"

        assert checker.has_update() is True

    def test_no_update_before_check(self, cache_path):
        checker = UpdateChecker("1.0.0", cache_path=cache_path)

        assert checker.has_update() is False

    def test_check_fetches_and_caches(self, cache_path):
        checker = UpdateChecker("1.0.0", cache_path=cache_path)
        fake_response = MagicMock()
        fake_response.__enter__.return_value = fake_response
        fake_response.read.return_value = json.dumps(
            {"tag_name": "v1.1.0", "html_url": "https://example.com/releases/v1.1.0"}
        ).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=fake_response):
            checker.check()

        assert checker.latest_version == "1.1.0"
        assert checker.release_url == "https://example.com/releases/v1.1.0"
        assert cache_path.exists()

    def test_check_uses_fresh_cache_without_network_call(self, cache_path):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "checked_at": time.time(),
                    "latest_version": "2.0.0",
                    "release_url": "https://example.com/releases/v2.0.0",
                }
            ),
            encoding="utf-8",
        )
        checker = UpdateChecker("1.0.0", cache_path=cache_path)

        with patch("urllib.request.urlopen") as mock_urlopen:
            checker.check()
            mock_urlopen.assert_not_called()

        assert checker.latest_version == "2.0.0"

    def test_check_refetches_when_cache_expired(self, cache_path):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "checked_at": time.time() - 100_000,
                    "latest_version": "2.0.0",
                    "release_url": "https://example.com/releases/v2.0.0",
                }
            ),
            encoding="utf-8",
        )
        checker = UpdateChecker("1.0.0", cache_path=cache_path)
        fake_response = MagicMock()
        fake_response.__enter__.return_value = fake_response
        fake_response.read.return_value = json.dumps(
            {"tag_name": "v3.0.0", "html_url": "https://example.com/releases/v3.0.0"}
        ).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=fake_response):
            checker.check()

        assert checker.latest_version == "3.0.0"

    def test_check_silently_fails_on_network_error(self, cache_path):
        checker = UpdateChecker("1.0.0", cache_path=cache_path)

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            checker.check()  # should not raise

        assert checker.latest_version is None
        assert checker.has_update() is False

    def test_check_silently_fails_on_malformed_cache(self, cache_path):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("not json", encoding="utf-8")
        checker = UpdateChecker("1.0.0", cache_path=cache_path)
        fake_response = MagicMock()
        fake_response.__enter__.return_value = fake_response
        fake_response.read.return_value = json.dumps(
            {"tag_name": "v1.2.0", "html_url": "https://example.com"}
        ).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=fake_response):
            checker.check()

        assert checker.latest_version == "1.2.0"