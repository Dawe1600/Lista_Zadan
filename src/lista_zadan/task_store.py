import json
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass
class Task:
    """Single task item owned by TaskStore."""

    id: str
    text: str
    done: bool = False
    description: str = ""
    is_important: bool = False

    @classmethod
    def from_dict(cls, raw: dict) -> "Task":
        """Build a Task from a stored dict, migrating legacy fields if needed."""
        is_important = raw.get("is_important")
        if is_important is None:
            is_important = raw.get("is_problem", False)

        return cls(
            id=str(raw.get("id") or uuid.uuid4().hex),
            text=str(raw.get("text", "")),
            done=bool(raw.get("done", False)),
            description=str(raw.get("description", "")),
            is_important=bool(is_important),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class TaskRepository(Protocol):
    """Persistence seam for TaskStore."""

    def load(self) -> list[dict]: ...

    def save(self, tasks: list[dict]) -> None: ...


class JsonTaskRepository:
    """Stores tasks in a UTF-8 JSON file."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list[dict]:
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def save(self, tasks: list[dict]) -> None:
        parent = os.path.dirname(self.file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)


class InMemoryTaskRepository:
    """In-memory adapter for testing TaskStore without disk I/O."""

    def __init__(self, initial_data: list[dict] | None = None):
        self._data: list[dict] = [dict(item) for item in (initial_data or [])]

    def load(self) -> list[dict]:
        return [dict(item) for item in self._data]

    def save(self, tasks: list[dict]) -> None:
        self._data = [dict(item) for item in tasks]


class TaskStore:
    """Single source of truth for task identity, ordering, lifecycle, and persistence."""

    def __init__(self, repository: TaskRepository):
        self._repository = repository
        self._tasks: list[Task] = []
        self.reload()

    def reload(self) -> None:
        raw_items = self._repository.load()
        self._tasks = [
            Task.from_dict(item)
            for item in raw_items
            if isinstance(item, dict) and str(item.get("text", "")).strip()
        ]

    def active_tasks(self) -> list[Task]:
        return [t for t in self._tasks if not t.done]

    def completed_tasks(self) -> list[Task]:
        return [t for t in self._tasks if t.done]

    def get(self, task_id: str) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def add(self, text: str, description: str = "", is_important: bool = False) -> Task:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Task text cannot be empty.")
        task = Task(
            id=uuid.uuid4().hex,
            text=clean_text,
            done=False,
            description=description.strip(),
            is_important=bool(is_important),
        )
        self._tasks.append(task)
        self._persist()
        return task

    def update(
        self,
        task_id: str,
        text: str,
        description: str,
        is_important: bool | None = None,
    ) -> Task:
        task = self._require(task_id)
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Task text cannot be empty.")
        task.text = clean_text
        task.description = description.strip()
        if is_important is not None:
            task.is_important = bool(is_important)
        self._persist()
        return task

    def complete(self, task_id: str) -> Task:
        task = self._require(task_id)
        task.done = True
        self._persist()
        return task

    def restore(self, task_id: str) -> Task:
        task = self._require(task_id)
        task.done = False
        self._persist()
        return task

    def toggle_important(self, task_id: str) -> Task:
        task = self._require(task_id)
        task.is_important = not task.is_important
        self._persist()
        return task

    def reorder_active(self, ordered_ids: list[str]) -> None:
        active_by_id = {t.id: t for t in self._tasks if not t.done}
        reordered = [active_by_id.pop(tid) for tid in ordered_ids if tid in active_by_id]
        # Preserve any active tasks not present in ordered_ids at the end.
        reordered.extend(active_by_id.values())
        completed = [t for t in self._tasks if t.done]
        self._tasks = reordered + completed
        self._persist()

    def delete(self, task_id: str) -> None:
        self._tasks = [t for t in self._tasks if t.id != task_id]
        self._persist()

    def clear_completed(self) -> None:
        self._tasks = [t for t in self._tasks if not t.done]
        self._persist()

    def _require(self, task_id: str) -> Task:
        task = self.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        return task

    def _persist(self) -> None:
        self._repository.save([t.to_dict() for t in self._tasks])
