from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

completion = client.chat.completions.create(
#   model="qwen/qwen-vl-plus:free",
#   model="meta-llama/llama-3.3-70b-instruct:free",
#   model="deepseek/deepseek-r1-distill-llama-70b:free",
#   model="mistralai/mistral-7b-instruct:free",
  model="google/gemma-2-9b-it:free",
  messages=[
    {
      "role": "system",
      "content": "You are a helpful AI assistant."
    },
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)

print(completion.choices[0].message.content)
