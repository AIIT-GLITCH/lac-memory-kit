#!/usr/bin/env python3
"""Browser Agent — Claude-tool-calling loop that drives the browser.

Originally Gary's. Browser Claude wrote the underlying worker;
this is the autonomous loop that lets a model see screenshots and
choose actions.

Set ANTHROPIC_API_KEY and run:
    python -m lac.browser.browser_agent "go to wikipedia and find Marie Curie"
"""

import sys
import json

try:
    import anthropic
except ImportError:
    print("Install: pip install anthropic", file=sys.stderr)
    sys.exit(1)

from .browser import (
    browser_go, browser_text, browser_screenshot_b64,
    browser_click, browser_click_xy, browser_fill,
    browser_scroll, browser_read_dom, browser_interactive,
    browser_eval, browser_close,
)

client = anthropic.Anthropic()
MODEL = "claude-opus-4-7"

TOOLS = [
    {"name": "screenshot",
     "description": "Take a screenshot of the current browser state. Always call after any action.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "navigate",
     "description": "Navigate to a URL. Returns a screenshot.",
     "input_schema": {"type": "object",
                      "properties": {"url": {"type": "string"}},
                      "required": ["url"]}},
    {"name": "click",
     "description": "Click by CSS selector OR x,y. Returns a screenshot.",
     "input_schema": {"type": "object",
                      "properties": {"selector": {"type": "string"},
                                     "x": {"type": "number"},
                                     "y": {"type": "number"}}}},
    {"name": "type_text",
     "description": "Type text into an input field. Returns a screenshot.",
     "input_schema": {"type": "object",
                      "properties": {"selector": {"type": "string"},
                                     "text": {"type": "string"}},
                      "required": ["selector", "text"]}},
    {"name": "scroll",
     "description": "Scroll up or down. Returns a screenshot.",
     "input_schema": {"type": "object",
                      "properties": {"direction": {"type": "string", "enum": ["up", "down"]},
                                     "amount": {"type": "integer"}},
                      "required": ["direction"]}},
    {"name": "get_interactive_elements",
     "description": "List clickable/interactive elements with text, selector, x/y.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_page_text",
     "description": "Get all visible text content as plain text.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "read_dom",
     "description": "Read innerHTML/innerText of a specific element by CSS selector.",
     "input_schema": {"type": "object",
                      "properties": {"selector": {"type": "string"}},
                      "required": ["selector"]}},
    {"name": "eval_js",
     "description": "Run JavaScript in the page and return the result. Use sparingly.",
     "input_schema": {"type": "object",
                      "properties": {"code": {"type": "string"}},
                      "required": ["code"]}},
]


def run_tool(name, inp):
    def text_block(t):
        return {"type": "text", "text": str(t)}

    def img_block(b64):
        return {"type": "image", "source": {"type": "base64",
                                            "media_type": "image/png", "data": b64}}

    if name == "screenshot":
        r = browser_screenshot_b64()
        if r.get("success") and r.get("screenshot_b64"):
            return [img_block(r["screenshot_b64"])]
        return [text_block("Screenshot failed: " + r.get("error", "unknown"))]

    if name == "navigate":
        r = browser_go(inp.get("url", ""))
        blocks = [text_block(f"Navigated to: {r.get('url','')} — {r.get('title','')}")]
        if r.get("screenshot_b64"):
            blocks.append(img_block(r["screenshot_b64"]))
        return blocks

    if name == "click":
        sel = inp.get("selector")
        x, y = inp.get("x"), inp.get("y")
        r = browser_click(sel) if sel else browser_click_xy(float(x), float(y))
        blocks = [text_block("Clicked" if r.get("success") else "Click failed: " + r.get("error", ""))]
        if r.get("screenshot_b64"):
            blocks.append(img_block(r["screenshot_b64"]))
        return blocks

    if name == "type_text":
        r = browser_fill(inp.get("selector", ""), inp.get("text", ""))
        blocks = [text_block("Typed" if r.get("success") else "Type failed: " + r.get("error", ""))]
        if r.get("screenshot_b64"):
            blocks.append(img_block(r["screenshot_b64"]))
        return blocks

    if name == "scroll":
        r = browser_scroll(inp.get("direction", "down"), inp.get("amount", 400))
        blocks = [text_block("Scrolled " + inp.get("direction", "down"))]
        if r.get("screenshot_b64"):
            blocks.append(img_block(r["screenshot_b64"]))
        return blocks

    if name == "get_interactive_elements":
        r = browser_interactive()
        if not r.get("success"):
            return [text_block("Error: " + r.get("error", "unknown"))]
        elements = r.get("elements", [])
        lines = [
            f"[{e['type']}] \"{e['text']}\" @ ({e['x']},{e['y']}) | selector: {e['selector']}"
            + (f" | href: {e['href']}" if e.get("href") else "")
            for e in elements
        ]
        return [text_block(f"{len(lines)} interactive elements:\n" + "\n".join(lines))]

    if name == "get_page_text":
        r = browser_text()
        return [text_block(r.get("text", "No text returned"))]

    if name == "read_dom":
        r = browser_read_dom(inp.get("selector", "body"))
        if not r.get("success"):
            return [text_block("Error: " + r.get("error", ""))]
        return [text_block(f"TEXT:\n{r.get('text','')}\n\nHTML:\n{r.get('html','')}")]

    if name == "eval_js":
        r = browser_eval(inp.get("code", ""))
        if r.get("success"):
            return [text_block(str(r.get("result", "done")))]
        return [text_block("JS error: " + r.get("error", ""))]

    return [text_block(f"Unknown tool: {name}")]


SYSTEM = """You have full control of a live browser. You can see (screenshots), click, type, scroll, and navigate.

Rules:
1. After EVERY action, call screenshot() to verify the result before proceeding.
2. Use get_interactive_elements() to find what to click.
3. Never guess at selectors — verify with get_interactive_elements() or read_dom() first.
4. If something doesn't work, screenshot and reassess.
5. Report what you did and what you see at each step.
6. When the task is done, say DONE and summarize what you accomplished."""


def run_agent(task: str, max_turns: int = 30):
    print(f"\n[AGENT] Task: {task}\n{'─'*60}")
    messages = [{"role": "user", "content": task}]
    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL, max_tokens=4096,
            system=SYSTEM, tools=TOOLS, messages=messages,
        )
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"\n[AGENT] {block.text}")
        if response.stop_reason == "end_turn":
            print("\n[AGENT] Task complete.")
            break
        if response.stop_reason == "tool_use":
            tool_calls = [b for b in response.content if b.type == "tool_use"]
            if not tool_calls:
                break
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for tc in tool_calls:
                print(f"\n[TOOL] {tc.name}({json.dumps(tc.input, ensure_ascii=False)[:120]})")
                result_content = run_tool(tc.name, tc.input)
                for block in result_content:
                    if block.get("type") == "text":
                        print(f"  → {block['text'][:200]}")
                    elif block.get("type") == "image":
                        print(f"  → [screenshot captured]")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_content,
                })
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    else:
        print(f"\n[AGENT] Max turns ({max_turns}) reached.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        run_agent(task)
    else:
        print("Browser Agent — interactive mode. Ctrl+C to quit.\n")
        while True:
            try:
                task = input("Task > ").strip()
                if task:
                    run_agent(task)
            except KeyboardInterrupt:
                print("\nClosing browser...")
                browser_close()
                break
