import asyncio
from collections.abc import Awaitable, Callable

import httpx
from bs4 import BeautifulSoup

from app.fixtures.demo_data import RESEARCH_TARGETS
from app.models.schemas import ResearchActivity, ResearchFinding


ActivityCallback = Callable[[ResearchActivity], Awaitable[None]]


async def research_pricing(on_activity: ActivityCallback | None = None) -> tuple[list[ResearchFinding], list[ResearchActivity]]:
    activities: list[ResearchActivity] = []

    async def emit(activity: ResearchActivity) -> None:
        activities.append(activity)
        if on_activity:
            await on_activity(activity)
        await asyncio.sleep(0.08)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(5.0),
        trust_env=False,
        headers={"User-Agent": "Margin-Research-Agent/1.0"},
    ) as client:
        for index, target in enumerate(RESEARCH_TARGETS):
            await emit(
                ResearchActivity(
                    id=f"search-{index}",
                    kind="search",
                    status="running",
                    label=f"Searching {target['vendor']} pricing",
                    detail=target["query"],
                    vendor=target["vendor"],
                    query=target["query"],
                )
            )
            await emit(
                ResearchActivity(
                    id=f"navigate-{index}",
                    kind="navigate",
                    status="running",
                    label=f"Opening official {target['category'].lower()} source",
                    detail=target["url"],
                    vendor=target["vendor"],
                    query=target["query"],
                    url=target["url"],
                )
            )

        findings = await asyncio.gather(*[_fetch(client, target) for target in RESEARCH_TARGETS])

        for index, finding in enumerate(findings):
            await emit(
                ResearchActivity(
                    id=f"extract-{index}",
                    kind="extract",
                    status="completed" if finding.source_status == "live" else "cached",
                    label=f"Extracted {finding.vendor} pricing evidence",
                    detail=finding.evidence_excerpt or finding.finding,
                    vendor=finding.vendor,
                    query=finding.search_query,
                    url=finding.source_url,
                )
            )
            if finding.competitor:
                await emit(
                    ResearchActivity(
                        id=f"compare-{index}",
                        kind="compare",
                        status="completed",
                        label=f"Compared {finding.vendor} with {finding.competitor}",
                        detail=finding.finding,
                        vendor=finding.vendor,
                        query=finding.search_query,
                        url=finding.source_url,
                    )
                )
        await emit(
            ResearchActivity(
                id="cite-market-evidence",
                kind="cite",
                status="completed",
                label="Attached market evidence to decision context",
                detail=f"{len(findings)} official sources mapped to strategy evaluation and report citations.",
            )
        )
    return findings, activities


async def _fetch(client: httpx.AsyncClient, target: dict) -> ResearchFinding:
    status = "cached"
    page_title = f"{target['vendor']} pricing"
    excerpt = target["finding"]
    try:
        response = await client.get(target["url"])
        if response.status_code < 400 and len(response.text) > 500:
            status = "live"
            soup = BeautifulSoup(response.text, "html.parser")
            if soup.title and soup.title.string:
                page_title = " ".join(soup.title.string.split())[:140]
            text = " ".join(soup.get_text(" ", strip=True).split())
            excerpt = text[:220] if text else excerpt
    except httpx.HTTPError:
        pass
    return ResearchFinding(
        vendor=target["vendor"],
        competitor=target["competitor"],
        benchmark_price=target["benchmark"],
        source_url=target["url"],
        source_status=status,
        finding=target["finding"],
        category=target["category"],
        search_query=target["query"],
        page_title=page_title,
        evidence_excerpt=excerpt,
    )
