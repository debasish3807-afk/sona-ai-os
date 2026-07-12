"""Planner, Function Calling, and Execution Engine tests."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIntentAnalyzer:
    """Test intent analysis."""

    def test_chat_intent_simple(self):
        from planner.intent import IntentAnalyzer, TaskIntent

        analyzer = IntentAnalyzer()
        result = analyzer.analyze("Hello, how are you?")
        assert result.intent == TaskIntent.CHAT
        assert result.requires_tools is False

    def test_file_intent(self):
        from planner.intent import IntentAnalyzer, TaskIntent

        analyzer = IntentAnalyzer()
        result = analyzer.analyze("Read the file config.py and show me its content")
        assert result.intent == TaskIntent.FILE_OPERATION
        assert result.requires_tools is True
        assert result.confidence > 0.2

    def test_git_intent(self):
        from planner.intent import IntentAnalyzer, TaskIntent

        analyzer = IntentAnalyzer()
        result = analyzer.analyze("Commit all changes and push to remote")
        assert result.intent in (TaskIntent.GIT_OPERATION, TaskIntent.MULTI_STEP)
        assert result.requires_tools is True

    def test_code_intent(self):
        from planner.intent import IntentAnalyzer, TaskIntent

        analyzer = IntentAnalyzer()
        result = analyzer.analyze("Run pytest to test the code")
        assert result.intent == TaskIntent.CODE_EXECUTION
        assert result.requires_tools is True

    def test_web_intent(self):
        from planner.intent import IntentAnalyzer, TaskIntent

        analyzer = IntentAnalyzer()
        result = analyzer.analyze("Search the web for Python async patterns")
        assert result.intent == TaskIntent.WEB_RESEARCH
        assert result.requires_tools is True

    def test_project_analysis_intent(self):
        from planner.intent import IntentAnalyzer, TaskIntent

        analyzer = IntentAnalyzer()
        result = analyzer.analyze("Analyze this project structure and summarize the codebase")
        assert result.intent == TaskIntent.PROJECT_ANALYSIS
        assert result.requires_tools is True

    def test_multi_step_intent(self):
        from planner.intent import IntentAnalyzer

        analyzer = IntentAnalyzer()
        result = analyzer.analyze(
            "First commit the changes, then push to remote, and finally create a PR"
        )
        assert result.requires_tools is True


class TestTaskPlanner:
    """Test plan creation."""

    def test_plan_git_commit(self):
        from planner.planner import TaskPlanner

        planner = TaskPlanner()
        plan = planner.create_plan("Commit all my changes with message 'fix: bug'")
        assert plan.step_count >= 2
        tool_names = [s.tool_name for s in plan.steps]
        assert "git_status" in tool_names
        assert "git_commit" in tool_names

    def test_plan_file_read(self):
        from planner.planner import TaskPlanner

        planner = TaskPlanner()
        plan = planner.create_plan("Read the file README.md")
        assert plan.step_count >= 1
        assert plan.steps[0].tool_name == "file_read"

    def test_plan_project_analysis(self):
        from planner.planner import TaskPlanner

        planner = TaskPlanner()
        plan = planner.create_plan("Analyze this project and summarize the codebase structure")
        assert plan.step_count >= 2

    def test_plan_no_tools_for_chat(self):
        from planner.planner import TaskPlanner

        planner = TaskPlanner()
        plan = planner.create_plan("What is the meaning of life?")
        assert plan.step_count == 0

    def test_plan_web_search(self):
        from planner.planner import TaskPlanner

        planner = TaskPlanner()
        plan = planner.create_plan("Search the web for FastAPI best practices")
        assert plan.step_count >= 1
        assert plan.steps[0].tool_name == "browser_search"


class TestExecutionPlan:
    """Test plan data structure."""

    def test_plan_creation(self):
        from planner.plan import ExecutionPlan

        plan = ExecutionPlan(description="Test plan")
        assert plan.step_count == 0
        assert plan.status.value == "created"

    def test_add_steps(self):
        from planner.plan import ExecutionPlan

        plan = ExecutionPlan(description="Test")
        s1 = plan.add_step("git_status", "Check status")
        s2 = plan.add_step("git_add", "Stage files", depends_on=[s1.step_id])
        assert plan.step_count == 2
        assert s2.depends_on == [s1.step_id]

    def test_get_next_step(self):
        from planner.plan import ExecutionPlan, StepStatus

        plan = ExecutionPlan()
        s1 = plan.add_step("tool_a", "Step A")
        s2 = plan.add_step("tool_b", "Step B", depends_on=[s1.step_id])

        # First step should be next
        nxt = plan.get_next_step()
        assert nxt is not None
        assert nxt.step_id == s1.step_id

        # After completing s1, s2 becomes available
        s1.status = StepStatus.COMPLETED
        nxt = plan.get_next_step()
        assert nxt is not None
        assert nxt.step_id == s2.step_id

    def test_plan_serialization(self):
        from planner.plan import ExecutionPlan

        plan = ExecutionPlan(description="Serialization test")
        plan.add_step("file_read", "Read a file", {"path": "test.py"})
        data = plan.to_dict()
        assert data["description"] == "Serialization test"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["tool_name"] == "file_read"


class TestFunctionCalling:
    """Test function call parsing and schema generation."""

    def test_openai_format_parsing(self):
        from function_calling.parser import parse_function_call

        call_data = {
            "id": "call_123",
            "function": {
                "name": "file_read",
                "arguments": '{"path": "/tmp/test.py"}',
            },
        }
        result = parse_function_call(call_data)
        assert result is not None
        assert result.name == "file_read"
        assert result.arguments["path"] == "/tmp/test.py"
        assert result.call_id == "call_123"

    def test_claude_format_parsing(self):
        from function_calling.parser import parse_function_call

        call_data = {
            "type": "tool_use",
            "id": "toolu_abc",
            "name": "terminal_exec",
            "input": {"command": "ls -la"},
        }
        result = parse_function_call(call_data)
        assert result is not None
        assert result.name == "terminal_exec"
        assert result.arguments["command"] == "ls -la"

    def test_gemini_format_parsing(self):
        from function_calling.parser import parse_function_call

        call_data = {
            "functionCall": {
                "name": "browser_fetch",
                "args": {"url": "https://example.com"},
            }
        }
        result = parse_function_call(call_data)
        assert result is not None
        assert result.name == "browser_fetch"
        assert result.arguments["url"] == "https://example.com"

    def test_schema_generation(self):
        from function_calling.schema import generate_tool_schemas
        from tools.base import ToolCategory, ToolMetadata, ToolParam

        tools = [
            ToolMetadata(
                name="test_tool",
                description="A test tool",
                category=ToolCategory.FILESYSTEM,
                parameters=[
                    ToolParam("path", "string", "File path"),
                    ToolParam("limit", "integer", "Max lines", required=False, default=100),
                ],
            )
        ]
        schemas = generate_tool_schemas(tools)
        assert len(schemas) == 1
        func = schemas[0]["function"]
        assert func["name"] == "test_tool"
        assert "path" in func["parameters"]["properties"]
        assert "path" in func["parameters"]["required"]
        assert "limit" not in func["parameters"]["required"]

    def test_validate_missing_params(self):
        from function_calling.parser import FunctionCall

        call = FunctionCall(name="file_read", arguments={"offset": 0})
        missing = call.validate_against(["path", "offset"])
        assert "path" in missing
        assert "offset" not in missing

    def test_parse_multiple_calls(self):
        from function_calling.parser import parse_multiple_calls

        calls = [
            {"function": {"name": "tool_a", "arguments": "{}"}},
            {"function": {"name": "tool_b", "arguments": '{"x": 1}'}},
        ]
        results = parse_multiple_calls(calls)
        assert len(results) == 2
        assert results[0].name == "tool_a"
        assert results[1].name == "tool_b"


class TestExecutionEngine:
    """Test execution engine."""

    def test_execute_simple_plan(self):
        from execution.engine import ExecutionEngine
        from planner.plan import ExecutionPlan

        plan = ExecutionPlan(description="Test execution")
        plan.add_step("list_dir", "List current directory", {"path": "."})

        engine = ExecutionEngine(max_step_timeout=10, max_plan_timeout=30)
        result = asyncio.run(engine.execute_plan(plan))

        assert result.steps_total == 1
        assert result.steps_completed == 1
        assert result.status == "completed"

    def test_execute_with_dependency(self):
        from execution.engine import ExecutionEngine
        from planner.plan import ExecutionPlan

        plan = ExecutionPlan(description="Dependency test")
        s1 = plan.add_step("list_dir", "List files", {"path": "."})
        plan.add_step("list_dir", "List again", {"path": "."}, depends_on=[s1.step_id])

        engine = ExecutionEngine(max_step_timeout=10)
        result = asyncio.run(engine.execute_plan(plan))

        assert result.steps_completed == 2
        assert result.status == "completed"

    def test_execute_nonexistent_tool(self):
        from execution.engine import ExecutionEngine
        from planner.plan import ExecutionPlan

        plan = ExecutionPlan(description="Failing plan")
        plan.add_step("nonexistent_tool_xyz", "This should fail", {})

        engine = ExecutionEngine(max_step_timeout=5)
        result = asyncio.run(engine.execute_plan(plan))

        assert result.steps_failed == 1
        assert result.status == "failed"
