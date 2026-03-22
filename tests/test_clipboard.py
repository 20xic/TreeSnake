from unittest.mock import MagicMock, call, patch

import pytest

from core.clipboard import (
    Clipboard,
    LinuxClipboard,
    MacOSClipboard,
    WindowsClipboard,
)


class TestWindowsClipboard:
    @pytest.fixture
    def win_mocks(self):
        mock_kernel32 = MagicMock()
        mock_user32 = MagicMock()

        mock_kernel32.GlobalAlloc.return_value = 0x1000
        mock_kernel32.GlobalLock.return_value = 0x2000
        mock_user32.OpenClipboard.return_value = True
        mock_user32.SetClipboardData.return_value = 0x1000

        with (
            patch("ctypes.windll") as mock_windll,
            patch("ctypes.memmove") as mock_memmove,
        ):
            mock_windll.kernel32 = mock_kernel32
            mock_windll.user32 = mock_user32
            yield mock_kernel32, mock_user32, mock_memmove

    def test_copy_calls_open_clipboard(self, win_mocks):
        _, user32, _ = win_mocks
        WindowsClipboard().copy("hello")
        user32.OpenClipboard.assert_called_once_with(None)

    def test_copy_calls_empty_clipboard(self, win_mocks):
        _, user32, _ = win_mocks
        WindowsClipboard().copy("hello")
        user32.EmptyClipboard.assert_called_once()

    def test_copy_calls_set_clipboard_data(self, win_mocks):
        _, user32, _ = win_mocks
        WindowsClipboard().copy("hello")
        CF_UNICODETEXT = 13
        user32.SetClipboardData.assert_called_once_with(CF_UNICODETEXT, 0x1000)

    def test_copy_calls_close_clipboard(self, win_mocks):
        _, user32, _ = win_mocks
        WindowsClipboard().copy("hello")
        user32.CloseClipboard.assert_called_once()

    def test_copy_encodes_utf16(self, win_mocks):
        kernel32, _, _ = win_mocks
        text = "hello"
        WindowsClipboard().copy(text)

        expected_encoded = text.encode("utf-16-le") + b"\x00\x00"
        alloc_call_size = kernel32.GlobalAlloc.call_args[0][1]
        assert alloc_call_size == len(expected_encoded)

    def test_copy_writes_encoded_bytes_to_memory(self, win_mocks):
        _, _, mock_memmove = win_mocks
        text = "hello"
        WindowsClipboard().copy(text)

        expected_encoded = text.encode("utf-16-le") + b"\x00\x00"
        mock_memmove.assert_called_once_with(
            0x2000, expected_encoded, len(expected_encoded)
        )

    def test_copy_unicode_text(self, win_mocks):
        kernel32, _, _ = win_mocks
        text = "Привет мир"
        WindowsClipboard().copy(text)

        expected_size = len(text.encode("utf-16-le") + b"\x00\x00")
        assert kernel32.GlobalAlloc.call_args[0][1] == expected_size

    def test_close_clipboard_called_on_set_data_failure(self, win_mocks):
        _, user32, _ = win_mocks
        user32.SetClipboardData.return_value = 0

        with pytest.raises(RuntimeError, match="Failed to set clipboard data"):
            WindowsClipboard().copy("hello")

        user32.CloseClipboard.assert_called_once()

    def test_raises_on_alloc_failure(self, win_mocks):
        kernel32, _, _ = win_mocks
        kernel32.GlobalAlloc.return_value = 0

        with pytest.raises(RuntimeError, match="Failed to allocate clipboard memory"):
            WindowsClipboard().copy("hello")

    def test_raises_on_lock_failure(self, win_mocks):
        kernel32, _, _ = win_mocks
        kernel32.GlobalLock.return_value = None

        with pytest.raises(RuntimeError, match="Failed to lock clipboard memory"):
            WindowsClipboard().copy("hello")

    def test_raises_on_open_clipboard_failure(self, win_mocks):
        _, user32, _ = win_mocks
        user32.OpenClipboard.return_value = 0

        with pytest.raises(RuntimeError, match="Failed to open clipboard"):
            WindowsClipboard().copy("hello")

    def test_frees_memory_on_lock_failure(self, win_mocks):
        kernel32, _, _ = win_mocks
        kernel32.GlobalLock.return_value = None

        with pytest.raises(RuntimeError):
            WindowsClipboard().copy("hello")

        kernel32.GlobalFree.assert_called_once_with(0x1000)

    def test_frees_memory_on_open_clipboard_failure(self, win_mocks):
        kernel32, user32, _ = win_mocks
        user32.OpenClipboard.return_value = 0

        with pytest.raises(RuntimeError):
            WindowsClipboard().copy("hello")

        kernel32.GlobalFree.assert_called_once_with(0x1000)


