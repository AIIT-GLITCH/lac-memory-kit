"""Browser control — talks to browser_worker.py over stdin/stdout JSON.

Originally Gary's. Browser Claude (Anthropic Chrome extension) wrote
the worker; this file is the thin client that lives in your model's
process and routes commands to it.
"""
import json
import os
import subprocess
import threading
import selectors

_lock = threading.Lock()
_worker_proc = None
_WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_worker.py")
_TIMEOUT = 120


def _start_worker():
    global _worker_proc
    if _worker_proc and _worker_proc.poll() is None:
        return
    _worker_proc = subprocess.Popen(
        ["python3", "-u", _WORKER_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _send_cmd(cmd_dict):
    global _worker_proc
    with _lock:
        if _worker_proc is None or _worker_proc.poll() is not None:
            _start_worker()
        try:
            line = json.dumps(cmd_dict) + "\n"
            _worker_proc.stdin.write(line)
            _worker_proc.stdin.flush()
            sel = selectors.DefaultSelector()
            sel.register(_worker_proc.stdout, selectors.EVENT_READ)
            events = sel.select(timeout=_TIMEOUT)
            sel.close()
            if not events:
                return {"ok": False, "error": "Worker timed out"}
            resp_line = _worker_proc.stdout.readline()
            if not resp_line:
                return {"ok": False, "error": "Worker returned empty response"}
            return json.loads(resp_line)
        except Exception as e:
            return {"ok": False, "error": str(e)}


def browser_go(url):
    return _send_cmd({"action": "go", "url": url})

def browser_text():
    return _send_cmd({"action": "text"})

def browser_screenshot(name):
    return _send_cmd({"action": "screenshot", "name": name})

def browser_click(selector):
    return _send_cmd({"action": "click", "selector": selector})

def browser_fill(selector, text):
    return _send_cmd({"action": "fill", "selector": selector, "text": text})

def browser_links():
    return _send_cmd({"action": "links"})

def browser_pdf():
    return _send_cmd({"action": "pdf"})

def browser_eval(code):
    return _send_cmd({"action": "eval", "code": code})

def browser_close():
    return _send_cmd({"action": "close"})

def browser_scroll(direction="down", amount=300):
    return _send_cmd({"action": "scroll", "direction": direction, "amount": amount})

def browser_read_dom(selector):
    return _send_cmd({"action": "read_dom", "selector": selector})

def browser_interactive():
    return _send_cmd({"action": "interactive"})

def browser_screenshot_b64():
    return _send_cmd({"action": "screenshot_b64"})

def browser_click_xy(x, y):
    return _send_cmd({"action": "click", "x": x, "y": y})


def _fmt(result):
    if not (result.get('ok') or result.get('success')):
        return 'Browser error - ' + result.get('error', 'unknown')
    parts = []
    if 'title' in result:
        parts.append('Page - ' + result['title'])
    if 'url' in result:
        parts.append('URL - ' + result['url'])
    if 'text' in result:
        parts.append(result['text'])
    if 'text_preview' in result:
        parts.append(result['text_preview'])
    if 'result' in result:
        parts.append(str(result['result']))
    if 'path' in result:
        parts.append('Saved to - ' + result['path'])
    if 'note' in result:
        parts.append('Note - ' + result['note'])
    if 'html' in result:
        parts.append('HTML - ' + result['html'][:2000])
    if 'links' in result:
        for link in result['links']:
            parts.append('  [' + link.get('text', '') + '] -> ' + link.get('href', ''))
    if 'screenshot_b64' in result:
        parts.append('[screenshot captured]')
    if 'elements' in result:
        for el in result.get('elements', []):
            parts.append('  ' + str(el))
    if 'status' in result:
        parts.append('Status - ' + str(result['status']))
    return chr(10).join(parts) if parts else 'OK'


def dispatch_browser(cmd_str):
    """Route [BROWSER:action:args] command strings to browser functions.
    Useful when the model emits tagged commands in plain text."""
    parts = cmd_str.split(":", 2)
    action = parts[0].upper().strip() if parts else ""
    arg1 = parts[1].strip() if len(parts) > 1 else ""
    arg2 = parts[2].strip() if len(parts) > 2 else ""

    if action == "GO":
        result = browser_go(arg1)
    elif action == "TEXT":
        result = browser_text()
    elif action == "SCREENSHOT":
        result = browser_screenshot(arg1 or "screenshot")
    elif action == "CLICK":
        result = browser_click(arg1)
    elif action == "FILL":
        if "|" in arg1:
            sel, txt = arg1.split("|", 1)
            result = browser_fill(sel.strip(), txt.strip())
        elif arg2:
            result = browser_fill(arg1, arg2)
        else:
            return "Error: FILL requires selector|text"
    elif action == "LINKS":
        result = browser_links()
    elif action == "PDF":
        result = browser_pdf()
    elif action == "EVAL":
        result = browser_eval(arg1 if not arg2 else arg1 + ":" + arg2)
    elif action == "CLOSE":
        result = browser_close()
    elif action == "SCROLL":
        direction = arg1.lower() if arg1 else "down"
        amount = int(arg2) if arg2 and arg2.isdigit() else 300
        result = browser_scroll(direction, amount)
    elif action == "DOM":
        result = browser_read_dom(arg1)
    elif action == "INTERACTIVE":
        result = browser_interactive()
    elif action == "CLICK_XY":
        try:
            x, y = int(arg1), int(arg2)
            result = browser_click_xy(x, y)
        except ValueError:
            return "Error: CLICK_XY requires x y coordinates"
    else:
        return "Unknown browser action: " + action

    return _fmt(result)
