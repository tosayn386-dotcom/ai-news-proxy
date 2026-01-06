import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def summarize_vi(text):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Bạn là nhà báo AI, viết tiếng Việt tự nhiên, không máy móc."},
            {"role": "user", "content": text}
        ]
    )
    return resp.choices[0].message.content.strip()
if __name__ == "__main__":
    print(summarize_vi("AI đang thay đổi thế giới như thế nào?"))

