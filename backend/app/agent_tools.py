from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Task
from .retrieval_service import retrieve_relevant_chunks


def search_documents_tool(
    db: Session,
    query: str,
    limit: int = 3,
):
    return retrieve_relevant_chunks(
        db=db,
        query=query,
        limit=limit,
    )


def create_task_tool(
    db: Session,
    title: str,
    description: str = "",
    source_document_id: int | None = None,
):
    clean_title = title.strip()

    existing_task = db.execute(
        select(Task).where(
            func.lower(Task.title)
            == clean_title.lower(),
            Task.status == "pending",
            Task.source_document_id
            == source_document_id,
        )
    ).scalar_one_or_none()

    if existing_task:
        return {
            "created": False,
            "duplicate": True,
            "id": existing_task.id,
            "title": existing_task.title,
            "status": existing_task.status,
            "message": (
                "A pending task with this title "
                "already exists."
            ),
        }

    task = Task(
        title=clean_title,
        description=description.strip(),
        source_document_id=source_document_id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "created": True,
        "duplicate": False,
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "source_document_id":
            task.source_document_id,
    }


def list_tasks_tool(
    db: Session,
):
    result = db.execute(
        select(Task).order_by(
            Task.created_at.desc()
        )
    )

    tasks = result.scalars().all()

    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "source_document_id":
                task.source_document_id,
        }
        for task in tasks
    ]


def complete_task_tool(
    db: Session,
    task_id: int,
):
    task = db.get(
        Task,
        task_id,
    )

    if not task:
        return {
            "error": "Task not found"
        }

    task.status = "completed"

    db.commit()
    db.refresh(task)

    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
    }