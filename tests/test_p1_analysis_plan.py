# -*- coding: utf-8 -*-
"""P1 analysis-plan migration tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORCH_ROOT = ROOT / "agents" / "strategy-orchestrator"
if str(ORCH_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCH_ROOT))

from evidence.evidence_ledger import Evidence  # noqa: E402
from executors.orchestrator import StrategyOrchestrator  # noqa: E402
from planning.analysis_plan import build_analysis_plan  # noqa: E402
from protocols.task_protocol import create_task_from_user_query  # noqa: E402


class P1AnalysisPlanTest(unittest.TestCase):
    def test_analysis_plan_normalizes_brand_and_time_range(self) -> None:
        task = create_task_from_user_query(
            "小米汽车近半年进入中国新能源SUV市场机会分析",
            time_range="最近12个月",
            entities=["小米"],
        )

        plan = build_analysis_plan(task)

        self.assertEqual(plan.target_brand, "小米")
        self.assertEqual(plan.time_range, "最近6个月")
        self.assertIn("小米", plan.brand_aliases)
        self.assertIn("新能源SUV", plan.market_scope)
        self.assertIn("小米", plan.rag_query)
        self.assertIn("最近6个月", plan.tavily_query)

    def test_orchestrator_tools_share_analysis_plan_and_emit_drw_store(self) -> None:
        orchestrator = StrategyOrchestrator()
        seen = []

        def assert_plan(task, state):
            self.assertIsNotNone(state.analysis_plan)
            self.assertEqual(state.analysis_plan.target_brand, "小米")
            self.assertEqual(state.analysis_plan.time_range, "最近6个月")
            self.assertIn("新能源SUV", state.analysis_plan.market_scope)
            seen.append(state.analysis_plan.to_dict())

        def fake_nl2sql(param, task, state):
            assert_plan(task, state)
            return {
                "evidence": Evidence(
                    source="nl2sql-pg",
                    tool="fake_market_db",
                    claim="结构化数据查询: 小米销量与份额",
                    content="小米最近6个月销量120000辆，覆盖SU7/YU7",
                    time_range=state.analysis_plan.time_range,
                    data_caliber="乘用车结构化销量数据库口径",
                    metrics=["销量", "份额", "趋势", "车型", "动力", "价格"],
                    coverage_dimensions=["时间范围", "口径"],
                    coverage_score=0.9,
                    source_credibility=0.88,
                    confidence=0.86,
                )
            }

        def fake_rag(param, task, state):
            assert_plan(task, state)
            self.assertIn("小米", state.analysis_plan.rag_query)
            return {
                "evidence": Evidence(
                    source="rag",
                    tool="fake_vector_retriever",
                    claim="RAG 检索: 小米战略背景",
                    content="小米汽车相关业务文档支持品牌进入策略分析",
                    time_range=f"用户问题时间范围: {state.analysis_plan.time_range}；文档发布日期以元数据为准",
                    data_caliber="向量检索文档摘要口径",
                    coverage_dimensions=["行业报告", "趋势解释"],
                    coverage_score=0.7,
                    source_credibility=0.72,
                    confidence=0.72,
                )
            }

        def fake_web(param, task, state):
            assert_plan(task, state)
            self.assertIn("小米", state.analysis_plan.tavily_query)
            return {
                "evidences": [
                    Evidence(
                        source="web-search",
                        tool="fake_tavily",
                        claim="Tavily 外部补证: 小米交付动态",
                        content="title=小米汽车交付动态; url=https://www.mi.com/auto/news; date=2026-06; source_grade=A; rejection_reason=accepted",
                        time_range=f"{state.analysis_plan.time_range}; source_date=2026-06",
                        data_caliber="Tavily 外部网页检索口径；按实体匹配和来源等级过滤",
                        source_url="https://www.mi.com/auto/news",
                        source_date="2026-06",
                        source_credibility=0.85,
                        coverage_dimensions=["外部补证", "URL", "来源日期", "来源等级", "剔除原因"],
                        coverage_score=0.8,
                        confidence=0.78,
                    )
                ]
            }

        def fake_framework(param, task, state):
            assert_plan(task, state)
            return {
                "evidence": Evidence(
                    source="analysis-framework",
                    tool="swot",
                    claim="框架分析: 小米机会判断",
                    content="基于D/R/W证据形成SWOT判断",
                    time_range=state.analysis_plan.time_range,
                    data_caliber="基于已入账证据的分析框架推断",
                    coverage_dimensions=["推断", "战略框架"],
                    coverage_score=0.6,
                    source_credibility=0.60,
                    confidence=0.65,
                )
            }

        orchestrator.register_tool("nl2sql-pg", fake_nl2sql)
        orchestrator.register_tool("rag", fake_rag)
        orchestrator.register_tool("web-search", fake_web)
        orchestrator.register_tool("analysis-framework", fake_framework)

        task = create_task_from_user_query(
            "小米汽车近半年进入中国新能源SUV市场机会分析",
            time_range="最近12个月",
            entities=["小米"],
        )
        result = orchestrator.execute(task).to_dict()

        self.assertGreaterEqual(len(seen), 3)
        self.assertEqual(result["analysis_plan"]["target_brand"], "小米")
        self.assertEqual(result["analysis_plan"]["time_range"], "最近6个月")
        self.assertEqual(result["evidence_store"]["summary"]["structured"], 1)
        self.assertEqual(result["evidence_store"]["summary"]["rag"], 1)
        self.assertEqual(result["evidence_store"]["summary"]["web"], 1)
        self.assertEqual(result["evidence_store"]["D"][0]["id"], "D1")
        self.assertEqual(result["evidence_store"]["R"][0]["id"], "R1")
        self.assertEqual(result["evidence_store"]["W"][0]["id"], "W1")


if __name__ == "__main__":
    unittest.main()
