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


def home_page_view(request):
    context = dict()

    if request.method == 'POST':
        form_data_str = json.dumps(request.POST)
        print(form_data_str)

        # use the Post-Redirect-Get (PRG) pattern
        # (see: https://www.theserverside.com/news/1365146/Redirect-After-Post)
        url = reverse('md_preview', kwargs={"padurl": form_data_str})
        return HttpResponseRedirect(url)

    return render(request, 'mainapp/main.html', context)


class ViewMdPreview(View):
    """
    Render the plain txt-content of a pad-url as markdown.
    """

    # noinspection PyMethodMayBeStatic
    def get(self, request, padurl=None):

        if padurl is None:
            padurl = "https://yopad.eu/p/mdpad-default-365days"

        md_src_url = f"{padurl}/export/txt"
        src_txt = get_md_src_or_error_msg(md_src_url)

        ctn = Container()
        ctn.src_txt = src_txt
        ctn.pad_url = padurl

        base = Container()
        # endow_base_object(base, request)

        context = {"ctn": ctn, "base": base}
        return render(request, 'mainapp/md_preview.html', context)


def get_md_src_or_error_msg(md_src_url):
    try:
        # noinspection PyUnresolvedReferences
        r = urllib.request.urlopen(md_src_url)
        src_txt = r.read().decode("utf8")
    # noinspection PyUnresolvedReferences
    except urllib.error.HTTPError:
        src_txt = f"**Error:** The following URL could not be read: \n\n `{md_src_url}`"
    return src_txt
