from django.test import TestCase
from django.urls import reverse
from django.conf import settings
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

    def test_home_encrypted_urls(self):

        padurl = "https://etherpad.wikimedia.org/p/some-test-pad"
        ob_padurl = util.obfuscate_source_url(padurl)

        # test utc-string for encrypted-url-mode
        url = reverse("md_preview_oburl", kwargs={"src_url": ob_padurl})
        res = self.client.get(url)
        self.assertContains(res, f"utc_md_rendering_oburl:{ob_padurl}")

        # test utc-string for plain-url-mode
        url = reverse("md_preview", kwargs={"src_url": padurl})
        res = self.client.get(url)
        self.assertContains(res, f"utc_md_rendering_plain_url:{padurl}")


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

    def test_recognize_mathjax(self):
        str1 = '<div class="MathJax_Preview"> \\begin{align*}...'
        str2 = 'foo\n<span class="MathJax_Preview"> \\begin{align*}...\nbar'
        str3 = 'foo\n<div class="Math--Jax_Preview"> \\begin{align*}...\nbar'

        self.assertTrue(util.recognize_mathjax(str1))
        self.assertTrue(util.recognize_mathjax(str2))
        self.assertFalse(util.recognize_mathjax(str3))

    def test_render_formula(self):

        html1 = util.render_markdown("formula: $a + b$")
        html2 = util.render_markdown("formula:\n $$a + b$$ \n")

        self.assertTrue(util.recognize_mathjax(html1))
        self.assertTrue(util.recognize_mathjax(html2))

    def test_custom_bleach(self):

        # test bleach in general
        str1 = '<script type="math/tex">test</script>'
        str2 = '<script type="math/tex; mode=display">test</script>'

        kwargs = dict(tags=settings.BLEACH_ALLOWED_TAGS, attributes=settings.BLEACH_ALLOWED_ATTRIBUTES)

        res1 = util.bleach.clean(str1, **kwargs)
        res2 = util.bleach.clean(str2, **kwargs)

        self.assertEqual(str1, res1)
        self.assertEqual(str2, res2)

        # test (here undesired) behavior of default bleach
        str1 = '<script type="math/tex">a > b < c \\& d</script><p>a > b < c \\& d</p>'
        res1 = util.bleach.clean(str1, **kwargs)
        e_res1 = '<script type="math/tex">a &gt; b &lt; c \\&amp; d</script><p>a &gt; b &lt; c \\&amp; d</p>'
        self.assertEqual(res1, e_res1)

        # test (desired) behavior of wrapped bleach
        res1 = util.custom_bleach(str1)
        self.assertEqual(res1, '<script type="math/tex">a > b < c \\& d</script><p>a &gt; b &lt; c \\&amp; d</p>')

    def test_error_page(self):
        ##!
        url = reverse("md_preview_oburl", kwargs={"src_url": "foobar"})
        res = self.client.get(url)

        self.assertContains(res, "utc_error_page")

