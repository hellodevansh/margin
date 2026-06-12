import json
from copy import deepcopy

import httpx

from app.fixtures.demo_data import STRATEGIES
from app.models.schemas import Strategy
from app.services.detection import gate_strategy
from app.settings import Settings
from pydantic import BaseModel


class StrategyBundle(BaseModel):
    strategies: list[Strategy]


def _strict_json_schema(schema: dict) -> dict:
    if schema.get("type") == "object":
        schema["additionalProperties"] = False
    for value in schema.values():
        if isinstance(value, dict):
            _strict_json_schema(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _strict_json_schema(item)
    return schema


def _gated(strategies: list[Strategy]) -> list[Strategy]:
    for strategy in strategies:
        strategy.approved = gate_strategy(strategy)
        strategy.gate_result = "execute" if strategy.approved else "human_review"
    return strategies


async def generate_and_evaluate(settings: Settings, context: dict) -> tuple[list[Strategy], str, dict[str, int]]:
    fallback = _gated(deepcopy(STRATEGIES))
    if not settings.anthropic_api_key:
        return fallback, "fixture", {}

    try:
        from anthropic import AsyncAnthropic

        async with httpx.AsyncClient(trust_env=False, timeout=15.0) as http_client:
            client = AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                base_url=settings.anthropic_base_url,
                timeout=15.0,
                http_client=http_client,
            )
            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=3000,
                system=(
                    "You evaluate SaaS spend recovery strategies. Return JSON only. "
                    "Never alter supplied savings. Favor reversible actions and complete evidence."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Review these precomputed strategies and scores. Preserve their IDs, titles, "
                            "savings, and numeric scores. You may improve descriptions only. Return an array "
                            f"under the key strategies.\n{json.dumps([item.model_dump(mode='json') for item in fallback])}"
                        ),
                    }
                ],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": _strict_json_schema(StrategyBundle.model_json_schema()),
                    }
                },
            )
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        parsed = StrategyBundle.model_validate(json.loads(text))
        usage = {
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens,
        }
        return _gated(parsed.strategies), "anthropic", usage
    except Exception:
        return fallback, "fixture", {}
