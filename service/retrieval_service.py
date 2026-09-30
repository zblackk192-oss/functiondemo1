import json
import time
from typing import Any, Dict, List

import requests

import config


def _normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unique_texts(values):
    result = []
    seen = set()

    for value in values:
        text = _normalize_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)

    return result


def _parse_json_field(value, default):
    if isinstance(value, type(default)):
        return value
    if not isinstance(value, str) or not value.strip():
        return default

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return default

    return parsed if isinstance(parsed, type(default)) else default


def _append_function_semantics(parts, item):
    if not isinstance(item, dict):
        return

    event = item.get("event", {})
    sources = [item]
    if isinstance(event, dict):
        sources.append(event)

    for source in sources:
        for field in (
            "name", "actor", "action", "object", "effect",
            "trigger", "condition", "scenario", "constraint"
        ):
            parts.append(source.get(field, ""))

        for field in (
            "inputs", "outputs", "preconditions", "postconditions"
        ):
            parts.extend(_normalize_list(source.get(field, [])))


def build_knowledge_query_text(current_case: Dict[str, Any]):
    """优先使用问题原文；没有原文时才从当前模型生成关键词文本。"""

    if not isinstance(current_case, dict):
        current_case = {}

    max_chars = max(200, int(config.KNOWLEDGE_API_MAX_QUERY_CHARS))
    raw_text = _normalize_text(current_case.get("raw_text", ""))

    if raw_text:
        return raw_text[:max_chars]

    parts = [current_case.get("summary", "")]
    for collection_name in ("functions", "function_points", "events"):
        collection = current_case.get(collection_name, [])
        if not isinstance(collection, list):
            continue

        for item in collection:
            _append_function_semantics(parts, item)

    relations = current_case.get("relations", [])

    if not isinstance(relations, list):
        relations = []

    for relation in relations:
        if not isinstance(relation, dict):
            continue

        for field in (
            "source_name", "target_name", "relation_type", "evidence"
        ):
            parts.append(relation.get(field, ""))

    query_text = "\n".join(_unique_texts(parts))
    return query_text[:max_chars]


def _clamp_limit(value):
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = 20
    return max(1, min(100, limit))


def _get_query_option(current_case, field_name, default=""):
    if not isinstance(current_case, dict):
        current_case = {}

    query_options = current_case.get("knowledge_query", {})
    if not isinstance(query_options, dict):
        query_options = {}

    value = query_options.get(field_name)
    if value in (None, "", []):
        value = current_case.get(field_name)
    if value in (None, "", []):
        value = default
    return value


def build_knowledge_query_payload(
    current_case: Dict[str, Any],
    query_text: str,
    limit: int
):
    """
    构造POST /api/query请求体。

    text负责FTS5关键词召回；其余字段只作为结果过滤条件。
    不从功能语义中擅自推断过滤条件，避免过度过滤导致漏召回。
    """

    payload = {
        "text": query_text,
        "limit": _clamp_limit(limit)
    }

    optional_fields = {
        "architecture_id": _get_query_option(
            current_case,
            "architecture_id",
            config.KNOWLEDGE_API_ARCHITECTURE_ID
        ),
        "view_type": _get_query_option(
            current_case,
            "view_type",
            config.KNOWLEDGE_API_VIEW_TYPE
        ),
        "subgraph_id": _get_query_option(
            current_case,
            "subgraph_id",
            config.KNOWLEDGE_API_SUBGRAPH_ID
        ),
        "function": _get_query_option(
            current_case,
            "function",
            config.KNOWLEDGE_API_FUNCTION
        )
    }

    for field_name, value in optional_fields.items():
        text = _normalize_text(value)
        if text:
            payload[field_name] = text

    tags = _unique_texts(
        _normalize_list(
            _get_query_option(
                current_case,
                "tags",
                config.KNOWLEDGE_API_TAGS
            )
        )
    )
    if tags:
        payload["tags"] = tags

    return payload


def build_component_query_payload(component_name, category="", limit=10):
    """构造组件库查询请求；该请求不进入架构补全Prompt。"""

    component_name = _normalize_text(component_name)
    if not component_name:
        raise ValueError("component_name不能为空")

    payload = {
        "component_name": component_name,
        "limit": _clamp_limit(limit)
    }

    category = _normalize_text(category)
    if category:
        payload["category"] = category

    return payload


