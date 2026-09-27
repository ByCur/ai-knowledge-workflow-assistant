from app.agent_service import (
    get_requested_task_count,
    has_completion_intent,
)


def test_detects_requested_task_count():
    result = get_requested_task_count(
        "Créame 3 tareas sobre Docker"
    )

    assert result == 3


def test_task_count_is_none_when_not_given():
    result = get_requested_task_count(
        "Créame algunas tareas sobre Docker"
    )

    assert result is None


def test_completion_requires_explicit_intent():
    assert (
        has_completion_intent(
            "Marca como completada la tarea 3"
        )
        is True
    )


def test_creating_tasks_is_not_completion():
    assert (
        has_completion_intent(
            "Créame 3 tareas sobre Docker"
        )
        is False
    )