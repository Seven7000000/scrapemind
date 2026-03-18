from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import os

app = FastAPI(title="ScrapeMind")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-sonnet-4-20250514"


class AnalyzeRequest(BaseModel):
    url: str
    analysis_type: str = "summary"  # summary, key_points, sentiment, full


def scrape_url(url: str) -> dict:
    """Scrape content from a URL."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=400, detail="Could not connect to the URL")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request to URL timed out")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"HTTP error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script, style, nav, footer, header elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Get meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    # Extract main content
    main_content = soup.find("main") or soup.find("article") or soup.find("body")
    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Get links
    links = []
    for a in soup.find_all("a", href=True)[:20]:
        href = a["href"]
        link_text = a.get_text(strip=True)[:80]
        if href.startswith("http") and link_text:
            links.append({"text": link_text, "url": href})

    # Get headings
    headings = []
    for h in soup.find_all(["h1", "h2", "h3"])[:15]:
        headings.append({"level": h.name, "text": h.get_text(strip=True)[:100]})

    return {
        "title": title,
        "meta_description": meta_desc,
        "text": text[:30000],  # Limit to 30k chars
        "headings": headings,
        "links": links,
        "word_count": len(text.split()),
    }


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    # Scrape the page
    scraped = scrape_url(req.url.strip())

    if not scraped["text"].strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the page")

    # Build analysis prompt
    content_preview = scraped["text"][:20000]
    headings_text = "\n".join([f"  {h['level']}: {h['text']}" for h in scraped["headings"]])

    system_prompt = (
        "You are ScrapeMind, an expert web content analyst. "
        "Analyze the provided web page content thoroughly. "
        "Respond in well-structured markdown format."
    )

    if req.analysis_type == "summary":
        user_prompt = (
            f"Analyze this web page and provide:\n\n"
            f"## Summary\nA concise 2-3 paragraph summary of the page content.\n\n"
            f"## Key Points\n5-8 bullet points of the most important information.\n\n"
            f"## Target Audience\nWho is this content aimed at?\n\n"
            f"## Content Quality\nBrief assessment of writing quality, structure, and completeness.\n\n"
            f"---\n\n"
            f"Page Title: {scraped['title']}\n"
            f"Meta Description: {scraped['meta_description']}\n"
            f"Headings:\n{headings_text}\n\n"
            f"Content:\n{content_preview}"
        )
    elif req.analysis_type == "key_points":
        user_prompt = (
            f"Extract and organize ALL key points from this web page:\n\n"
            f"## Main Topic\nWhat is this page about?\n\n"
            f"## Key Facts & Data\nList every important fact, statistic, or data point.\n\n"
            f"## Key Arguments\nList the main arguments or claims made.\n\n"
            f"## Action Items\nAny recommendations or calls to action.\n\n"
            f"---\n\nPage Title: {scraped['title']}\nContent:\n{content_preview}"
        )
    elif req.analysis_type == "sentiment":
        user_prompt = (
            f"Perform a sentiment and tone analysis on this web page:\n\n"
            f"## Overall Sentiment\nPositive/Negative/Neutral with a score (1-10)\n\n"
            f"## Tone Analysis\nDescribe the writing tone (formal, casual, persuasive, etc.)\n\n"
            f"## Emotional Triggers\nIdentify emotional language or persuasion techniques used.\n\n"
            f"## Bias Detection\nNote any potential bias or one-sided arguments.\n\n"
            f"## Credibility Assessment\nRate the credibility of the content.\n\n"
            f"---\n\nPage Title: {scraped['title']}\nContent:\n{content_preview}"
        )
    else:  # full
        user_prompt = (
            f"Perform a COMPREHENSIVE analysis of this web page:\n\n"
            f"## Summary\nConcise 2-3 paragraph summary.\n\n"
            f"## Key Points\n8-12 bullet points of critical information.\n\n"
            f"## Sentiment & Tone\nOverall sentiment, writing tone, and persuasion techniques.\n\n"
            f"## SEO Assessment\nTitle quality, meta description, heading structure, keyword usage.\n\n"
            f"## Target Audience\nWho is this for and what's the intent?\n\n"
            f"## Strengths & Weaknesses\nWhat works well and what could be improved.\n\n"
            f"## Recommendations\n3-5 actionable recommendations.\n\n"
            f"---\n\n"
            f"Page Title: {scraped['title']}\n"
            f"Meta Description: {scraped['meta_description']}\n"
            f"Headings:\n{headings_text}\n\n"
            f"Content:\n{content_preview}"
        )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": MODEL, "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ], "max_tokens": 3000},
            timeout=60,
        )
        response.raise_for_status()
        analysis = response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI analysis timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    return {
        "url": req.url,
        "title": scraped["title"],
        "meta_description": scraped["meta_description"],
        "word_count": scraped["word_count"],
        "headings_count": len(scraped["headings"]),
        "links_count": len(scraped["links"]),
        "analysis": analysis,
        "headings": scraped["headings"],
    }


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
