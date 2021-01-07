import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.urls import reverse
from django.views import View
import urllib

from ipydex import IPS


# empty object to store some attributes at runtime
class Container(object):
    pass


def home_page_view(request, form_data_len=None):
    context = dict(greeting_message="Hello, World!", data_len=form_data_len)

    if request.method == 'POST':
        # here the data of the HTML-form can be processed. E.g it can be saved to the database etc.
        # for demonstration convert the dict `request.POST` to a json representaion
        form_data_str = json.dumps(request.POST)
        print(form_data_str)

        # use the Post-Redirect-Get (PRG) pattern
        # (see: https://www.theserverside.com/news/1365146/Redirect-After-Post)

        url = reverse('landingpage_with_form_data', kwargs={"form_data_len": len(form_data_str)})
        return HttpResponseRedirect(url)

    return render(request, 'mainapp/main.html', context)


class ViewMdPreview(View):
    """
    Render the plain txt-content of a pad-url as markdown.
    """

    # noinspection PyMethodMayBeStatic
    def get(self, request, padurl=None):

        src_url = "https://pad.fsfw-dresden.de/p/funding-foss-35c3/export/txt"

        assert src_url.endswith("/export/txt")

        # noinspection PyUnresolvedReferences
        r = urllib.request.urlopen(src_url)
        src_txt = r.read().decode("utf8")

        ctn = Container()
        ctn.src_txt = src_txt
        ctn.src_url = src_url.replace("/export/txt", "")
        ctn.a = 8

        base = Container()
        # endow_base_object(base, request)

        context = {"ctn": ctn, "base": base}
        return render(request, 'mainapp/md_preview.html', context)


def debug_view(request, xyz=0):

    z = 1

    if xyz == 1:
        # start interactive shell for debugging (helpful if called from the unittests)
        IPS()

    elif xyz == 2:
        return HttpResponseServerError("Errormessage")

    return HttpResponse('Some plain message')
