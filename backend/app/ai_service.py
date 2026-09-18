import asyncio
import json

import httpx

from app.config import get_settings
from app.schemas import AnalysisPayload


settings = get_settings()
_semaphore = asyncio.Semaphore(settings.ai_concurrency)


class DeepSeekError(RuntimeError):
    pass


def _system_prompt(categories: list[str]) -> str:
    category_text = "、".join(categories)
    return f"""你是企业客户反馈分析助手。请只输出一个合法 JSON 对象，不要输出 Markdown 或解释。
问题分类只能从以下分类中选择：{category_text}、其他/待确认。

JSON 字段必须完整：
{{
  "summary": "不超过60字的问题摘要",
  "category": "分类",
  "subcategory": "更具体的子类，没有则为空字符串",
  "keywords": ["最多5个关键词"],
  "sentiment": "positive|neutral|negative",
  "severity": "low|medium|high|urgent",
  "user_impact": "对业务或使用流程的影响",
  "suggested_priority": "P0|P1|P2|P3",
  "confidence": 0.0,
  "information_missing": ["处理问题仍缺少的信息"]
}}

严重程度规则：urgent=重大服务中断、数据或安全风险；high=核心流程不可用；medium=部分受限但有替代方案；low=轻微体验问题。
优先级结合严重程度、反馈频次线索和时间敏感度判断。confidence 必须在 0 到 1 之间。"""


async def analyze_feedback(api_key: str, content: str, categories: list[str]) -> tuple[AnalysisPayload, str]:
    request_body = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": _system_prompt(categories)},
            {"role": "user", "content": f"请将下面的客户反馈分析为 JSON：\n\n{content}"},
        ],
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "temperature": 0.2,
        "max_tokens": 1200,
        "stream": False,
    }

    last_error: Exception | None = None
    async with _semaphore:
        for attempt in range(settings.ai_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
                    response = await client.post(
                        f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json=request_body,
                    )
                response.raise_for_status()
                payload = response.json()
                choice = payload["choices"][0]
                if choice.get("finish_reason") == "length":
                    raise DeepSeekError("AI 输出被截断")
                content_text = choice["message"].get("content")
                if not content_text or not content_text.strip():
                    raise DeepSeekError("AI 返回了空内容")
                parsed = AnalysisPayload.model_validate(json.loads(content_text))
                if parsed.category not in categories and parsed.category != "其他/待确认":
                    parsed.category = "其他/待确认"
                return parsed, content_text
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, DeepSeekError) as exc:
                last_error = exc
                if attempt < settings.ai_max_retries:
                    await asyncio.sleep(1.5 * (attempt + 1))

    raise DeepSeekError(f"DeepSeek 分析失败：{last_error}")
