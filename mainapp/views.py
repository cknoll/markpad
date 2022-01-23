from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views import View
from bs4 import BeautifulSoup

import urllib

from . import util
from .util import Container

static_page_blocks = util.get_static_pages()


def home_page_view(request):
    context = dict()

    if request.method == "POST":
        form_data_str = request.POST.get("field1")

        # use the Post-Redirect-Get (PRG) pattern
        # (see: https://www.theserverside.com/news/1365146/Redirect-After-Post)

        if form_data_str == "":
            url = reverse("md_preview")
        else:
            url = reverse("md_preview", kwargs={"src_url": form_data_str})
        return HttpResponseRedirect(url)

    return render(request, "mainapp/main.html", context)


class ViewMdPreview(View):
    """
    Render the plain txt-content of a pad-url as markdown.
    """

    # noinspection PyMethodMayBeStatic
    def get(self, request, src_url=None, mode="plain_url"):

        ctn = Container()

        if src_url is None:
            return render_error_page(request, err_msg="No source url was provided.")

        if mode == "plain_url":
            ctn.plain_url_mode = True
            ctn.src_url = src_url
            ctn.src_oburl = util.obfuscate_source_url(src_url)
        else:
            ctn.plain_url_mode = False
            try:
                ctn.src_url = util.deobfuscate_source_url(src_url)
            except ValueError as ve:
                return render_error_page(request, ve.args[0])
            ctn.src_oburl = src_url

        md_src_url = f"{ctn.src_url}/export/txt"
        try:
            src_txt = get_md_src_or_raise_error(md_src_url)
        except ValueError as ve:
            return render_error_page(request, ve.args[0])

        ctn.src_txt = src_txt

        raw_html = util.render_markdown(src_txt)
        ctn.enable_mathjax = util.recognize_mathjax(raw_html)
        ctn.sanitized_html = util.custom_bleach(raw_html, ctn.enable_mathjax)

        context = {"ctn": ctn}
        return render(request, "mainapp/md_preview.html", context)


class StaticContent(View):
    """
    Render the plain txt-content of a pad-url as markdown.
    """

    # noinspection PyMethodMayBeStatic
    def get(self, request, key=None):
        ctn = Container()

        try:
            block = static_page_blocks[key]
        except KeyError:
            raise Http404(f"unknown static-page-key: {key}")

        ctn.title = block.title
        ctn.src_txt = block.content

        context = {"ctn": ctn}
        return render(request, "mainapp/static_page.html", context)


# noinspection PyUnresolvedReferences
def get_md_src_or_raise_error(md_src_url):

    if "--undefined-url--.net" in md_src_url:
        src_txt = f"**Error:** No source url was provided."
        return src_txt

    try:
        r = urllib.request.urlopen(md_src_url)
        src_txt = r.read().decode("utf8")
    except (urllib.error.HTTPError, urllib.error.URLError):
        msg = f"The following URL could not be read: \n\n `{md_src_url}`"
        raise ValueError(msg)
    return src_txt


def render_error_page(request, err_msg: str, prefix="**Error:**"):
    ctn = Container(err_msg=err_msg, prefix=prefix)
    context = {"ctn": ctn}
    return render(request, "mainapp/error_page.html", context)