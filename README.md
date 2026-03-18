# ScrapeMind

Enter any URL and get instant AI-powered content analysis -- summaries, key points, sentiment, SEO assessment, and more.

![ScrapeMind Screenshot](static/screenshot.png)
<!-- Replace with actual screenshot -->

## Features

- **Smart Scraping** -- Extracts clean text content from any URL, stripping scripts, styles, nav, and boilerplate
- **4 Analysis Modes:**
  - **Summary** -- 2-3 paragraph summary + key points + target audience
  - **Key Points** -- Facts, data, arguments, and action items extracted
  - **Sentiment** -- Tone analysis, emotional triggers, bias detection, credibility score
  - **Full Analysis** -- All of the above plus SEO assessment and recommendations
- **Metadata Extraction** -- Pulls page title, meta description, headings, and links
- **Word Count & Structure** -- Heading hierarchy and content length metrics
- **Handles Edge Cases** -- Auto-prefixes URLs, cleans whitespace, limits content size

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| AI Model | Claude Sonnet 4 via OpenRouter |
| Web Scraping | Requests + BeautifulSoup4 |
| Frontend | HTML + TailwindCSS (CDN) |

## Quick Start

### Prerequisites

- Python 3.10+
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

### Installation

```bash
# Clone the repository
git clone https://github.com/Seven7000000/scrapemind.git
cd scrapemind

# Install dependencies
pip install -r requirements.txt

# Set your API key
export OPENROUTER_API_KEY="your-key-here"

# Run the server
uvicorn main:app --port 8004 --reload
```

Open [http://localhost:8004](http://localhost:8004) in your browser.

## API Reference

### `POST /analyze`

Scrape a URL and analyze its content.

**Request:**
```json
{
  "url": "https://example.com/article",
  "analysis_type": "full"
}
```

**Parameters:**

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `url` | string | required | Any valid URL |
| `analysis_type` | string | `"summary"` | `summary`, `key_points`, `sentiment`, `full` |

**Response:**
```json
{
  "url": "https://example.com/article",
  "title": "Page Title",
  "meta_description": "Page description...",
  "word_count": 2450,
  "headings_count": 8,
  "links_count": 15,
  "analysis": "## Summary\nThis article covers...",
  "headings": [
    { "level": "h1", "text": "Main Heading" },
    { "level": "h2", "text": "Section Title" }
  ]
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Your OpenRouter API key |

## Project Structure

```
scrapemind/
  main.py             # FastAPI application + scraping engine
  requirements.txt    # Python dependencies
  static/
    index.html         # Single-page frontend
```

## License

MIT