class TestMacOSClipboard:
    def test_copy_calls_pbcopy(self):
        with patch("subprocess.run") as mock_run:
            MacOSClipboard().copy("hello")
            mock_run.assert_called_once_with(
                "pbcopy",
                input=b"hello",
                check=True,
            )

    def test_copy_encodes_utf8(self):
        text = "Привет мир"
        with patch("subprocess.run") as mock_run:
            MacOSClipboard().copy(text)
            mock_run.assert_called_once_with(
                "pbcopy",
                input=text.encode("utf-8"),
                check=True,
            )

    def test_raises_when_pbcopy_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="pbcopy not found"):
                MacOSClipboard().copy("hello")

    def test_raises_on_pbcopy_failure(self):
        import subprocess

        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "pbcopy")
        ):
            with pytest.raises(RuntimeError, match="pbcopy failed"):
                MacOSClipboard().copy("hello")


class TestLinuxClipboard:
    def test_copy_uses_xclip_when_available(self):
        with patch("subprocess.run") as mock_run:
            LinuxClipboard().copy("hello")
            mock_run.assert_called_once_with(
                ["xclip", "-selection", "clipboard"],
                input=b"hello",
                check=True,
            )

    def test_copy_falls_back_to_xsel_when_xclip_not_found(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [FileNotFoundError, None]
            LinuxClipboard().copy("hello")
            assert mock_run.call_count == 2
            assert mock_run.call_args_list[1] == call(
                ["xsel", "--clipboard", "--input"],
                input=b"hello",
                check=True,
            )

    def test_raises_when_both_xclip_and_xsel_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="xclip or xsel"):
                LinuxClipboard().copy("hello")

    def test_raises_on_xclip_failure_and_xsel_not_found(self):
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "xclip"),
                FileNotFoundError,
            ]
            with pytest.raises(RuntimeError, match="xclip or xsel"):
                LinuxClipboard().copy("hello")

    def test_copy_encodes_utf8(self):
        text = "Привет мир"
        with patch("subprocess.run") as mock_run:
            LinuxClipboard().copy(text)
            mock_run.assert_called_once_with(
                ["xclip", "-selection", "clipboard"],
                input=text.encode("utf-8"),
                check=True,
            )


class TestClipboard:
    def test_resolves_windows(self):
        with patch("platform.system", return_value="Windows"):
            cb = Clipboard()
        assert isinstance(cb._impl, WindowsClipboard)

    def test_resolves_macos(self):
        with patch("platform.system", return_value="Darwin"):
            cb = Clipboard()
        assert isinstance(cb._impl, MacOSClipboard)

    def test_resolves_linux(self):
        with patch("platform.system", return_value="Linux"):
            cb = Clipboard()
        assert isinstance(cb._impl, LinuxClipboard)

    def test_raises_on_unsupported_platform(self):
        with patch("platform.system", return_value="FreeBSD"):
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                Clipboard()

    def test_copy_delegates_to_impl(self):
        with patch("platform.system", return_value="Windows"):
            cb = Clipboard()

        cb._impl = MagicMock()
        cb.copy("test")
        cb._impl.copy.assert_called_once_with("test")
