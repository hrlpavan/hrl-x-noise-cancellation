"""
Lightweight HTTP server serving the Anush X HRL Web Dashboard.
Built using standard library http.server (zero third-party dependencies).
"""

import http.server
import os
import socketserver
import webbrowser
from pathlib import Path


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the web dashboard and audio static files."""

    def __init__(self, *args, **kwargs):
        web_dir = Path(__file__).parent.parent / "web"
        super().__init__(*args, directory=str(web_dir), **kwargs)

    def log_message(self, format, *args):
        # Clean terminal logging
        sys_msg = format % args
        if "GET" in sys_msg or "POST" in sys_msg:
            print(f"[HTTP] {sys_msg}")


def start_server(port: int = 8080, open_browser: bool = True) -> int:
    """Starts the local web server."""
    # Allow address reuse to prevent 'Address already in use' errors
    socketserver.TCPServer.allow_reuse_address = True

    web_dir = Path(__file__).parent.parent / "web"
    if not web_dir.exists():
        print(f"[!] Error: Web dashboard directory not found at {web_dir}")
        return 1

    try:
        with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
            url = f"http://localhost:{port}"
            print("=" * 64)
            print("  ANUSH X HRL // REAL-TIME WEB DASHBOARD")
            print("=" * 64)
            print(f"[*] Serving web dashboard at: {url}")
            print("[*] Press Ctrl+C to stop server.")
            print("=" * 64)

            if open_browser:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server shutdown requested by user. Goodbye.")
    except OSError as e:
        print(f"[!] Server error on port {port}: {e}")
        return 1

    return 0


if __name__ == "__main__":
    start_server()
