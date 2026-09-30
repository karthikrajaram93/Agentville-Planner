# AgentsVille Trip Planner

An AI travel assistant for the fictional city of **AgentsVille** (Udacity Agentic AI Nanodegree project).

It works in two stages:

1. **The Expert Planner.** An LLM acting as a travel planner reads the travelers' preferences, the
   weather forecast and the available activities. It reasons step by step, then returns a
   day-by-day itinerary as JSON, which is checked against the `TravelPlan` Pydantic model.
2. **The Resourceful Assistant.** A **ReAct agent** (THINK → ACT → OBSERVE) revises the itinerary
   to include traveler feedback ("at least two activities per day"). It uses tools to look up
   activities, calculate costs and run the evaluations, and it may only finish with
   `final_answer_tool` after `run_evals_tool` has been called.

## Files

| File | What it is |
|---|---|
| `AgentsVille_Trip_Planner.ipynb` | **The project.** Run the cells from top to bottom. |
| `project_lib.py` | A stand-in for Udacity's `project_lib.py` (the mocked weather and activity APIs). **In the Udacity workspace, use Udacity's own file.** |
| `tests/test_notebook_offline.py` | Runs the whole notebook against a fake LLM to check the code works without an API key. |

## How to run

In the Udacity workspace:

1. Copy the notebook into the project folder, next to Udacity's `project_lib.py`.
2. Set your Vocareum key: create a `.env` file containing `OPENAI_API_KEY=voc-...`, or set the
   environment variable. The notebook sends `voc-` keys through the Vocareum endpoint automatically.
3. Choose **Run All**. The last cell prints `🎉 The final itinerary passes every evaluation!`

Locally: `pip install -r requirements.txt`, then do the same. To run the offline tests:
`python -m pytest tests -q`.

## Rubric map

| Rubric item | Where in the notebook |
|---|---|
| `ITINERARY_AGENT_SYSTEM_PROMPT`: travel-planner role | Section 4, `## ROLE` |
| Chain-of-thought guidance and examples | Section 4, `## PLANNING PROCESS` (6 steps, written under `## Analysis`) plus an example itinerary day |
| JSON output matching `TravelPlan` | Section 4, `## OUTPUT FORMAT`, which includes `TravelPlan.model_json_schema()` |
| Context: `VacationInfo`, weather, activities | Section 4, `## CONTEXT` |
| `ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT`: role and task | Section 5, `## ROLE` and `## TASK` |
| Exact output format | Section 5, `REASONING: ...` / `FINAL ANSWER: IS_COMPATIBLE or IS_INCOMPATIBLE` |
| Examples | Section 5, five worked examples |
| `get_activities_by_date_tool` docstring | Section 7: purpose, when to use it, `date (str, "YYYY-MM-DD")`, `city (str)` and the return format |
| `ITINERARY_REVISION_AGENT_SYSTEM_PROMPT`: role and revision task | Section 8, `## ROLE` and `## TASK` |
| Explicit THINK-ACT-OBSERVE cycle | Section 8, `## HOW YOU WORK` |
| All tools, their purposes and parameters (added dynamically) | Section 8, `## AVAILABLE TOOLS`, built by `get_tool_descriptions_string(ALL_TOOLS)` |
| Exact ACTION format | Section 8, `{"tool_name": "[tool_name]", "arguments": {"arg1": "value1", ...}}` |
| Exit through `final_answer_tool` | Section 8, `## EXIT INSTRUCTIONS` |
| `run_evals_tool` before `final_answer_tool` | Section 8, `## EXIT INSTRUCTIONS` (the ReAct loop also enforces it in code) |
| `VacationInfo` model built from the JSON | Section 1, `Traveler` and `VacationInfo` |
| Start and end dates read from `VacationInfo` for the weather and activity data | Section 2, `get_trip_dates(vacation_info)` |
| `TravelPlan` schema in the system prompts | Both Section 4 and Section 8 include `TRAVEL_PLAN_SCHEMA` |

## Key concepts, in plain English

- **System prompt**: standing instructions that set the LLM's role, rules and output format.
- **Chain-of-thought**: asking the model to reason step by step before answering, which makes
  complex plans more accurate.
- **Pydantic model**: a Python class that defines the shape data must have. It rejects bad data
  (a wrong date format, a missing field) immediately.
- **Structured output**: making the LLM answer in JSON that matches a schema, so code can use the answer.
- **Tool**: a Python function the agent can ask to run. The agent only sees the function's name,
  parameters and docstring, so the docstring acts as the tool's instruction manual.
- **ReAct**: *Reason + Act*. The agent thinks, calls one tool, reads the result (the
  "observation") and repeats until the job is done.
- **Evals**: automatic checks, some in plain Python and some judged by an LLM, that catch mistakes
  such as a wrong total cost, an invented event or an outdoor hike during a thunderstorm.
