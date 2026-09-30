"""
Offline end-to-end test of AgentsVille_Trip_Planner.ipynb.

Runs every code cell of the notebook with the OpenAI client replaced by a scripted
fake LLM, so the Python plumbing (Pydantic models, evals, tools, the ReAct loop)
is tested without an API key. It does NOT test the quality of the real LLM's answers.

Run with:  python -m pytest tests -q
"""
import json
import pathlib
import types

import nbformat
import openai

from project_lib import call_activity_by_id_api_mocked

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _plan(days, total):
    return {
        "city": "AgentsVille", "start_date": "2025-06-10", "end_date": "2025-06-12",
        "total_cost": total,
        "itinerary_days": [
            {"date": date, "weather": weather,
             "activity_recommendations": [
                 {"activity": call_activity_by_id_api_mocked(aid), "reasons_for_recommendation": ["test"]}
                 for aid in ids]}
            for date, weather, ids in days
        ],
    }


W1 = {"temperature": 25, "temperature_unit": "celsius", "condition": "sunny"}
W2 = {"temperature": 18, "temperature_unit": "celsius", "condition": "thunderstorm"}
W3 = {"temperature": 21, "temperature_unit": "celsius", "condition": "partly cloudy"}

# First draft: one activity per day and a hike during a thunderstorm -> should fail evals.
DRAFT = _plan([("2025-06-10", W1, ["event-2025-06-10-0"]),
               ("2025-06-11", W2, ["event-2025-06-11-0"]),
               ("2025-06-12", W3, ["event-2025-06-12-1"])], 35)
# Revised plan: two activities per day, indoor on the stormy day -> should pass evals.
FIXED = _plan([("2025-06-10", W1, ["event-2025-06-10-0", "event-2025-06-10-1"]),
               ("2025-06-11", W2, ["event-2025-06-11-1", "event-2025-06-11-2"]),
               ("2025-06-12", W3, ["event-2025-06-12-0", "event-2025-06-12-1"])], 100)

AGENT_SCRIPT = [
    # Tries to finish too early -> the loop must refuse (run_evals_tool not called yet).
    {"tool_name": "final_answer_tool", "arguments": {"final_output": FIXED}},
    {"tool_name": "get_activities_by_date_tool", "arguments": {"date": "2025-06-11", "city": "AgentsVille"}},
    {"tool_name": "calculator_tool", "arguments": {"input_expression": "15 + 5 + 25 + 15 + 30 + 10"}},
    {"tool_name": "run_evals_tool", "arguments": {"travel_plan": FIXED}},
    {"tool_name": "final_answer_tool", "arguments": {"final_output": FIXED}},
]
OBSERVATIONS = []


def fake_llm(messages):
    system, last = messages[0]["content"], messages[-1]["content"]
    if "expert travel planner" in system:
        return "## Analysis\nthinking...\n\n## Final Output\n```json\n" + json.dumps(DRAFT) + "\n```"
    if "event-safety and weather analyst" in system:
        activity, weather = last.split("\nWeather: ")
        bad = "thunderstorm" in weather and "(outdoor)" in activity
        return f"REASONING: test\nFINAL ANSWER: {'IS_INCOMPATIBLE' if bad else 'IS_COMPATIBLE'}"
    if "quality reviewer" in system:
        plan = json.loads(last.split("Itinerary:\n", 1)[1])
        ok = all(len(d["activity_recommendations"]) >= 2 for d in plan["itinerary_days"])
        return f"REASONING: test\nFINAL ANSWER: {'IS_INCORPORATED' if ok else 'IS_NOT_INCORPORATED'}"
    if "itinerary revision specialist" in system:
        if last.startswith("OBSERVATION:"):
            OBSERVATIONS.append(last)
        step = sum(m["role"] == "assistant" for m in messages)
        return "THINK:\nworking on it\n\nACTION:\n" + json.dumps(AGENT_SCRIPT[step])
    raise AssertionError(f"Unexpected system prompt: {system[:80]}")


class FakeOpenAI:
    def __init__(self, *args, **kwargs):
        create = lambda **kw: types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=fake_llm(kw["messages"])))])
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=create))


def test_notebook_runs_end_to_end(monkeypatch):
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    monkeypatch.chdir(ROOT)
    nb = nbformat.read(ROOT / "AgentsVille_Trip_Planner.ipynb", as_version=4)
    ns = {"__name__": "__main__"}
    for cell in nb.cells:
        if cell.cell_type == "code":
            exec(compile(cell.source, "<notebook>", "exec"), ns)

    # Stage 1: the draft is parsed into a TravelPlan and the evals catch its problems.
    assert not ns["eval_results_1"].success
    failures = " ".join(ns["eval_results_1"].failures)
    assert "Sunrise Summit Hike" in failures

    # Stage 2: the ReAct loop refused the early final answer, ran the tools, and returned the fix.
    assert "must call run_evals_tool before final_answer_tool" in OBSERVATIONS[0]
    assert '"success": true' in OBSERVATIONS[-1]
    assert ns["final_eval_results"].success
    assert ns["travel_plan_2"].total_cost == 100

    # Rubric checks on the prompts.
    revision_prompt = ns["ITINERARY_REVISION_AGENT_SYSTEM_PROMPT"]
    for tool in ("calculator_tool", "get_activities_by_date_tool", "run_evals_tool", "final_answer_tool"):
        assert tool in revision_prompt
    assert '{"tool_name": "[tool_name]", "arguments": {"arg1": "value1", ...}}' in revision_prompt
    schema_marker = '"title": "TravelPlan"'
    assert schema_marker in revision_prompt and schema_marker in ns["ITINERARY_AGENT_SYSTEM_PROMPT"]


def test_calculator_is_safe():
    nb = nbformat.read(ROOT / "AgentsVille_Trip_Planner.ipynb", as_version=4)
    tool_cell = next(c.source for c in nb.cells if "def calculator_tool" in c.source)
    ns = {"TravelPlan": object, "List": list, "Callable": object}
    exec("import ast, operator, datetime, inspect\n" + tool_cell.split("def run_evals_tool")[0], ns)
    assert ns["calculator_tool"]("15 + 5 * (2 + 1)") == 30.0
    try:
        ns["calculator_tool"]("__import__('os').system('ls')")
    except ValueError:
        pass
    else:
        raise AssertionError("calculator_tool must reject non-arithmetic input")
