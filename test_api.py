from openai import OpenAI


def get_response(model="qwen/qwen-vl-plus:free", system_prompt="You are a helpful AI assistant.", user_prompt="Who are you?"):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return completion.choices[0].message.content


if __name__ == "__main__":
    # model = "qwen/qwq-32b:free"
    # model = "meta-llama/llama-3.3-70b-instruct:free"
    model = "deepseek/deepseek-r1-distill-llama-70b:free"
    # model = "mistralai/mistral-7b-instruct:free"
    # model = "google/gemma-2-9b-it:free"
    print(get_response(model=model))
