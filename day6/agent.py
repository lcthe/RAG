"""
agent.py - Day 6: Agent + RAG 集成
====================================
核心：Agent（决策层）+ Tools（工具集）

Agent 通过 ReAct 模式运行：
  思考(Reason) -> 行动(Act) -> 观察(Observe) -> 循环

内置工具：
  - RetrievalTool: 知识库检索（调用 Day5 RAG Pipeline）
  - CalculatorTool: 简单计算
  - ChatTool: 闲聊（直接回答，不检索）
"""

from __future__ import annotations
import os, sys, re, time, json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# 第一部分：Tool 抽象层
# ============================================================

@dataclass
class ToolResult:
    """工具执行结果。"""
    tool_name: str
    content: str
    success: bool = True
    latency_ms: float = 0.0

    def __repr__(self):
        preview = self.content[:60].replace("\n", " ")
        return f"ToolResult({self.tool_name}, success={self.success}, '{preview}...')"


class BaseTool(ABC):
    """工具基类，所有工具实现 execute() 方法。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，Agent 通过这个名字调用。"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，告诉 Agent 这个工具能做什么。"""
        pass

    @property
    def parameters_schema(self) -> str:
        """参数说明，告诉 Agent 怎么传参。"""
        return "无参数"

    @abstractmethod
    def execute(self, input_text: str) -> ToolResult:
        """执行工具，返回结果。"""
        pass

    def to_prompt(self) -> str:
        """转成 Prompt 格式，让 Agent 看到有哪些工具可用。"""
        return f"- {self.name}: {self.description}\n  参数: {self.parameters_schema}"


# ============================================================
# 第二部分：内置工具实现
# ============================================================

class ChatTool(BaseTool):
    """闲聊工具：直接回答，不查知识库。"""

    def __init__(self, llm):
        self._llm = llm

    @property
    def name(self) -> str:
        return "chat"

    @property
    def description(self) -> str:
        return "闲聊、问候、常识问答。当问题不涉及知识库内容时使用。"

    def execute(self, input_text: str) -> ToolResult:
        start = time.time()
        messages = [
            {"role": "system", "content": "你是一个友好的助手，直接回答用户问题，简洁自然。"},
            {"role": "user", "content": input_text},
        ]
        resp = self._llm.chat(messages)
        return ToolResult(
            tool_name=self.name, content=resp.content,
            latency_ms=(time.time() - start) * 1000)


class RetrievalTool(BaseTool):
    """知识库检索工具：调用 Day5 RAG Pipeline。"""

    def __init__(self, rag_pipeline):
        self._pipeline = rag_pipeline

    @property
    def name(self) -> str:
        return "retrieval"

    @property
    def description(self) -> str:
        return "从知识库中检索产品信息、技术文档、价格、规格等。当问题涉及具体产品或业务知识时使用。"

    def execute(self, input_text: str) -> ToolResult:
        start = time.time()
        result = self._pipeline.query(input_text, save_history=False)
        return ToolResult(
            tool_name=self.name, content=result.answer,
            latency_ms=(time.time() - start) * 1000)


