import time

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI
)

import config


# ==================================================
# Qwen客户端
# ==================================================

client = OpenAI(
    api_key=config.QWEN_API_KEY,
    base_url=config.QWEN_BASE_URL,
    timeout=config.QWEN_API_TIMEOUT,
    max_retries=config.QWEN_MAX_RETRIES
)


def call_qwen(prompt):
    """调用Qwen，并保证网络异常不会无限等待。"""

    print(flush=True)
    print("=" * 60, flush=True)
    print("开始调用Qwen", flush=True)
    print(
        f"模型：{config.QWEN_MODEL}；"
        f"超时：{config.QWEN_API_TIMEOUT}秒；"
        f"自动重试：{config.QWEN_MAX_RETRIES}",
        flush=True
    )
    print("=" * 60, flush=True)

    start_time = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=config.QWEN_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=4000,
            extra_body={
                "enable_thinking": False
            }
        )

        if not response.choices:
            raise RuntimeError("Qwen响应中没有choices")

        content = response.choices[0].message.content
        if content is None or not str(content).strip():
            raise RuntimeError("Qwen返回内容为空")

        elapsed = time.perf_counter() - start_time
        print(
            f"[耗时] Qwen API总耗时：{elapsed:.3f}秒",
            flush=True
        )

        if getattr(response, "usage", None):
            usage = response.usage
            print(
                "[Token] 输入Token："
                f"{getattr(usage, 'prompt_tokens', 0)}",
                flush=True
            )
            print(
                "[Token] 输出Token："
                f"{getattr(usage, 'completion_tokens', 0)}",
                flush=True
            )
            print(
                "[Token] 总Token："
                f"{getattr(usage, 'total_tokens', 0)}",
                flush=True
            )

        print("=" * 60, flush=True)
        return str(content)

    except APITimeoutError as e:
        elapsed = time.perf_counter() - start_time
        raise RuntimeError(
            "Qwen API调用超时："
            f"超过{config.QWEN_API_TIMEOUT}秒；"
            f"实际等待{elapsed:.3f}秒"
        ) from e

    except APIConnectionError as e:
        elapsed = time.perf_counter() - start_time
        raise RuntimeError(
            "无法连接Qwen API："
            f"{config.QWEN_BASE_URL}；"
            f"等待{elapsed:.3f}秒"
        ) from e

    except APIStatusError as e:
        elapsed = time.perf_counter() - start_time
        response_text = ""
        if e.response is not None:
            response_text = e.response.text[:1000]
        raise RuntimeError(
            "Qwen API返回错误："
            f"HTTP {e.status_code}；"
            f"等待{elapsed:.3f}秒；"
            f"响应内容：{response_text}"
        ) from e

    except RuntimeError:
        raise

    except Exception as e:
        elapsed = time.perf_counter() - start_time
        raise RuntimeError(
            "Qwen调用失败："
            f"{type(e).__name__}: {e}；"
            f"等待{elapsed:.3f}秒"
        ) from e
