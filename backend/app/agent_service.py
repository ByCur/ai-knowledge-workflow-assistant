import json
import re
from .llm_service import generate_chat
from sqlalchemy.orm import Session

from .agent_tools import (
    complete_task_tool,
    create_task_tool,
    list_tasks_tool,
    search_documents_tool,
)
from .config import settings


SYSTEM_PROMPT = """
You are an AI workflow agent.

You have direct access to tools.
The USER does NOT execute tools.
YOU must execute the tools whenever they are needed.

AVAILABLE TOOLS:

1. search_documents
Arguments:
{
  "query": "string",
  "limit": 3
}

2. create_task
Arguments:
{
  "title": "string",
  "description": "string",
  "source_document_id": integer or null
}

3. list_tasks
Arguments:
{}

4. complete_task
Arguments:
{
  "task_id": integer
}

TO USE A TOOL, respond ONLY with valid JSON:

{
  "type": "tool",
  "tool": "tool_name",
  "arguments": {}
}

WHEN THE REQUEST IS FULLY COMPLETED, respond ONLY:

{
  "type": "final",
  "answer": "final response to the user"
}

IMPORTANT RULES:

- Never tell the user to call a tool.
- Never explain that a tool could be used.
- You are responsible for calling tools yourself.

- If the user asks to see, inspect or list tasks,
  you MUST call list_tasks before answering.

- If the user asks to complete a task,
  you MUST call list_tasks if necessary to identify it,
  then call complete_task.

- If the user asks to create a task,
  you MUST call create_task.

- If tasks must be created from uploaded documents,
  you MUST call search_documents first,
  then create_task for each required task.

- If the user asks something about uploaded documents,
  use search_documents.

- Never claim an action succeeded unless its tool
  returned a successful result.

- Perform only ONE tool call per response.
- After receiving a TOOL RESULT, continue working
  until the complete user request has been fulfilled.
- Answer in the same language as the user.
- Creating a task and completing a task are different actions.

- If the user asks to create tasks, use create_task
  and leave the new tasks with status "pending".

- NEVER call complete_task after creating a task
  unless the user explicitly asked to mark that task
  as completed, finished, done or equivalent.

- "Complete the request" means finish processing the
  user's request. It does NOT mean marking created
  tasks as completed.

- Do not perform actions that the user did not request.

- When the user asks you to create a specific
  number of tasks, stop immediately after that
  number of create_task calls succeeds.

- Do NOT call list_tasks just to verify tasks
  that you have just created. The successful
  create_task result is sufficient confirmation.

- Never intentionally create duplicate pending tasks.

- If create_task reports that a task already exists,
  do not create the same task again.

- If the user requested multiple tasks and one proposed
  task is a duplicate, create a different relevant task
  instead.

- Task titles should describe distinct actions.

EXAMPLE:

User:
Muéstrame mis tareas pendientes

Your first response MUST be:

{
  "type": "tool",
  "tool": "list_tasks",
  "arguments": {}
}

After receiving the tool result, return:

{
  "type": "final",
  "answer": "Estas son tus tareas pendientes: ..."
}
""".strip()

import re


def get_requested_task_count(
    instruction: str,
) -> int | None:
    match = re.search(
        r"\b(\d+)\s+(?:tareas|tasks)\b",
        instruction.lower(),
    )

    if not match:
        return None

    return int(match.group(1))


def has_completion_intent(
    instruction: str,
) -> bool:
    instruction_lower = instruction.lower()

    phrases = [
        "completa la tarea",
        "completar la tarea",
        "marca como completada",
        "marca como hecha",
        "termina la tarea",
        "finaliza la tarea",
        "complete the task",
        "mark as completed",
        "mark as done",
    ]

    return any(
        phrase in instruction_lower
        for phrase in phrases
    )


