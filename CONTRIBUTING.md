# Współpraca przy projekcie (Contributing)

Dziękujemy za chęć rozwoju **Lista Zadań AI**! Poniżej znajdziesz krótkie zasady, które ułatwią przygotowanie zmian i przejście automatycznych testów w CI.

## Środowisko deweloperskie

Wymagania: **Python 3.10+**, system **Windows** (lub środowisko z PyQt5 w trybie `offscreen` do samych testów).

```bash
git clone https://github.com/Dawe1600/Lista_Zadan.git
cd Lista_Zadan
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Przed wysłaniem Pull Requesta

1. **Linter (`ruff`):**
   ```bash
   ruff check src tests
   ```
2. **Testy jednostkowe:**
   ```bash
   set QT_QPA_PLATFORM=offscreen
   python -m unittest discover -s tests -v
   ```
   *(W PowerShell: `$env:QT_QPA_PLATFORM="offscreen"; python -m unittest discover -s tests -v`)*
3. **Standardy kodu:** Zapoznaj się z [CODING_STANDARDS.md](CODING_STANDARDS.md) oraz słownikiem pojęć w [GLOSSARY.md](GLOSSARY.md).

## Zgłaszanie błędów i propozycji

* Skorzystaj z szablonów w zakładce **Issues** (zgłoszenie błędu lub propozycja funkcji).
* W PR krótko opisz, co i dlaczego zostało zmienione, oraz dołącz zrzut ekranu, jeśli zmiana dotyczy wyglądu UI.
