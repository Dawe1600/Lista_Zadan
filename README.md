# Lista Zadań (PyQt5) ✅

Prosta, lekka aplikacja desktopowa w **Python + PyQt5** do zarządzania listą zadań (to‑do) z możliwością:
- dodawania zadań,
- oznaczania jako wykonane (checkbox + przekreślenie),
- edycji zadania oraz opisu po dwukliku,
- usuwania wykonanych zadań,
- opcjonalnego uruchamiania wraz ze startem systemu (Windows),
- automatycznego zapisu do pliku `tasks.json` w katalogu **Dokumenty** użytkownika.

Aplikacja ma **okno bez ramek** (frameless) oraz możliwość **przeciągania okna myszką** (z wyłączeniem interaktywnych kontrolek, np. pól tekstowych i przycisków).

---

## ✨ Funkcje

- ✅ Lista zadań z checkboxami (wykonane / niewykonane)
- 📝 Dodawanie zadania + opcjonalny opis
- ✏️ Edycja zadania i opisu po **podwójnym kliknięciu**
- 🗑️ Usuwanie wszystkich **zaznaczonych (wykonanych)** zadań jednym przyciskiem
- 💾 Automatyczny zapis/odczyt w formacie **JSON**
- 🎨 Ciemny motyw (dark UI) + emoji w ikonach/przyciskach
- ⚙️ Opcja **autostartu** z systemem Windows (w menu ustawień)
- 🪟 Okno bez ramek + przeciąganie okna

## 🧠 Konfiguracja AI (Google Gemini)

Aby korzystać z funkcji asystenta AI, należy użyć własnego klucza Google API.
1. Zdobądź klucz API z [Google AI Studio](https://aistudio.google.com/).
2. Utwórz plik `secrets.py` w głównym katalogu projektu (plik jest ignorowany przez git) i wpisz:
   ```python
   GEMINI_API_KEY = "TWOJ_KLUCZ_API"
   ```

## 🚀 Uruchomienie

Plik wykonywalny `.exe` znajduje się w głównym katalogu projektu.
