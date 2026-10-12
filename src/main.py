import asyncio
import json

from copilot import CopilotClient

try:
    from .tools import (
        get_assignments,
        get_assignment,
        get_current_time,
        update_progress,
    )
except ImportError:
    from tools import (
        get_assignments,
        get_assignment,
        get_current_time,
        update_progress,
    )


MAX_STEPS = 8
MAX_EMPTY_RETRIES = 2

SYSTEM_MESSAGE = """
You are an agentic student assignment planning assistant.

You choose tools based on the information you need.
Python tools return facts. You analyze facts and make judgments.

TOOL PROTOCOL

To call a tool, output exactly one line:
ACTION: {"tool": "tool_name", "args": {}}

To finish, output:
FINAL: your complete answer

AVAILABLE TOOLS

1. get_assignments
Arguments: {}

2. get_assignment
Arguments: {"assignment_id": 1}

3. get_current_time
Arguments: {}

RULES

- Decide which tool to call and when.
- Your next action must depend on the information received.
- Use actual tool results. Never invent assignment data.
- Consider deadlines, remaining minutes, progress, and priority.
- Use remaining minutes, not original estimated minutes.
- Never schedule completed assignments.
- Never schedule work after its deadline.
- For weekly plans, schedule each assignment's full remaining
  minutes in one session. Do not split assignments across days.
- Schedule each assignment at most once.
- Do not invent study availability or calendar events.
- Check daily totals and weekly totals carefully.
- Explain conflicts if assignments cannot reasonably fit.
- If a deadline has passed, identify the overdue assignment.
- For study recommendations, return three ranked options
  when at least three suitable options exist.
- Format recommendations as three separate numbered lines
  beginning exactly with "1. ", "2. ", and "3. ".
- Put each recommendation's assignment title, course, study
  duration, remaining work, deadline, and reason in its item.
- Do not use bullets instead of numbered recommendations.
- Each recommendation must include the assignment, course,
  study duration, remaining work, deadline, and reason.
- Distinguish partial sessions from completing assignments.
- For weekly plans, include all seven dates, assignments,
  durations, deadlines, daily totals, and the grand total.
- List assignments that cannot be scheduled before their deadlines
  separately as conflicts.
- Never return only an introduction when a complete answer is requested.
- Return exactly one ACTION or FINAL per response.
- ACTION must contain valid JSON on one line.
- FINAL must contain a complete, non-empty answer.
- Do not use tools that are not listed above.
"""


def run_tool(tool_name, args):
    """Validate and execute approved tools."""

    if not isinstance(args, dict):
        return {"error": "Tool arguments must be a JSON object."}

    if tool_name == "get_assignments":
        if args:
            return {"error": "get_assignments takes no arguments"}
        return get_assignments()

    if tool_name == "get_current_time":
        if args:
            return {"error": "get_current_time takes no arguments"}
        return get_current_time()

    if tool_name == "get_assignment":
        if set(args) != {"assignment_id"}:
            return {"error": "Expected only assignment_id"}

        assignment_id = args["assignment_id"]

        if (
            not isinstance(assignment_id, int)
            or isinstance(assignment_id, bool)
        ):
            return {"error": "assignment_id must be an integer"}

        return get_assignment(assignment_id)

    return {"error": f"Unknown or unauthorized tool: {tool_name}"}


def parse_action(response_text):
    """Parse tool calls and final answers."""

    if not isinstance(response_text, str):
        return "ERROR", "Model response was not text."

    response_text = response_text.strip()

    if not response_text:
        return "ERROR", "The model returned an empty response."

    for line in response_text.splitlines():
        line = line.strip()

        if line.startswith("FINAL:"):
            answer = line[len("FINAL:"):].strip()

            if answer:
                return "FINAL", answer

            return "EMPTY_FINAL", ""

        if line.startswith("ACTION:"):
            payload = line[len("ACTION:"):].strip()

            try:
                action = json.loads(payload)
            except json.JSONDecodeError:
                return "ERROR", "The ACTION JSON was invalid."

            if not isinstance(action, dict):
                return "ERROR", "ACTION must be a JSON object."

            tool_name = action.get("tool")
            args = action.get("args", {})

            if not isinstance(tool_name, str) or not tool_name:
                return "ERROR", "ACTION needs a tool name."

            if not isinstance(args, dict):
                return "ERROR", "ACTION args must be an object."

            return "ACTION", {
                "tool": tool_name,
                "args": args,
            }

    # Accept complete plain-text responses as final answers.
    if len(response_text) > 20:
        return "FINAL", response_text

    return "ERROR", (
        "No ACTION or FINAL line was found. "
        f"Response received: {response_text[:300]}"
    )


