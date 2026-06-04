"""
Submit Aethyro.com sitemap to Google Search Console.
Run: python submit_sitemap_gsc.py
Opens your browser for Google OAuth, then submits the sitemap automatically.
"""
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs
import urllib.request
import secrets
import hashlib
import base64
import os

SITE_URL    = "https://aethyro.com/"
SITEMAP_URL = "https://aethyro.com/sitemap.xml"
PORT        = 8765

# Google OAuth — these are public client credentials for installed apps.
# If you have a project in Google Cloud Console with the Search Console API enabled,
# replace these with your own OAuth 2.0 Client ID and Secret.
CLIENT_ID     = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")

SCOPE    = "https://www.googleapis.com/auth/webmasters"
REDIRECT = f"http://localhost:{PORT}/callback"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _pkce():
    verifier = _b64(secrets.token_bytes(32))
    challenge = _b64(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


def _exchange_code(code: str, verifier: str, client_id: str, client_secret: str) -> str:
    data = urlencode({
        "code":          code,
        "client_id":     client_id,
        "client_secret": client_secret,
        "redirect_uri":  REDIRECT,
        "grant_type":    "authorization_code",
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]


def _submit_sitemap(token: str) -> int:
    encoded_site    = urllib.request.quote(SITE_URL, safe="")
    encoded_sitemap = urllib.request.quote(SITEMAP_URL, safe="")
    url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/sitemaps/{encoded_sitemap}"
    req = urllib.request.Request(
        url,
        method="PUT",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


def _check_sitemap(token: str) -> dict:
    encoded_site    = urllib.request.quote(SITE_URL, safe="")
    encoded_sitemap = urllib.request.quote(SITEMAP_URL, safe="")
    url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/sitemaps/{encoded_sitemap}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def main():
    # ── Check for OAuth credentials ────────────────────────────────────────────
    if not CLIENT_ID or not CLIENT_SECRET:
        print()
        print("=" * 65)
        print("  Google Search Console — Manual Submission Required")
        print("=" * 65)
        print()
        print("  No GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET set.")
        print()
        print("  FASTEST OPTION — Submit directly in your browser:")
        print()
        print("  1. Open this URL:")
        print()
        print("     https://search.google.com/search-console/sitemaps")
        print("         ?resource_id=https%3A%2F%2Faethyro.com%2F")
        print()
        print("  2. Paste this sitemap URL into the field:")
        print()
        print("     https://aethyro.com/sitemap.xml")
        print()
        print("  3. Click Submit.")
        print()
        print("  Sitemap is ALREADY in robots.txt so Google will find it")
        print("  automatically — this just speeds it up by 1-7 days.")
        print()
        print("  ─── To enable automated submission in the future ────────")
        print()
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create/select a project → Enable 'Google Search Console API'")
        print("  3. APIs & Services → Credentials → Create OAuth 2.0 Client ID")
        print("     (Application type: Desktop)")
        print("  4. Set in your shell:")
        print("     $env:GOOGLE_OAUTH_CLIENT_ID   = 'your-client-id'")
        print("     $env:GOOGLE_OAUTH_CLIENT_SECRET = 'your-client-secret'")
        print("  5. Re-run this script — it will handle auth automatically.")
        print()

        # Try to open the browser directly
        gsc_url = ("https://search.google.com/search-console/sitemaps"
                   "?resource_id=https%3A%2F%2Faethyro.com%2F")
        try:
            webbrowser.open(gsc_url)
            print("  Browser opened to Google Search Console.")
        except Exception:
            print("  Could not auto-open browser — use URL above.")
        return

    # ── OAuth PKCE flow ────────────────────────────────────────────────────────
    verifier, challenge = _pkce()
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode({
            "client_id":             CLIENT_ID,
            "redirect_uri":          REDIRECT,
            "response_type":         "code",
            "scope":                 SCOPE,
            "code_challenge":        challenge,
            "code_challenge_method": "S256",
            "access_type":           "offline",
            "prompt":                "consent",
        })
    )

    token_holder = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass  # suppress access logs

        def do_GET(self):
            qs = parse_qs(urlparse(self.path).query)
            code = qs.get("code", [""])[0]
            if code:
                token_holder["code"] = code
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>Authorized. You can close this tab.</h2>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"<h2>No code received.</h2>")

        def do_HEAD(self): pass

    print(f"\nOpening browser for Google authorization...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", PORT), Handler)
    server.timeout = 120
    server.handle_request()

    code = token_holder.get("code")
    if not code:
        print("No authorization code received. Aborting.")
        sys.exit(1)

    print("Exchanging code for access token...")
    token = _exchange_code(code, verifier, CLIENT_ID, CLIENT_SECRET)

    print(f"Submitting sitemap: {SITEMAP_URL}")
    status = _submit_sitemap(token)
    print(f"Submission HTTP status: {status}")

    if status in (200, 204):
        print("\nSitemap submitted successfully!")
        try:
            info = _check_sitemap(token)
            print(f"  GSC reports {info.get('contents', [{}])[0].get('submitted', '?')} URLs submitted")
        except Exception:
            pass
    else:
        print(f"Unexpected status {status}. Check GSC manually.")


if __name__ == "__main__":
    main()
