import unittest

from lista_zadan.app_settings import AppSettings, InMemorySettingsBackend


class TestAppSettings(unittest.TestCase):
    def test_ai_disabled_hides_api_key(self):
        settings = AppSettings(
            InMemorySettingsBackend(ai_enabled=False, gemini_api_key="secret-key")
        )
        self.assertFalse(settings.is_ai_enabled())
        self.assertIsNone(settings.get_gemini_api_key())

    def test_ai_enabled_returns_non_empty_key(self):
        settings = AppSettings(
            InMemorySettingsBackend(ai_enabled=True, gemini_api_key="secret-key")
        )
        self.assertTrue(settings.is_ai_enabled())
        self.assertEqual(settings.get_gemini_api_key(), "secret-key")

    def test_blank_api_key_returns_none(self):
        settings = AppSettings(
            InMemorySettingsBackend(ai_enabled=True, gemini_api_key="   ")
        )
        self.assertIsNone(settings.get_gemini_api_key())

    def test_autostart_toggle(self):
        settings = AppSettings(InMemorySettingsBackend(autostart_enabled=False))
        self.assertFalse(settings.is_autostart_enabled())

        settings.set_autostart(True)
        self.assertTrue(settings.is_autostart_enabled())

        settings.set_autostart(False)
        self.assertFalse(settings.is_autostart_enabled())

    def test_ai_enabled_toggle_controls_availability_and_api_key(self):
        settings = AppSettings(
            InMemorySettingsBackend(ai_enabled=False, gemini_api_key="secret-key")
        )
        self.assertFalse(settings.is_ai_enabled())
        self.assertIsNone(settings.get_gemini_api_key())

        settings.set_ai_enabled(True)
        self.assertTrue(settings.is_ai_enabled())
        self.assertEqual(settings.get_gemini_api_key(), "secret-key")

        settings.set_ai_enabled(False)
        self.assertFalse(settings.is_ai_enabled())
        self.assertIsNone(settings.get_gemini_api_key())


if __name__ == "__main__":
    unittest.main()