class CalculatorTool(BaseTool):
    """计算器工具：执行数学运算。"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "数学计算。当问题涉及数字运算、价格计算、数量换算时使用。"

    @property
    def parameters_schema(self) -> str:
        return "数学表达式，如 '2999 * 10' 或 '899 + 699'"

    def execute(self, input_text: str) -> ToolResult:
        start = time.time()
        try:
            # 安全的数学表达式求值
            allowed = set("0123456789+-*/.() ")
            expr = input_text.strip()
            if not all(c in allowed for c in expr):
                return ToolResult(
                    tool_name=self.name, content=f"不支持的表达式: {expr}",
                    success=False, latency_ms=(time.time() - start) * 1000)
            result = eval(expr)
            return ToolResult(
                tool_name=self.name, content=f"{expr} = {result}",
                latency_ms=(time.time() - start) * 1000)
        except Exception as e:
            return ToolResult(
                tool_name=self.name, content=f"计算错误: {e}",
                success=False, latency_ms=(time.time() - start) * 1000)


# ============================================================
# 第三部分：Agent（ReAct 模式）
# ============================================================

@dataclass
class AgentStep:
    """Agent 的一步决策。"""
    thought: str        # Agent 的思考
    action: str         # 选择的工具名
    action_input: str   # 传给工具的输入
    observation: str    # 工具返回的结果
    step_num: int = 0


@dataclass
class AgentResponse:
    """Agent 完整响应。"""
    answer: str
    steps: list[AgentStep]
    total_latency_ms: float = 0.0

    def __repr__(self):
        return f"AgentResponse(steps={len(self.steps)}, latency={self.total_latency_ms:.0f}ms)"


class Agent:
    """
    ReAct Agent：Reasoning + Acting 循环。

    流程：
    1. 把用户问题 + 工具列表 + ReAct 指令发给 LLM
    2. LLM 返回思考过程和工具调用
    3. 执行工具，拿到结果
    4. 把结果反馈给 LLM，继续循环
    5. LLM 输出最终答案时停止

    最多循环 max_steps 轮，防止死循环。
    """

    REACT_PROMPT = """你是一个智能助手。你有以下工具可以使用：

{tool_descriptions}

请严格按以下格式回答：

如果需要调用工具：
Thought: <你的思考过程>
Action: <工具名，必须是上面列出的工具之一>
Action Input: <用户的原始问题或问题中的关键部分，不是工具名也不是参数说明>

如果不需要工具，直接回答：
Thought: <你的思考>
Final Answer: <你的回答>

