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
    def test_get_static_pages(self):

        static_page_blocks = util.get_static_pages()
        self.assertIsInstance(static_page_blocks["about"], util.Container)
        self.assertIn("markdown rendering", static_page_blocks["about"].content)
        self.assertIn("Legal Notice", static_page_blocks["legal-notice"].title)

    def test_encrypt_decrypt(self):

        test_str = "abcde"
        token = util.encrypt_str(test_str)

        decrypted_token = util.decrypt_str(token)

        self.assertNotEqual(token, test_str)
        self.assertEqual(decrypted_token, test_str)

    def test_obfuscate_url(self):

        p1, p2 = "https://etherpad.wikimedia.org/", "p/some-pad-name"

        url = p1 + p2
        res = util.obfuscate_source_url(url)
        self.assertTrue(res.startswith(p1))
        self.assertNotIn(p2, res)

        print(url)
        print(res)

        res2 = util.deobfuscate_source_url(res)
        self.assertEqual(res2, url)

        p1, p2 = "http://xyz.abc/", "efgh/ijk/lmn/OPQ-rst-UVW"

        url = p1 + p2
        res = util.obfuscate_source_url(url)
        self.assertTrue(res.startswith(p1))
        self.assertNotIn(p2, res)

        res2 = util.deobfuscate_source_url(res)
        self.assertEqual(res2, url)
        print(url)
        print(res)
