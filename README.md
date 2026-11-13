# 📝 Lista Zadań AI (To-Do List AI)

Nowoczesna, desktopowa aplikacja do zarządzania zadaniami (To-Do) stworzona w języku Python przy użyciu biblioteki **PyQt5**. Aplikacja wyróżnia się minimalistycznym, ciemnym interfejsem (Dark Mode) oraz wbudowanym **Asystentem AI** (napędzanym przez Google Gemini), który pomaga w rozwiązywaniu najtrudniejszych zadań.

<img width="423" height="243" alt="ToDoListAi" src="https://github.com/user-attachments/assets/9da27445-49ec-4a6c-9b5b-1cfe2a83b819" />

## ✨ Główne funkcje

* **Wsparcie AI (Google Gemini):** Oznacz zadanie jako "problem", kliknij prawym przyciskiem myszy i poproś AI o wygenerowanie 3 konkretnych kroków do jego rozwiązania.
* **Drag & Drop:** Wygodnie zmieniaj kolejność zadań chwytając je i upuszczając (interaktywny kursor rączki).
* **Nowoczesny Interfejs (Frameless):** Brak standardowych ramek systemu Windows. Okno można swobodnie przeciągać po ekranie, chwytając za dowolne puste miejsce.
* **Zarządzanie Zadaniami:** Dodawanie, edycja, usuwanie i opcjonalne dodawanie dłuższych opisów.
* **Historia Zadań:** Dedykowany widok dla ukończonych zadań z opcją ich łatwego przywracania.
* **Autostart:** Możliwość uruchamiania aplikacji wraz ze startem systemu Windows.

## 📥 Instalacja (Dla użytkowników)

Nie musisz znać Pythona, aby korzystać z tej aplikacji!
1. Przejdź do zakładki **[Releases](../../releases)** po prawej stronie repozytorium na GitHubie.
2. Pobierz najnowszy plik `Instalator_ListyZadan.exe`.
3. Uruchom instalator. W trakcie instalacji zostaniesz zapytany, czy chcesz włączyć funkcje AI.
4. Jeśli wybierzesz "Tak", wklej swój darmowy klucz **Google Gemini API** (możesz go wygenerować w [Google AI Studio](https://aistudio.google.com/)).
5. Gotowe! Aplikacja zainstaluje się i jest gotowa do pracy.

---

## 🛠️ Dla programistów (Uruchamianie i kompilacja)

Jeśli chcesz zmodyfikować kod, uruchomić aplikację lokalnie ze źródeł lub samodzielnie ją skompilować, postępuj zgodnie z poniższymi krokami.

### 1. Wymagania i uruchomienie ze źródeł
* Python 3.8+
* System operacyjny: Windows (aplikacja korzysta z Rejestru Windows do zapisu ustawień).

```bash
# Sklonuj repozytorium
git clone https://github.com/Dawe1600/lista_zadan.git

# Zainstaluj zależności
pip install PyQt5 google-genai

# Uruchom aplikację
python main.py
