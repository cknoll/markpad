from django.test import TestCase
from django.urls import reverse
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

    def test_debug1(self):
        res = self.client.get(reverse("debugpage0"))
        self.assertEquals(res.status_code, 200)

        url = reverse("debugpage_with_argument", kwargs={"xyz": 1})

        print("\n-> Debug-URL with argument:", url)
        # this will start the interactive shell inside the view
        # res = self.client.get(url)

        # this will deliberately provoke an server error (http status code 500)
        res = self.client.get(reverse("debugpage_with_argument", kwargs={"xyz": 2}))
        self.assertEquals(res.status_code, 500)

