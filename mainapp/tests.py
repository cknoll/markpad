from django.test import TestCase
from django.urls import reverse
from . import util
from ipydex import IPS

# The tests can be run with
# `python manage.py test`
# `python manage.py test --rednose` # with colors


class TestMainApp1(TestCase):
    def setup(self):
        pass

    def test_home_page1(self):

        # get url by its unique name, see urls.py

        url = reverse("landingpage")
        res = self.client.get(url)

        # `utc` means "unit test comment"
        # this is a simple mechanism to ensure the desired content actually was delivered
        self.assertEquals(res.status_code, 200)
        self.assertContains(res, "utc_landing_page")
        self.assertNotContains(res, "utc_debug_page")


class TestUtils(TestCase):
    def test_(self):

        static_page_blocks = util.get_static_pages()
        self.assertIsInstance(static_page_blocks["about"], util.Container)
        self.assertIn("markdown rendering", static_page_blocks["about"].content)
        self.assertIn("Legal Notice", static_page_blocks["legal-notice"].title)
