import unittest
from html.parser import HTMLParser
from unittest.mock import patch

from pydantic_settings.sources import DotEnvSettingsSource

with patch.object(DotEnvSettingsSource, "_read_env_files", return_value={}):
    from app.main import app

from fastapi.testclient import TestClient


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        value = attrs.get("src") or (attrs.get("href") if tag in ("link", "use") else None)
        if value:
            self.assets.append(value.split("#")[0])


# Страницы и ресурсы должны работать без БД и не выполнять действия из email по GET.
class PageTests(unittest.TestCase):
    def setUp(self):
        self.client = self.enterContext(TestClient(app))

    def test_pages_and_referenced_assets_are_served(self):
        paths = ["/", "/features", "/tutors", "/for-tutors", "/for-students", "/help", "/login", "/register", "/t/1", "/tutor/dashboard", "/student/dashboard", "/confirm", "/cancel"]
        for path in paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn("text/html", response.headers["content-type"])
            self.assertEqual(response.headers["cache-control"], "no-store")
            parser = AssetParser()
            parser.feed(response.text)
            for asset in parser.assets:
                self.assertEqual(self.client.get(asset).status_code, 200, asset)

    def test_health_endpoint_remains_available(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/openapi.json").status_code, 200)

    def test_existing_email_links_serve_the_action_pages(self):
        for action in ["confirm", "cancel"]:
            response = self.client.get(f"/api/v1/bookings/{action}?token=example")
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'data-action="{action}"', response.text)


if __name__ == "__main__":
    unittest.main()
