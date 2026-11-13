# Coding Standards

Judgement-call rules for code review. Mechanical checks (unused imports, import sorting, syntax/style lint) belong in `ruff` via `pyproject.toml`, not here.

## Domain vocabulary
- Follow `GLOSSARY.md`: use `Important Task` (`is_important`) rather than legacy `"problem"` wording in user-facing text, AI prompts, and new symbols.

## Module boundaries
- Keep Qt dialog classes in `src/lista_zadan/dialogs.py` separate from Gemini API / `QThread` worker logic as new AI features are added.
- Keep `TaskStore` mutations (`add`, `update`, `reorder_active`, `complete`, `restore`, `delete`) inside `TaskStore` rather than manipulating `active_tasks()` lists from UI code.
- Avoid pure 1:1 pass-through wrappers when a backend protocol or direct adapter suffices.

## Naming
- Use English for new class, method, and variable names; keep existing Polish UI labels/strings in Polish.

## PyQt5 layout & tests
- Changes to `ListaZadan` row widgets, `TaskDelegate`, or frameless painting must be covered by an offscreen `show()` + `processEvents()` geometry check in `tests/test_main_widget.py` (no clipped rows, no horizontal scrollbar overflow, bounded initial row height).
