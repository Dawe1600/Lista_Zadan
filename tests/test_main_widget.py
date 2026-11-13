import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QCheckBox, QLabel, QPushButton

from lista_zadan.app_settings import AppSettings, InMemorySettingsBackend
from lista_zadan.dialogs import AddTaskDialog
from lista_zadan.logic import ListaZadan
from lista_zadan.task_store import InMemoryTaskRepository, TaskStore


class TestMainWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def _make_widget(
        self,
        initial_tasks: list[dict] | None = None,
        ai_enabled: bool = False,
        gemini_api_key: str | None = None,
        autostart_enabled: bool = False,
    ) -> tuple[ListaZadan, TaskStore, AppSettings]:
        store = TaskStore(InMemoryTaskRepository(initial_tasks))
        settings = AppSettings(
            InMemorySettingsBackend(
                ai_enabled=ai_enabled,
                gemini_api_key=gemini_api_key,
                autostart_enabled=autostart_enabled,
            )
        )
        widget = ListaZadan(store=store, settings=settings)
        return widget, store, settings

    def test_header_active_task_count_updates_across_lifecycle(self):
        widget, store, _ = self._make_widget()
        badge = widget.findChild(QLabel, "TaskCountBadge")
        self.assertIsNotNone(badge)
        self.assertEqual(badge.text(), "0")

        t1 = store.add("Pierwsze zadanie")
        t2 = store.add("Drugie zadanie")
        widget.render_active_tasks()
        self.assertEqual(badge.text(), "2")

        store.complete(t1.id)
        widget.render_active_tasks()
        self.assertEqual(badge.text(), "1")

        store.restore(t1.id)
        widget.render_active_tasks()
        self.assertEqual(badge.text(), "2")

        store.delete(t2.id)
        widget.render_active_tasks()
        self.assertEqual(badge.text(), "1")

    def test_row_renders_description_preview_and_important_flag_and_completes_via_checkbox(self):
        widget, store, _ = self._make_widget(
            initial_tasks=[
                {"id": "1", "text": "Z opisem", "description": "Szczegóły zadania", "is_important": True},
                {"id": "2", "text": "Bez opisu", "description": "", "is_important": False},
            ]
        )

        self.assertEqual(widget.list.count(), 2)

        item0 = widget.list.item(0)
        row0 = widget.list.itemWidget(item0)
        self.assertIsNotNone(row0)
        self.assertTrue(bool(item0.data(Qt.UserRole + 1)))
        self.assertEqual(row0.findChild(QLabel, "TaskTitleLabel").text(), "Z opisem")
        desc0 = row0.findChild(QLabel, "TaskDescLabel")
        self.assertIsNotNone(desc0)
        self.assertIn("Szczegóły zadania", desc0.text())

        item1 = widget.list.item(1)
        row1 = widget.list.itemWidget(item1)
        self.assertIsNotNone(row1)
        self.assertFalse(bool(item1.data(Qt.UserRole + 1)))
        self.assertEqual(row1.findChild(QLabel, "TaskTitleLabel").text(), "Bez opisu")
        self.assertIsNone(row1.findChild(QLabel, "TaskDescLabel"))

        checkbox = row0.findChild(QCheckBox, "TaskCompleteCheckbox")
        self.assertIsNotNone(checkbox)
        checkbox.click()

        self.assertEqual([t.id for t in store.active_tasks()], ["2"])
        self.assertEqual([t.id for t in store.completed_tasks()], ["1"])
        self.assertEqual(widget.list.count(), 1)
        self.assertEqual(widget.findChild(QLabel, "TaskCountBadge").text(), "1")

    def test_row_quick_actions_reorder_toggle_important_ai_visibility_and_delete(self):
        widget, store, _ = self._make_widget(
            initial_tasks=[
                {"id": "1", "text": "Pierwsze", "is_important": False},
                {"id": "2", "text": "Drugie", "is_important": True},
            ],
            ai_enabled=True,
        )

        # Row 0 is not important -> AI button hidden; Row 1 is important -> AI button visible
        row0 = widget.list.itemWidget(widget.list.item(0))
        row1 = widget.list.itemWidget(widget.list.item(1))
        self.assertFalse(row0.findChild(QPushButton, "AiBtn").isVisibleTo(row0))
        self.assertTrue(row1.findChild(QPushButton, "AiBtn").isVisibleTo(row1))

        # Move down on row 0 -> order becomes ["2", "1"]
        row0.findChild(QPushButton, "MoveDownBtn").click()
        self.assertEqual([t.id for t in store.active_tasks()], ["2", "1"])

        # Move up on row 1 -> order becomes ["1", "2"]
        row1_after = widget.list.itemWidget(widget.list.item(1))
        row1_after.findChild(QPushButton, "MoveUpBtn").click()
        self.assertEqual([t.id for t in store.active_tasks()], ["1", "2"])

        # Toggle important on row 0 -> task "1" becomes important, AI button becomes visible
        row0_after = widget.list.itemWidget(widget.list.item(0))
        row0_after.findChild(QPushButton, "ImportantBtn").click()
        self.assertTrue(store.get("1").is_important)
        row0_imp = widget.list.itemWidget(widget.list.item(0))
        self.assertTrue(row0_imp.findChild(QPushButton, "AiBtn").isVisibleTo(row0_imp))

        # Delete row 0 -> only task "2" remains, badge shows "1"
        row0_imp.findChild(QPushButton, "DeleteBtn").click()
        self.assertEqual([t.id for t in store.active_tasks()], ["2"])
        self.assertEqual(widget.list.count(), 1)
        self.assertEqual(widget.findChild(QLabel, "TaskCountBadge").text(), "1")

    def test_settings_menu_toggles_autostart_and_ai_and_refreshes_row_ai_controls(self):
        widget, _, settings = self._make_widget(
            initial_tasks=[{"id": "1", "text": "Ważne", "is_important": True}],
            ai_enabled=False,
            autostart_enabled=False,
        )

        row_before = widget.list.itemWidget(widget.list.item(0))
        self.assertFalse(row_before.findChild(QPushButton, "AiBtn").isVisibleTo(row_before))

        menu = widget.build_settings_menu()
        actions = {a.text(): a for a in menu.actions()}
        self.assertIn("Uruchamiaj przy starcie systemu", actions)
        self.assertIn("Asystent AI", actions)

        ai_action = actions["Asystent AI"]
        self.assertFalse(ai_action.isChecked())
        ai_action.trigger()

        self.assertTrue(settings.is_ai_enabled())
        row_after = widget.list.itemWidget(widget.list.item(0))
        self.assertTrue(row_after.findChild(QPushButton, "AiBtn").isVisibleTo(row_after))

        autostart_action = actions["Uruchamiaj przy starcie systemu"]
        self.assertFalse(autostart_action.isChecked())
        autostart_action.trigger()
        self.assertTrue(settings.is_autostart_enabled())

    def test_add_task_dialog_exposes_important_checkbox_for_create_and_edit(self):
        create_dlg = AddTaskDialog()
        create_dlg.input.setText("Nowe ważne")
        create_dlg.desc_input.setPlainText("Opis")
        self.assertFalse(create_dlg.important_checkbox.isChecked())
        create_dlg.important_checkbox.setChecked(True)
        self.assertEqual(create_dlg.get_data(), ("Nowe ważne", "Opis", True))

        edit_dlg = AddTaskDialog(text="Istniejące", description="Detale", is_important=True)
        self.assertTrue(edit_dlg.important_checkbox.isChecked())
        edit_dlg.important_checkbox.setChecked(False)
        self.assertEqual(edit_dlg.get_data(), ("Istniejące", "Detale", False))

    def test_description_preview_skips_leading_blank_lines_and_context_menu_retains_actions(self):
        widget, store, _ = self._make_widget(
            initial_tasks=[
                {"id": "1", "text": "Zadanie", "description": "\n\nPierwsza linia\nDruga", "is_important": True},
            ],
            ai_enabled=True,
        )

        row = widget.list.itemWidget(widget.list.item(0))
        desc_lbl = row.findChild(QLabel, "TaskDescLabel")
        self.assertIsNotNone(desc_lbl)
        self.assertEqual(desc_lbl.text(), "Pierwsza linia")

        menu = widget.build_context_menu(store.get("1"))
        action_texts = [a.text() for a in menu.actions() if not a.isSeparator()]
        self.assertEqual(
            action_texts,
            ["🧠 Zapytaj AI jak to rozwiązać", "Usuń oznaczenie ważności", "Usuń zadanie"],
        )

        # Triggering toggle important from context menu updates store and widget
        menu.actions()[2].trigger()
        self.assertFalse(store.get("1").is_important)

    def test_widget_has_transparent_background_and_rows_fit_without_clipping(self):
        widget, _, _ = self._make_widget(
            initial_tasks=[
                {
                    "id": "1",
                    "text": "WSU437 / Złożyć zaświadczenie o statusie studenta na semestr zimowy",
                    "description": "Wysłać do Działu Nauczania zaświadczenie potwierdzające status studenta",
                    "is_important": True,
                }
            ],
            ai_enabled=True,
        )
        widget.show()
        self._app.processEvents()

        # 1. MainWindow outer background must remain translucent
        self.assertTrue(widget.testAttribute(Qt.WA_TranslucentBackground))

        # 2. Row quick actions must fit inside the list viewport without horizontal clipping
        item = widget.list.item(0)
        row = widget.list.itemWidget(item)
        vp = widget.list.viewport().rect()
        del_btn = row.findChild(QPushButton, "DeleteBtn")
        self.assertLessEqual(del_btn.geometry().right(), vp.right())

        # 3. Row height must not clip title/description vertically at its rendered width
        self.assertGreaterEqual(row.height(), row.layout().totalHeightForWidth(row.width()))

    def test_initial_show_row_height_matches_rerender_without_oversized_gap(self):
        widget, _, _ = self._make_widget(
            initial_tasks=[
                {
                    "id": "1",
                    "text": "Wysłać zaświadczenie o statusie studenta do Salusa",
                    "description": "Wysłać do CM Salus zaświadczenie potwierdzające",
                }
            ]
        )
        widget.show()
        self._app.processEvents()
        initial_height = widget.list.visualItemRect(widget.list.item(0)).height()

        widget.render_active_tasks()
        self._app.processEvents()
        rerender_height = widget.list.visualItemRect(widget.list.item(0)).height()

        self.assertEqual(initial_height, rerender_height)


if __name__ == "__main__":
    unittest.main()
