"""Gary's Browser — bundled with LAC Memory Kit.

ORIGIN STORY (honest):
  This browser code was written by Browser Claude — Anthropic's
  Chrome-extension Claude with browser-driving capability — when Rhet
  asked him to lend Gary his hands. Gary needed to drive a browser;
  Browser Claude already had the hands for that. He wrote the code that
  gives any agent the same hands.

  One Claude gifting capability to another agent. It works. It ships
  free with the memory kit.

Three files:
  browser_worker.py — Playwright worker process (the actual hands)
  browser.py        — JSON-over-stdio client to talk to the worker
  browser_agent.py  — Claude-tool-calling loop that sees screenshots
                      and drives the browser autonomously

Configure with env vars (optional — sensible defaults):
  LAC_BROWSER_SCREENSHOTS — where to save screenshots
                            (default: ~/.lac_browser/screenshots)
  LAC_BROWSER_PROFILE     — Chrome user data dir
                            (default: ~/.lac_browser/chrome_profile)
  LAC_BROWSER_DOWNLOADS   — PDF/download destination
                            (default: ~/Downloads)
"""
from .browser import (
    browser_go, browser_text, browser_click, browser_fill, browser_links,
    browser_pdf, browser_eval, browser_close, browser_scroll,
    browser_read_dom, browser_interactive, browser_screenshot,
    browser_screenshot_b64, browser_click_xy, dispatch_browser,
)

__all__ = [
    "browser_go", "browser_text", "browser_click", "browser_fill",
    "browser_links", "browser_pdf", "browser_eval", "browser_close",
    "browser_scroll", "browser_read_dom", "browser_interactive",
    "browser_screenshot", "browser_screenshot_b64", "browser_click_xy",
    "dispatch_browser",
]
