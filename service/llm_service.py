from openai import OpenAI

import config


# ==================================================
# Qwen客户端
# ==================================================

client = OpenAI(
    api_key=config.QWEN_API_KEY,
    base_url=config.QWEN_BASE_URL
)


def call_qwen(prompt):

    print()
    print("=" * 60)
    print("开始调用Qwen")
    print("=" * 60)

    import time

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

            # 控制输出长度
            max_tokens=4000,

            # Qwen3.7关闭思考
            extra_body={
                "enable_thinking": False
            }
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            f"[耗时] Qwen API总耗时：{elapsed:.3f}秒"
        )

        # ==================================================
        # Token统计
        # ==================================================

        if hasattr(response, "usage") and response.usage:

            usage = response.usage

            print(
                f"[Token] 输入Token："
                f"{getattr(usage, 'prompt_tokens', 0)}"
            )

            print(
                f"[Token] 输出Token："
                f"{getattr(usage, 'completion_tokens', 0)}"
            )

            print(
                f"[Token] 总Token："
                f"{getattr(usage, 'total_tokens', 0)}"
            )

        print("=" * 60)

        return content

    except Exception as e:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            f"[错误] Qwen调用失败"
        )

        print(
            f"[耗时] Qwen调用失败耗时："
            f"{elapsed:.3f}秒"
        )

        print(
            f"[错误信息] {e}"
        )

        raise