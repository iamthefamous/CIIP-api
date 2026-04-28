from __future__ import annotations

import json
from typing import Optional, Tuple

from anthropic import AsyncAnthropic

from app.utils.config import Settings


class AIService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = (
            AsyncAnthropic(api_key=settings.anthropic_api_key)
            if settings.anthropic_api_key
            else None
        )

    async def generate_summary_and_tags(self, content: str) -> Tuple[Optional[str], Optional[list]]:
        if not self.client:
            return None, None

        response = await self.client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=500,
            temperature=0.2,
            system=(
                "Return JSON with keys 'summary' (string) and 'tags' (array of strings) "
                "for the given opportunity content."
            ),
            messages=[{"role": "user", "content": content}],
        )
        text = response.content[0].text
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None, None
        summary = payload.get("summary")
        tags = payload.get("tags")
        return summary, tags
