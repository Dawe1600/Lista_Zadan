import sys
from typing import Protocol


class SettingsBackend(Protocol):
    """Seam for application preferences and OS autostart integration."""

    def is_ai_enabled(self) -> bool: ...

    def get_gemini_api_key(self) -> str | None: ...

    def is_autostart_enabled(self) -> bool: ...

    def set_autostart(self, enabled: bool) -> None: ...


class WindowsQSettingsBackend:
    """Production adapter backed by QSettings and the Windows Run registry key."""

    APP_ORG = "ToDoList"
    APP_NAME = "ToDoWidgetApp"
    RUN_KEY = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    AUTOSTART_VALUE = "ListaZadan"

    def __init__(self, app_executable: str | None = None):
        self._app_executable = app_executable or sys.executable

    def _app_settings(self):
        from PyQt5.QtCore import QSettings

        return QSettings(self.APP_ORG, self.APP_NAME)

    def _run_settings(self):
        from PyQt5.QtCore import QSettings

        return QSettings(self.RUN_KEY, QSettings.NativeFormat)

    def is_ai_enabled(self) -> bool:
        return bool(self._app_settings().value("EnableAI", 0, type=int))

    def get_gemini_api_key(self) -> str | None:
        if not self.is_ai_enabled():
            return None
        api_key = self._app_settings().value("GeminiApiKey", type=str)
        if api_key and api_key.strip():
            return api_key
        return None

    def is_autostart_enabled(self) -> bool:
        return self._run_settings().contains(self.AUTOSTART_VALUE)

    def set_autostart(self, enabled: bool) -> None:
        settings = self._run_settings()
        if enabled:
            app_path = self._app_executable.replace("/", "\\")
            settings.setValue(self.AUTOSTART_VALUE, f'"{app_path}"')
        else:
            settings.remove(self.AUTOSTART_VALUE)


class InMemorySettingsBackend:
    """In-memory adapter for testing AppSettings without QSettings or Windows Registry."""

    def __init__(
        self,
        ai_enabled: bool = False,
        gemini_api_key: str | None = None,
        autostart_enabled: bool = False,
    ):
        self._ai_enabled = ai_enabled
        self._gemini_api_key = gemini_api_key
        self._autostart_enabled = autostart_enabled

    def is_ai_enabled(self) -> bool:
        return self._ai_enabled

    def get_gemini_api_key(self) -> str | None:
        if not self._ai_enabled:
            return None
        if self._gemini_api_key and self._gemini_api_key.strip():
            return self._gemini_api_key
        return None

    def is_autostart_enabled(self) -> bool:
        return self._autostart_enabled

    def set_autostart(self, enabled: bool) -> None:
        self._autostart_enabled = bool(enabled)


class AppSettings:
    """Deep module owning application preferences and OS autostart."""

    def __init__(self, backend: SettingsBackend | None = None):
        self._backend = backend or WindowsQSettingsBackend()

    def is_ai_enabled(self) -> bool:
        return self._backend.is_ai_enabled()

    def get_gemini_api_key(self) -> str | None:
        return self._backend.get_gemini_api_key()

    def is_autostart_enabled(self) -> bool:
        return self._backend.is_autostart_enabled()

    def set_autostart(self, enabled: bool) -> None:
        self._backend.set_autostart(enabled)
