#!/usr/bin/env python3
"""Browser worker — Playwright process Gary calls into.

Originally written by Browser Claude (Anthropic's Chrome-extension Claude)
when Rhet asked him to lend Gary his hands.

Configure paths via env vars:
  LAC_BROWSER_SCREENSHOTS  (default: ~/.lac_browser/screenshots)
  LAC_BROWSER_PROFILE      (default: ~/.lac_browser/chrome_profile)
  LAC_BROWSER_DOWNLOADS    (default: ~/Downloads)

Requires: pip install playwright && playwright install chromium
"""
import json
import os
import sys
import time
import base64

SCREENSHOTS_DIR = os.path.expanduser(
    os.environ.get("LAC_BROWSER_SCREENSHOTS", "~/.lac_browser/screenshots")
)
BROWSER_PROFILE = os.path.expanduser(
    os.environ.get("LAC_BROWSER_PROFILE", "~/.lac_browser/chrome_profile")
)
DOWNLOADS_DIR = os.path.expanduser(
    os.environ.get("LAC_BROWSER_DOWNLOADS", "~/Downloads")
)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def _clip(s, n):
    return s if len(s) <= n else s[:n]


_pw = None
_context = None
_page = None


def log(msg):
    sys.stderr.write("BW " + str(msg) + chr(10))
    sys.stderr.flush()


def ensure_browser():
    global _pw, _context, _page
    if _page and not _page.is_closed():
        return _page
    log("Launching browser")
    from playwright.sync_api import sync_playwright
    _pw = sync_playwright().start()
    _context = _pw.chromium.launch_persistent_context(
        user_data_dir=BROWSER_PROFILE,
        headless=False,
        channel="chrome",
        args=["--no-first-run", "--disable-blink-features=AutomationControlled", "--no-sandbox"],
        viewport=dict(width=1280, height=800),
    )
    pages = _context.pages
    _page = pages.pop(0) if pages else _context.new_page()
    log("Browser ready")
    return _page


def close_browser():
    global _pw, _context, _page
    try:
        if _context:
            _context.close()
        if _pw:
            _pw.stop()
    except Exception:
        pass
    _pw = None
    _context = None
    _page = None


def handle_ping(a):
    return dict(success=True, status="alive")


def handle_go(args):
    url = args.get("url", "")
    if not url:
        return dict(success=False, error="No URL")
    p = ensure_browser()
    p.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(1)
    body = p.inner_text("body")
    b64 = _snap_b64()
    return dict(success=True, title=p.title(), url=p.url,
                text_preview=_clip(body, 2000), screenshot_b64=b64)


def handle_text(args):
    body = ensure_browser().inner_text("body")
    return dict(success=True, text=_clip(body, 10000))


def handle_screenshot(args):
    n = args.get("name") or ("screenshot_" + str(int(time.time())))
    if not n.endswith(".png"):
        n += ".png"
    path = os.path.join(SCREENSHOTS_DIR, n)
    ensure_browser().screenshot(path=path, full_page=False)
    return dict(success=True, path=path)


def _snap_b64():
    try:
        data = ensure_browser().screenshot(full_page=False)
        return base64.b64encode(data).decode()
    except Exception as e:
        log("snap_b64 error: " + str(e))
        return None


def handle_click(args):
    s = args.get("selector", "")
    x = args.get("x")
    y = args.get("y")
    p = ensure_browser()
    if s:
        p.click(s, timeout=10000)
    elif x is not None and y is not None:
        p.mouse.click(float(x), float(y))
    else:
        return dict(success=False, error="Need selector or x,y")
    time.sleep(0.8)
    return dict(success=True, screenshot_b64=_snap_b64())


def handle_fill(args):
    s = args.get("selector", "")
    t = args.get("text", "")
    if not s:
        return dict(success=False, error="No selector")
    p = ensure_browser()
    p.click(s, timeout=5000)
    p.fill(s, t, timeout=10000)
    time.sleep(0.4)
    return dict(success=True, screenshot_b64=_snap_b64())