规则：
1. Action 必须是 chat、retrieval、calculator 之一
2. 涉及产品、价格、规格的问题必须用 retrieval 工具
3. 涉及数学计算的问题必须用 calculator 工具
4. 闲聊直接用 Final Answer
5. 每次只输出一个 Action"""

    def __init__(self, llm, tools: list[BaseTool], max_steps: int = 5):
        self._llm = llm
        self._tools = {t.name: t for t in tools}
        self._max_steps = max_steps

    def run(self, query: str) -> AgentResponse:
        """执行 Agent ReAct 循环。"""
        start = time.time()
        steps = []

        # 构造工具描述
        tool_desc = "\n".join(t.to_prompt() for t in self._tools.values())

        # 初始消息
        messages = [
            {"role": "system", "content": self.REACT_PROMPT.format(tool_descriptions=tool_desc)},
            {"role": "user", "content": query},
        ]

        for step_num in range(1, self._max_steps + 1):
            # 让 LLM 思考
            resp = self._llm.chat(messages, temperature=0.1)
            output = resp.content

            # 解析输出
            thought = self._extract(output, "Thought")
            action = self._extract(output, "Action")
            action_input = self._extract(output, "Action Input")
            final_answer = self._extract(output, "Final Answer")

            # 如果输出 Final Answer，结束循环
            if final_answer:
                steps.append(AgentStep(
                    thought=thought or "直接回答",
                    action="final_answer",
                    action_input=final_answer,
                    observation="",
                    step_num=step_num,
                ))
                break

            # 如果没有 Action，让 LLM 重新输出
            if not action:
                messages.append({"role": "assistant", "content": output})
                messages.append({"role": "user", "content": "请按格式输出，使用 Action 或 Final Answer。"})
                continue

            # 执行工具
            tool = self._tools.get(action)
            if not tool:
                observation = f"工具 {action} 不存在。可用工具: {list(self._tools.keys())}"
            else:
                # 如果 action_input 为空或看起来不像有效输入，用原始 query
                effective_input = action_input
                if not effective_input or effective_input in ["无参数", "无", "N/A"]:
                    effective_input = query
                result = tool.execute(effective_input)
                observation = result.content

            # 记录步骤
            steps.append(AgentStep(
                thought=thought or "",
                action=action,
                action_input=action_input or query,
                observation=observation,
                step_num=step_num,
            ))

            # 把 LLM 输出和工具结果加入消息历史
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": f"工具 {action} 的结果:\n{observation}\n\n请继续思考，使用 Final Answer 输出最终答案。"})

        # 如果循环结束还没有 Final Answer，强制总结
        if not steps or steps[-1].action != "final_answer":
            messages.append({"role": "user", "content": "请根据以上信息，用 Final Answer 输出最终回答。"})
            resp = self._llm.chat(messages, temperature=0.1)
            final = self._extract(resp.content, "Final Answer") or resp.content
            steps.append(AgentStep(
                thought="总结", action="final_answer",
                action_input=final, observation="", step_num=len(steps)+1))

        # 提取最终答案
        answer = steps[-1].action_input if steps[-1].action == "final_answer" else "无法生成回答"

        return AgentResponse(
            answer=answer, steps=steps,
            total_latency_ms=(time.time() - start) * 1000)

    @staticmethod
    def _extract(text: str, marker: str) -> str:
        """从 LLM 输出中提取指定标记后的内容。"""
        # Try strict format first (marker: content on same line or multi-line)
        pattern = rf"{marker}:\s*(.+?)(?=\n(?:Thought|Action|Action Input|Final Answer):|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: look for marker followed by anything
        pattern2 = rf"{marker}:\s*(.+)"
        match2 = re.search(pattern2, text, re.MULTILINE)
        return match2.group(1).strip() if match2 else ""


# ============================================================
# 第四部分：工厂函数
# ============================================================

def create_agent(rag_pipeline=None, llm=None):
    """
    创建 Agent 实例，自动注册所有工具。

    Args:
        rag_pipeline: Day5 的 RAG Pipeline（可选，没有则不注册检索工具）
        llm: LLM 实例（可选，没有则自动选择）
    """
    # 导入 Day5 的 LLM
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day5"))
    from rag_pipeline import get_llm

    if llm is None:
        llm = get_llm("auto")

    tools = [ChatTool(llm), CalculatorTool()]

    if rag_pipeline:
        tools.append(RetrievalTool(rag_pipeline))

    return Agent(llm=llm, tools=tools)


# ============================================================
# 第五部分：Demo
# ============================================================

def demo():
    print("=" * 70)
    print("  Day 6 - Agent + RAG Demo")
    print("=" * 70)

    # 1. 初始化 RAG Pipeline
    print("\n--- 1. 初始化 RAG Pipeline ---")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day5"))
    from rag_pipeline import RAGPipeline

    pipeline = RAGPipeline(chunk_size=300, chunk_overlap=50)
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    pipeline.ingest(data_dir)

    # 2. 创建 Agent
    print("\n--- 2. 创建 Agent ---")
    agent = create_agent(rag_pipeline=pipeline)
    print(f"  工具: {list(agent._tools.keys())}")

    # 3. 测试各种场景
    test_cases = [
        ("闲聊", "你好，你是谁？"),
        ("知识库检索", "ZY-SP100 的价格是多少？"),
        ("计算", "899 * 10 等于多少？"),
        ("多步推理", "ZY-SP100 单价多少？10台多少钱？"),
        ("知识库+计算", "ZY-SP100 首发优惠价是多少？买5台打9折，总价多少？"),
    ]

    for category, query in test_cases:
        print(f"\n{'='*70}")
        print(f"  [{category}] {query}")
        print(f"{'='*70}")

        result = agent.run(query)

        for step in result.steps:
            print(f"\n  Step {step.step_num}:")
            print(f"    Thought: {step.thought}")
            if step.action != "final_answer":
                print(f"    Action: {step.action}({step.action_input[:50]})")
                print(f"    Observation: {step.observation[:100]}...")
            else:
                print(f"    Final Answer: {step.action_input}")

        print(f"\n  --- 最终回答 ---")
        print(f"  {result.answer}")
        print(f"  [耗时 {result.total_latency_ms:.0f}ms, {len(result.steps)} 步]")


if __name__ == "__main__":
    demo()