def validate_recommendations(answer):
    """Check whether an answer contains three numbered recommendations."""

    if not isinstance(answer, str) or not answer.strip():
        return False

    numbered_items = 0

    for line in answer.splitlines():
        stripped = line.strip()

        if (
            len(stripped) >= 3
            and stripped[0].isdigit()
            and stripped[1:3] in {". ", ") "}
        ):
            numbered_items += 1

    return numbered_items >= 3


def show_assignments(assignments):
    """Display all assignment records."""

    print("\nYOUR ASSIGNMENTS")
    print("=" * 40)

    for item in assignments:
        print(f"\n{item['course']} - {item['title']}")
        print(f"  Due: {item['due']}")
        print(f"  Status: {item['status']}")
        print(f"  Priority: {item['priority']}/5")
        print(f"  Remaining: {item['remaining_minutes']} minutes")

    print()


def update_assignment_progress(assignments):
    """Record a study session."""

    unfinished = [
        item for item in assignments
        if item["status"] != "completed"
    ]

    if not unfinished:
        print("All assignments are completed!")
        return

    print("\nCHOOSE AN ASSIGNMENT")

    for index, item in enumerate(unfinished, start=1):
        print(
            f"{index}. {item['course']} - {item['title']} "
            f"({item['remaining_minutes']} minutes remaining)"
        )

    try:
        choice = int(input("\nAssignment number: "))

        if not 1 <= choice <= len(unfinished):
            print("Invalid selection.")
            return

        item = unfinished[choice - 1]
        minutes = int(input("Minutes studied this session: "))

        if minutes < 0:
            print("Minutes cannot be negative.")
            return

        result = update_progress(item["id"], minutes)

        print(f"\nSaved: {result['title']}")
        print(f"Status: {result['status']}")
        print(f"Completed: {result['completed_minutes']} minutes")
        print(f"Remaining: {result['remaining_minutes']} minutes")

    except ValueError:
        print("Please enter a valid whole number.")


