import json
import re

import httpx

from app.schemas import ExtractedInfo, LLMExtractionResult


class LLMExtractor:
    @staticmethod
    def _headers(api_key: str, provider: str) -> dict[str, str]:
        if provider == "bailian":
            return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _endpoint(base_url: str, provider: str) -> str:
        if provider == "bailian" and "compatible-mode" not in base_url:
            return f"{base_url.rstrip('/')}/compatible-mode/v1/chat/completions"
        return f"{base_url.rstrip('/')}/v1/chat/completions"

    @staticmethod
    def _system_prompt() -> str:
        return (
            "你是简历信息抽取器。输出必须是 JSON，字段为: "
            "name,phone,email,address,years_of_experience,education,intent,skills。"
            "skills 必须是字符串数组。无法提取填 null 或空数组。"
        )

    @staticmethod
    def _extract_json(text: str) -> dict:
        fenced = re.search(r"```json\s*(\{.*\})\s*```", text, re.S)
        if fenced:
            return json.loads(fenced.group(1))

        direct = re.search(r"(\{.*\})", text, re.S)
        if direct:
            return json.loads(direct.group(1))

        return {}

    @classmethod
    def extract(
        cls,
        text: str,
        provider: str,
        api_key: str,
        base_url: str,
        model: str,
        timeout_s: int = 30,
    ) -> LLMExtractionResult:
        payload = {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": cls._system_prompt()},
                {"role": "user", "content": text[:12000]},
            ],
        }

        endpoint = cls._endpoint(base_url, provider)
        headers = cls._headers(api_key, provider)
        response = httpx.post(endpoint, headers=headers, json=payload, timeout=timeout_s)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        parsed = cls._extract_json(content)
        extracted = ExtractedInfo(**{
            "name": parsed.get("name"),
            "phone": parsed.get("phone"),
            "email": parsed.get("email"),
            "address": parsed.get("address"),
            "years_of_experience": parsed.get("years_of_experience"),
            "education": parsed.get("education"),
            "intent": parsed.get("intent"),
            "skills": parsed.get("skills") or [],
        })
        return LLMExtractionResult(extracted=extracted, raw_response=content)
