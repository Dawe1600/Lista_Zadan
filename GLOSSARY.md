# Lista Zadań

Desktop task list application for managing active tasks, completed history, and application preferences.

## Language

**Task**:
A single work item with a title, optional description, and importance flag.
_Avoid_: Item, entry, ticket

**Active Task**:
A task currently on the main list awaiting completion.
_Avoid_: Pending task, open task

**Completed Task**:
A task marked as done and moved to history, retaining its properties so it can be restored without loss.
_Avoid_: Done item, archived item

**Important Task**:
A task highlighted as high-priority (`is_important`).
_Avoid_: Problem task, flagged task, urgent task

**Task Store**:
The single source of truth that owns task identity, ordering, lifecycle transitions, and persistence.
_Avoid_: Task manager, task repo, task list state

**App Settings**:
Application preferences and OS integration (AI availability flag, Gemini key, and Windows autostart).
_Avoid_: Config, registry wrapper, preferences helper