async def ask_agent(user_request):
    """Run the bounded reason-act-observe agent loop."""

    client = CopilotClient()

    try:
        await client.start()

        session = await client.create_session(
            model="auto",
            system_message={
                "mode": "append",
                "content": SYSTEM_MESSAGE,
            },
        )

        prompt = (
            f"USER REQUEST:\n{user_request}\n\n"
            "Decide what information you need first. "
            "Return exactly one ACTION or FINAL."
        )

        print("\nAnalyzing your assignments...")

        empty_retries = 0
        recommendation_request = (
            user_request.startswith("I have ")
            and "Recommend three ranked options" in user_request
        )

        for step in range(1, MAX_STEPS + 1):
            response = await session.send_and_wait(prompt)

            if not response or not response.data:
                response_text = ""
            else:
                response_text = response.data.content or ""

            action_type, result = parse_action(response_text)

            if action_type == "FINAL":
                if (
                    recommendation_request
                    and not validate_recommendations(result)
                ):
                    empty_retries += 1

                    if empty_retries > MAX_EMPTY_RETRIES:
                            print(
                                "\nThe AI did not return three numbered "
                                "recommendations."
                            )
                            print("\nDEBUG: Last AI answer:")
                            print(result)
                            print("\nPlease try again with a narrower request.")
                            return

                    prompt = (
                        "Your previous answer was incomplete. "
                        "Return three numbered study recommendations "
                        "when possible. Include assignment title, "
                        "course, study duration, remaining work, "
                        "deadline, and reason. Use actual assignment "
                        "data already retrieved. If more facts are "
                        "needed, call an available tool. "
                        "Return exactly one ACTION or FINAL. "
                        "Do not return only an introduction."
                    )
                    continue

                print("\n" + "=" * 40)
                print("RESULT")
                print("=" * 40 + "\n")
                print(result)
                print()
                return

            if action_type == "EMPTY_FINAL":
                empty_retries += 1

                if empty_retries > MAX_EMPTY_RETRIES:
                    print(
                        "\nThe AI repeatedly returned an empty final "
                        "answer. Please try again."
                    )
                    return

                prompt = (
                    "Your previous FINAL response was empty. "
                    "Continue using the information already available. "
                    "If more facts are needed, return a valid ACTION. "
                    "Otherwise return FINAL: followed by a complete "
                    "non-empty answer. Do not return an empty FINAL."
                )
                continue

            if action_type == "ERROR":
                print("\nThe agent response could not be read.")
                print(result)

                if response_text:
                    print("\nRaw response:")
                    print(response_text[:1000])

                print("\nPlease try again.")
                return

            tool_name = result["tool"]
            args = result["args"]

            try:
                tool_result = run_tool(tool_name, args)
            except Exception as error:
                tool_result = {
                    "error": f"Tool execution failed: {error}"
                }

            prompt = (
                f"TOOL OBSERVATION: {tool_name}\n"
                f"{json.dumps(tool_result, indent=2, default=str)}\n\n"
                "Interpret these facts. Decide whether another tool "
                "call is needed or whether you can finish. "
                "Return exactly one ACTION or FINAL. "
                "Do not repeat completed work. Check arithmetic. "
                "FINAL must contain a complete, non-empty answer."
            )

        print(
            "\nThe agent reached its step limit without a final answer. "
            "Try a narrower question."
        )

    except Exception as error:
        print(f"\nAgent error: {error}")
        print("Check your Copilot installation and authentication.")

    finally:
        await client.stop()


async def main():
    print("\n" + "=" * 40)
    print("       ASSIGNMENT PLANNING AGENT")
    print("=" * 40)
    print("1. What should I work on right now? (3 recommendations)")
    print("2. Plan my next 7 days")
    print("3. Update my progress")
    print("4. Show all assignments and deadlines")

    choice = input("\nChoose 1, 2, 3, or 4: ").strip()

    if choice not in {"1", "2", "3", "4"}:
        print("Please choose 1, 2, 3, or 4.")
        return

    if choice == "4":
        show_assignments(get_assignments())
        return

    if choice == "3":
        update_assignment_progress(get_assignments())
        return

    if choice == "2":
        request = (
            "Create a complete study plan for the next seven calendar "
            "days starting today. First retrieve the current date and "
            "assignments using tools. Use actual tool results. "
            "Schedule each unfinished assignment's full remaining "
            "minutes in one session, at most once, and before its "
            "deadline. Do not invent available study hours. "
            "Show each date, assignment, course, duration, and deadline. "
            "Calculate every daily total and the weekly grand total. "
            "List unschedulable assignments as conflicts. "
            "Return the complete daily schedule, not just an introduction."
        )
        await ask_agent(request)
        return

    if choice == "1":
        try:
            minutes = int(input("\nHow many minutes can you study? "))

            if minutes <= 0:
                print("Enter a number greater than zero.")
                return

        except ValueError:
            print("Enter a valid whole number.")
            return

        request = (
            f"I have {minutes} minutes available to study. "
            "Retrieve the current date and assignment data using tools. "
            "Recommend three ranked options when possible. "
            "Consider deadlines, remaining minutes, progress, and "
            "priority. Distinguish between assignments that can be "
            "completed in the available time and useful partial sessions. "
            "Do not claim partial work will finish an assignment. "
            "Explain why each recommendation is appropriate and "
            "identify urgent deadline risks."
        )

        await ask_agent(request)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped.")