import os
from datetime import datetime, timezone
from pathlib import Path


TEST_DB = Path(__file__).parent / "test_voc.db"
os.environ["VOC_DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas import AnalysisPayload  # noqa: E402


def setup_module() -> None:
    TEST_DB.unlink(missing_ok=True)


def teardown_module() -> None:
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)


def test_feedback_requires_initialized_session() -> None:
    with TestClient(app) as client:
        response = client.get("/api/feedbacks")
        assert response.status_code == 401


def test_create_and_list_feedback() -> None:
    with TestClient(app) as client:
        session_response = client.post(
            "/api/session",
            json={"operator_name": "测试人员", "api_key": "test-key"},
        )
        assert session_response.status_code == 200
        assert session_response.json()["operator_name"] == "测试人员"

        create_response = client.post(
            "/api/feedbacks",
            json={
                "content": "升级后无法导出 Excel 文件",
                "source": "售后记录",
                "feedback_time": datetime.now(timezone.utc).isoformat(),
                "product_module": "数据导出",
            },
        )
        assert create_response.status_code == 201
        assert create_response.json()["created_by_name"] == "测试人员"

        list_response = client.get("/api/feedbacks?keyword=Excel")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1
        assert list_response.json()["items"][0]["source"] == "售后记录"


def test_complete_analysis_to_issue_flow(monkeypatch) -> None:
    async def fake_analysis(api_key: str, content: str, categories: list[str]):
        assert api_key == "test-key"
        return AnalysisPayload(
            summary="升级后无法导出 Excel",
            category="功能异常",
            subcategory="数据导出",
            keywords=["Excel", "导出失败"],
            sentiment="negative",
            severity="high",
            user_impact="无法完成数据导出任务",
            suggested_priority="P1",
            confidence=0.91,
            information_missing=["产品版本"],
        ), '{"summary":"升级后无法导出 Excel"}'

    monkeypatch.setattr("app.analysis_tasks.analyze_feedback", fake_analysis)
    with TestClient(app) as client:
        client.post("/api/session", json={"operator_name": "产品团队", "api_key": "test-key"})
        created = client.post(
            "/api/feedbacks",
            json={
                "content": "系统升级以后 Excel 无法导出",
                "source": "售后记录",
                "feedback_time": datetime.now(timezone.utc).isoformat(),
            },
        ).json()

        analysis_response = client.post(f"/api/feedbacks/{created['id']}/analyze")
        assert analysis_response.status_code == 202
        feedback = client.get(f"/api/feedbacks/{created['id']}").json()
        assert feedback["analysis_status"] == "success"
        assert feedback["analysis"]["category"] == "功能异常"

        confirmed = client.put(
            f"/api/feedbacks/{created['id']}/analysis",
            json={**{key: feedback["analysis"][key] for key in [
                "summary", "category", "subcategory", "keywords", "sentiment", "severity",
                "user_impact", "suggested_priority", "confidence", "information_missing"
            ]}, "confirmed": True},
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["confirmed"] is True

        issue = client.post(
            "/api/issues",
            json={
                "feedback_id": created["id"],
                "title": feedback["analysis"]["summary"],
                "description": feedback["analysis"]["user_impact"],
                "category": feedback["analysis"]["category"],
                "severity": feedback["analysis"]["severity"],
                "priority": feedback["analysis"]["suggested_priority"],
            },
        )
        assert issue.status_code == 201
        issue_id = issue.json()["id"]
        assert issue.json()["feedback_count"] == 1

        completed = client.post(
            f"/api/issues/{issue_id}/complete",
            json={"solution": "回滚导出模块并发布修复版本"},
        )
        assert completed.status_code == 200
        assert completed.json()["status"] == "processed"
        assert completed.json()["processed_by_name"] == "产品团队"

        overview = client.get("/api/dashboard/overview")
        assert overview.status_code == 200
        assert overview.json()["issue_processed"] >= 1


def test_import_csv() -> None:
    with TestClient(app) as client:
        client.post("/api/session", json={"operator_name": "售后团队", "api_key": "test-key"})
        response = client.post(
            "/api/feedbacks/import",
            files={"file": ("feedbacks.csv", "反馈内容,来源\n页面加载很慢,售后记录\n权限配置无法保存,客服工单".encode("utf-8-sig"), "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["success"] == 2
        assert response.json()["failed"] == 0
