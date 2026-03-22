import platform
import subprocess
from abc import ABC, abstractmethod


class IClipboard(ABC):
    @abstractmethod
    def copy(self, text: str) -> None:
        raise NotImplementedError


class WindowsClipboard(IClipboard):
    def copy(self, text: str) -> None:
        try:
            import ctypes
            import ctypes.wintypes

            CF_UNICODETEXT = 13
            GMEM_MOVEABLE = 0x0002

            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32

            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalAlloc.argtypes = [ctypes.wintypes.UINT, ctypes.c_size_t]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.restype = ctypes.wintypes.BOOL
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalFree.restype = ctypes.c_void_p
            kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
            user32.OpenClipboard.restype = ctypes.wintypes.BOOL
            user32.OpenClipboard.argtypes = [ctypes.wintypes.HWND]
            user32.EmptyClipboard.restype = ctypes.wintypes.BOOL
            user32.SetClipboardData.restype = ctypes.c_void_p
            user32.SetClipboardData.argtypes = [ctypes.wintypes.UINT, ctypes.c_void_p]
            user32.CloseClipboard.restype = ctypes.wintypes.BOOL

            encoded = text.encode("utf-16-le") + b"\x00\x00"
            size = len(encoded)

            h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            if not h_mem:
                raise RuntimeError("Failed to allocate clipboard memory")

            p_mem = kernel32.GlobalLock(h_mem)
            if not p_mem:
                kernel32.GlobalFree(h_mem)
                raise RuntimeError("Failed to lock clipboard memory")

            ctypes.memmove(p_mem, encoded, size)
            kernel32.GlobalUnlock(h_mem)

            if not user32.OpenClipboard(None):
                kernel32.GlobalFree(h_mem)
                raise RuntimeError("Failed to open clipboard")

            try:
                user32.EmptyClipboard()
                if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                    raise RuntimeError("Failed to set clipboard data")
            finally:
                user32.CloseClipboard()

        except (AttributeError, OSError) as e:
            raise RuntimeError(f"Windows clipboard error: {e}") from e


class MacOSClipboard(IClipboard):
    def copy(self, text: str) -> None:
        try:
            subprocess.run(
                "pbcopy",
                input=text.encode("utf-8"),
                check=True,
            )
        except FileNotFoundError as e:
            raise RuntimeError("pbcopy not found") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"pbcopy failed with code {e.returncode}") from e


class LinuxClipboard(IClipboard):
    def copy(self, text: str) -> None:
        encoded = text.encode("utf-8")
        errors: list[str] = []

        for cmd in (
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ):
            try:
                subprocess.run(cmd, input=encoded, check=True)
                return
            except FileNotFoundError:
                errors.append(f"{cmd[0]!r} not found")
            except subprocess.CalledProcessError as e:
                errors.append(f"{cmd[0]!r} failed with code {e.returncode}")

        raise RuntimeError(
            "Linux clipboard unavailable. Install xclip or xsel:\n"
            "  sudo apt install xclip\n"
            "  sudo dnf install xclip\n"
            f"Details: {'; '.join(errors)}"
        )


class Clipboard(IClipboard):
    _implementations: dict[str, type[IClipboard]] = {
        "windows": WindowsClipboard,
        "darwin": MacOSClipboard,
        "linux": LinuxClipboard,
    }

    def __init__(self):
        self._impl = self._resolve()

    def _resolve(self) -> IClipboard:
        system = platform.system().lower()
        impl_class = self._implementations.get(system)

        if impl_class is None:
            raise RuntimeError(
                f"Unsupported platform: {platform.system()!r}. "
                f"Supported: {list(self._implementations)}"
            )

        return impl_class()

    def copy(self, text: str) -> None:
        self._impl.copy(text)
