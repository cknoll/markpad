from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
import urllib


# empty object to store some attributes at runtime
class Container(object):
    pass


def home_page_view(request):
    context = dict()

    if request.method == 'POST':
        form_data_str = request.POST.get("field1")

        # use the Post-Redirect-Get (PRG) pattern
        # (see: https://www.theserverside.com/news/1365146/Redirect-After-Post)

        if form_data_str == "":
            url = reverse('md_preview')
        else:
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


# noinspection PyUnresolvedReferences
def get_md_src_or_error_msg(md_src_url):
    try:
        r = urllib.request.urlopen(md_src_url)
        src_txt = r.read().decode("utf8")
    except (urllib.error.HTTPError, urllib.error.URLError):
        src_txt = f"**Error:** The following URL could not be read: \n\n `{md_src_url}`"
    return src_txt
