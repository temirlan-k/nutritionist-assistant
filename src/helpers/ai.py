import os

from openai import AsyncOpenAI


class AI:

    def __init__(self):
        self.openai = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            timeout=360,
        )

    async def get_response(self, system_message, user_message=None):
        openai_response = await self.openai.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "system", "content": system_message}],
        )

        return openai_response.choices[0].message.content