def handle_links(args):
    p = ensure_browser()
    anchors = p.query_selector_all("a")
    result = []
    for el in anchors:
        href = el.get_attribute("href") or ""
        txt = (el.inner_text() or "").strip()
        if txt and href:
            result.append(dict(text=_clip(txt, 80), href=href))
        if len(result) >= 50:
            break
    return dict(success=True, links=result)


def handle_eval(args):
    code = args.get("code", "")
    if not code:
        return dict(success=False, error="No code")
    p = ensure_browser()
    result = p.evaluate(code)
    return dict(success=True, result=str(result) if result else "done")


def handle_pdf(args):
    url = args.get("url")
    p = ensure_browser()
    if url:
        p.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
    path = os.path.join(DOWNLOADS_DIR, "lac_export_" + str(int(time.time())) + ".pdf")
    try:
        p.pdf(path=path)
        return dict(success=True, path=path)
    except Exception:
        ss = os.path.join(SCREENSHOTS_DIR, "pdf_fallback_" + str(int(time.time())) + ".png")
        p.screenshot(path=ss, full_page=True)
        return dict(success=True, path=ss, note="PDF failed, screenshot saved")


def handle_close(args):
    close_browser()
    return dict(success=True, status="closed")


def handle_scroll(args):
    direction = args.get("direction", "down")
    amount = int(args.get("amount", 300))
    p = ensure_browser()
    delta = amount if direction == "down" else -amount
    p.evaluate(f"window.scrollBy(0, {delta})")
    time.sleep(0.5)
    return dict(success=True, screenshot_b64=_snap_b64())


def handle_read_dom(args):
    selector = args.get("selector", "body")
    p = ensure_browser()
    try:
        el = p.query_selector(selector)
        if not el:
            return dict(success=False, error=f"No element: {selector}")
        return dict(
            success=True,
            text=_clip(el.inner_text(), 5000),
            html=_clip(el.inner_html(), 5000),
        )
    except Exception as e:
        return dict(success=False, error=str(e))


def handle_interactive(args):
    p = ensure_browser()
    elements = []
    selectors = [
        ("button", "button"), ("a", "link"),
        ("input", "input"), ("select", "select"),
        ("textarea", "textarea"), ("[role='button']", "button"),
    ]
    for sel, kind in selectors:
        for el in p.query_selector_all(sel)[:30]:
            try:
                box = el.bounding_box()
                text = (el.inner_text() or el.get_attribute("placeholder")
                        or el.get_attribute("aria-label")
                        or el.get_attribute("value") or "")
                href = el.get_attribute("href") or ""
                if box:
                    elements.append(dict(
                        type=kind, text=_clip(text.strip(), 60),
                        href=href,
                        x=round(box["x"] + box["width"] / 2),
                        y=round(box["y"] + box["height"] / 2),
                        selector=sel,
                    ))
            except Exception:
                pass
        if len(elements) >= 80:
            break
    return dict(success=True, elements=elements)


def handle_screenshot_b64(args):
    b64 = _snap_b64()
    if b64:
        return dict(success=True, screenshot_b64=b64)
    return dict(success=False, error="Screenshot failed")


HANDLERS = dict(
    ping=handle_ping, go=handle_go, text=handle_text,
    screenshot=handle_screenshot, screenshot_b64=handle_screenshot_b64,
    click=handle_click, fill=handle_fill,
    links=handle_links, pdf=handle_pdf,
    close=handle_close, eval=handle_eval,
    scroll=handle_scroll, read_dom=handle_read_dom,
    interactive=handle_interactive,
)


def respond(d):
    sys.stdout.write(json.dumps(d) + chr(10))
    sys.stdout.flush()


def main():
    log("Worker started")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            cmd = req.get("action") or req.get("cmd", "")
            h = HANDLERS.get(cmd)
            if not h:
                respond(dict(success=False, error="Unknown " + cmd))
                continue
            log("Exec " + cmd)
            respond(h(req))
        except Exception as e:
            log("Error " + str(e))
            respond(dict(success=False, error=str(e)))


if __name__ == "__main__":
    main()