def _build_headers():
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    token = _normalize_text(config.KNOWLEDGE_API_TOKEN)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _request_knowledge_api(payload):
    api_url = _normalize_text(config.KNOWLEDGE_API_URL)
    if not api_url:
        raise RuntimeError("未配置KNOWLEDGE_API_URL")

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=_build_headers(),
            timeout=config.KNOWLEDGE_API_TIMEOUT
        )
        response.raise_for_status()
    except requests.Timeout as e:
        raise RuntimeError(f"知识库API请求超时：{api_url}") from e
    except requests.RequestException as e:
        response_body = ""
        if e.response is not None and e.response.text:
            response_body = e.response.text[:1000]
        raise RuntimeError(
            f"知识库API请求失败：{api_url}；"
            f"错误信息：{e}；响应内容：{response_body}"
        ) from e

    try:
        response_data = response.json()
    except ValueError as e:
        raise RuntimeError("知识库API响应不是合法JSON") from e

    if not isinstance(response_data, dict):
        raise RuntimeError("知识库API响应根节点必须是JSON对象")

    return response_data


def query_knowledge_components(component_name, category="", limit=10):
    """
    查询组件库并返回API原始JSON。

    组件响应结构尚未纳入当前架构补全数据模型，因此不把组件matches
    直接送入Prompt，避免把组件候选误当成已验证的功能架构方案。
    """

    payload = build_component_query_payload(
        component_name=component_name,
        category=(
            category
            or config.KNOWLEDGE_API_COMPONENT_CATEGORY
        ),
        limit=limit
    )
    return _request_knowledge_api(payload)


def _normalize_match(match, response_data, order):
    labels = _parse_json_field(match.get("labels_json", {}), {})
    scenarios = _parse_json_field(match.get("scenario_json", []), [])

    try:
        rank = float(match.get("rank", 0.0))
    except (TypeError, ValueError):
        rank = 0.0

    return {
        "match_order": order,
        "match_status": _normalize_text(response_data.get("status", "")),
        "knowledge_scope": _normalize_text(
            response_data.get("knowledge_scope", "architecture")
        ),
        "query_terms": _unique_texts(
            _normalize_list(response_data.get("terms", []))
        ),
        "subgraph_id": _normalize_text(match.get("subgraph_id", "")),
        "architecture_id": _normalize_text(match.get("architecture_id", "")),
        "view_id": _normalize_text(match.get("view_id", "")),
        "view_type": _normalize_text(match.get("view_type", "")),
        "view_title": _normalize_text(match.get("view_title", "")),
        "case_title": _normalize_text(match.get("case_title", "")),
        "title": _normalize_text(match.get("title", "")),
        "description": _normalize_text(match.get("description", "")),
        "labels": labels,
        "scenarios": _unique_texts(scenarios),
        "source_path": _normalize_text(match.get("source_path", "")),
        "rank": rank
    }


def retrieve_top_k_cases(current_case, db=None, k=None):
    """调用知识库POST /api/query并返回标准化matches。"""

    del db  # 兼容旧调用签名；新流程不再使用FAISS实例。

    start = time.perf_counter()
    top_k = _clamp_limit(
        k if k is not None else config.KNOWLEDGE_API_TOP_K
    )
    query_text = build_knowledge_query_text(current_case)

    if not query_text:
        print("[知识库API] 当前案例没有可检索文本")
        return []

    print("\n" + "=" * 60)
    print("开始调用知识库API")
    print(f"API：{config.KNOWLEDGE_API_URL}")
    print(f"limit：{top_k}")
    print(f"查询文本长度：{len(query_text)}")
    print("=" * 60)

    payload = build_knowledge_query_payload(
        current_case,
        query_text,
        top_k
    )

    print(
        "查询过滤："
        f"{json.dumps({key: value for key, value in payload.items() if key != 'text'}, ensure_ascii=False)}"
    )

    response_data = _request_knowledge_api(payload)
    matches = response_data.get("matches", [])

    if not isinstance(matches, list):
        raise RuntimeError("知识库API响应中的matches必须是数组")

    results = []
    seen = set()

    for order, match in enumerate(matches, start=1):
        if not isinstance(match, dict):
            continue

        normalized = _normalize_match(match, response_data, order)
        dedupe_key = normalized.get("subgraph_id") or (
            normalized.get("architecture_id"),
            normalized.get("view_id"),
            normalized.get("title")
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        results.append(normalized)

        if len(results) >= top_k:
            break

    for item in results:
        print(
            "[知识库命中] "
            f"Top-{item.get('match_order', '')} | "
            f"{item.get('subgraph_id', '')} | "
            f"{item.get('title', '')} | "
            f"rank={item.get('rank', 0.0)}"
        )

    print(
        "[知识库API] "
        f"status={response_data.get('status', '')}，"
        f"scope={response_data.get('knowledge_scope', '')}，"
        f"terms={response_data.get('terms', [])}，"
        f"matches={len(results)}"
    )
    print(f"[耗时] 知识库API检索：{time.perf_counter() - start:.3f}秒")

    return results


def build_case_vector_database(history_cases: List[Dict[str, Any]]):
    """兼容旧导入路径；本地JSON/BGE/FAISS建库已经停用。"""

    del history_cases
    raise RuntimeError(
        "本地历史JSON/BGE/FAISS建库流程已停用，"
        "请使用KNOWLEDGE_API_URL配置的知识库API"
    )
