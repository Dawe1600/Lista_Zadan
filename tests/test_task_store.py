import os
import sys
import tempfile
import unittest

_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from lista_zadan.task_store import InMemoryTaskRepository, JsonTaskRepository, TaskStore


class TestTaskStore(unittest.TestCase):
    def test_add_update_and_persist_immediately(self):
        repo = InMemoryTaskRepository()
        store = TaskStore(repo)

        task = store.add("  Kupić mleko  ", "  2%  ")
        self.assertEqual(task.text, "Kupić mleko")
        self.assertEqual(task.description, "2%")
        self.assertFalse(task.done)
        self.assertFalse(task.is_important)

        # Reloading from the same repository confirms immediate persistence.
        reloaded = TaskStore(repo)
        self.assertEqual(len(reloaded.active_tasks()), 1)
        self.assertEqual(reloaded.active_tasks()[0].id, task.id)

        store.update(task.id, "Kupić chleb", "razowy")
        reloaded = TaskStore(repo)
        self.assertEqual(reloaded.get(task.id).text, "Kupić chleb")
        self.assertEqual(reloaded.get(task.id).description, "razowy")

    def test_add_and_update_with_is_important(self):
        repo = InMemoryTaskRepository()
        store = TaskStore(repo)

        task = store.add("Pilny raport", "Do piątku", is_important=True)
        self.assertTrue(task.is_important)

        reloaded = TaskStore(repo)
        self.assertTrue(reloaded.get(task.id).is_important)

        store.update(task.id, "Pilny raport", "Przełożony", is_important=False)
        reloaded = TaskStore(repo)
        self.assertFalse(reloaded.get(task.id).is_important)

    def test_duplicate_titles_do_not_collide_on_restore_or_delete(self):
        repo = InMemoryTaskRepository()
        store = TaskStore(repo)

        first = store.add("Raport", "Q1")
        second = store.add("Raport", "Q2")

        store.complete(first.id)
        store.complete(second.id)
        self.assertEqual(len(store.completed_tasks()), 2)

        store.restore(first.id)
        self.assertEqual([t.id for t in store.active_tasks()], [first.id])
        self.assertEqual([t.id for t in store.completed_tasks()], [second.id])

        store.delete(second.id)
        self.assertEqual(store.completed_tasks(), [])
        self.assertEqual([t.id for t in store.active_tasks()], [first.id])

    def test_complete_and_restore_preserve_is_important(self):
        repo = InMemoryTaskRepository()
        store = TaskStore(repo)

        task = store.add("Awaria serwera")
        store.toggle_important(task.id)
        self.assertTrue(store.get(task.id).is_important)

        store.complete(task.id)
        self.assertTrue(store.completed_tasks()[0].is_important)

        store.restore(task.id)
        self.assertTrue(store.active_tasks()[0].is_important)

    def test_reorder_active_preserves_completed_and_persists(self):
        repo = InMemoryTaskRepository()
        store = TaskStore(repo)

        t1 = store.add("Pierwsze")
        t2 = store.add("Drugie")
        t3 = store.add("Trzecie")
        store.complete(t3.id)

        store.reorder_active([t2.id, t1.id])

        reloaded = TaskStore(repo)
        self.assertEqual([t.id for t in reloaded.active_tasks()], [t2.id, t1.id])
        self.assertEqual([t.id for t in reloaded.completed_tasks()], [t3.id])

    def test_clear_completed_keeps_active_tasks(self):
        repo = InMemoryTaskRepository()
        store = TaskStore(repo)

        active = store.add("Aktywne")
        done = store.add("Zakończone")
        store.complete(done.id)

        store.clear_completed()
        self.assertEqual([t.id for t in store.active_tasks()], [active.id])
        self.assertEqual(store.completed_tasks(), [])

    def test_migrates_legacy_is_problem_and_missing_id(self):
        legacy_data = [
            {"text": "Stare ważne", "done": False, "description": "", "is_problem": True},
            {"text": "Stare zwykłe", "done": True, "description": "ok", "is_problem": False},
        ]
        store = TaskStore(InMemoryTaskRepository(legacy_data))

        active = store.active_tasks()
        completed = store.completed_tasks()
        self.assertEqual(len(active), 1)
        self.assertTrue(active[0].is_important)
        self.assertTrue(bool(active[0].id))

        self.assertEqual(len(completed), 1)
        self.assertFalse(completed[0].is_important)
        self.assertTrue(bool(completed[0].id))

    def test_json_repository_handles_corrupt_and_valid_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "tasks.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not valid json")

            repo = JsonTaskRepository(path)
            store = TaskStore(repo)
            self.assertEqual(store.active_tasks(), [])

            task = store.add("Nowe zadanie")
            reloaded = TaskStore(JsonTaskRepository(path))
            self.assertEqual([t.id for t in reloaded.active_tasks()], [task.id])


if __name__ == "__main__":
    unittest.main()