def run_agent(
    db: Session,
    instruction: str,
) -> dict:

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": instruction,
        },
    ]

    executed_actions = []

    requested_task_count = (
    get_requested_task_count(
        instruction
    )
)

    match = re.search(
        r"\b(\d+)\s+(?:tareas|tasks)\b",
        instruction.lower(),
    )

    if match:
        requested_task_count = int(
            match.group(1)
        )

    for _ in range(10):
        raw_content = generate_chat(
        messages=messages,
        json_mode=True,
        )

        try:
            decision = json.loads(
                raw_content
            )
        except json.JSONDecodeError:
            return {
                "answer":
                    "The agent returned an "
                    "invalid response.",
                "actions":
                    executed_actions,
            }

        if decision.get("type") == "final":
            instruction_lower = instruction.lower()

            tool_required = any(
                word in instruction_lower
                for word in [
                    "task",
                    "tasks",
                    "tarea",
                    "tareas",
                    "document",
                    "documents",
                    "documento",
                    "documentos",
                ]
            )

            if tool_required and not executed_actions:
                 messages.append(
                     {
                            "role": "user",
                            "content": (
                            "You attempted to finish without "
                             "using a required tool. "
                             "Do not tell me which tool to use. "
                             "Use the appropriate tool yourself now."
                         ),
                     }
                )

                 continue

            return {
        "answer": decision.get(
            "answer",
            "Request completed.",
        ),
        "actions": executed_actions,
    }

        if decision.get("type") != "tool":
            return {
                "answer":
                    "The agent could not "
                    "determine an action.",
                "actions":
                    executed_actions,
            }

        tool_name = decision.get("tool")
        arguments = (
            decision.get("arguments")
            or {}
        )

        if (
    tool_name == "complete_task"
    and not has_completion_intent(
        instruction
    )
):
            instruction_lower = instruction.lower()

            completion_intent = any(
                 phrase in instruction_lower
                 for phrase in [
                     "completa la tarea",
                     "completar la tarea",
                     "marca como completada",
                     "marca como hecha",
                     "termina la tarea",
                     "finaliza la tarea",
                     "complete the task",
                     "mark as completed",
                     "mark as done",
                 ]  
            )

            if not completion_intent:
                 tool_result = {
                    "error": (
                    "complete_task is not authorized "
                    "because the user did not ask to "
                    "complete any task."
                    )
             }

            messages.append(
            {
                "role": "assistant",
                "content": json.dumps(
                    decision,
                    ensure_ascii=False,
                ),
            }
            )

            messages.append(
            {
                "role": "user",
                "content": (
                    "TOOL RESULT:\n"
                    + json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    )
                    + "\nDo not complete tasks. "
                    "Continue the original request."
                ),
             }
            )

            continue

        tool_result = execute_tool(
            db=db,
            tool_name=tool_name,
            arguments=arguments,
        )

        executed_actions.append(
            {
                "tool": tool_name,
                "arguments": arguments,
                "result": tool_result,
            }
        )

        if (
            tool_name == "create_task"
            and requested_task_count is not None
        ):
            created_tasks = [
                action
                    for action in executed_actions
                        if (
                            action["tool"] == "create_task"
                            and isinstance(
                            action["result"],
                            dict,
                            )
                    and action["result"].get(
                    "created"
                ) is True
            )
            ]

            if (
                len(created_tasks)
                >= requested_task_count
            ):
                task_titles = [
                action["result"]["title"]
                for action in created_tasks
                ]

                task_list = "\n".join(
                    f"{index + 1}. {title}"
                    for index, title
                    in enumerate(task_titles)
                )

                return {
                    "answer": (
                        f"He creado "
                        f"{requested_task_count} tareas:\n"
                        f"{task_list}"
                    ),
                    "actions": executed_actions,
                }

        messages.append(
            {
                "role": "assistant",
                "content":
                    json.dumps(
                        decision,
                        ensure_ascii=False,
                    ),
            }
        )

        messages.append(
            {
                "role": "user",
                "content": (
                    "TOOL RESULT:\n"
                    + json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    )
                    + "\nContinue working on "
                    "the original request."
                ),
            }
        )

    return {
        "answer": (
            "The agent reached its maximum "
            "number of actions."
        ),
        "actions": executed_actions,
    }


def execute_tool(
    db: Session,
    tool_name: str,
    arguments: dict,
):
    if tool_name == "search_documents":
        return search_documents_tool(
            db=db,
            query=arguments.get(
                "query",
                "",
            ),
            limit=arguments.get(
                "limit",
                3,
            ),
        )

    if tool_name == "create_task":
        return create_task_tool(
            db=db,
            title=arguments.get(
                "title",
                "Untitled task",
            ),
            description=arguments.get(
                "description",
                "",
            ),
            source_document_id=
                arguments.get(
                    "source_document_id"
                ),
        )

    if tool_name == "list_tasks":
        return list_tasks_tool(
            db=db
        )

    if tool_name == "complete_task":
        return complete_task_tool(
            db=db,
            task_id=arguments.get(
                "task_id"
            ),
        )

    return {
        "error":
            f"Unknown tool: {tool_name}"
    }