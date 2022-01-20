import os
from django.conf import settings
import re
from cryptography.fernet import Fernet
import markdown
import bleach
from bs4 import BeautifulSoup

# noinspection PyUnresolvedReferences
from ipydex import IPS, activate_ips_on_exception

# activate_ips_on_exception()


class Container(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


md = markdown.Markdown(extensions=["extra", "nl2br", "pymdownx.magiclink", "pymdownx.arithmatex"])

# Extension description:
# https://python-markdown.github.io/extensions/extra/ # tables, footnotes, ...
# https://python-markdown.github.io/extensions/nl2br/ newline to break
# https://facelessuser.github.io/pymdown-extensions/extensions/magiclink/


def render_markdown(txt):
    return md.convert(txt)


def get_static_pages() -> dict:
    with open(
        os.path.join(settings.BASEDIR, "mainapp", "static", "mainapp", "static-content.md"), "r"
    ) as txtfile:
        static_content_raw = txtfile.read()
    blocks = static_content_raw.split("<!-- --block-separator-- -->")

    pages = {}

    for block in blocks:
        pc = parse_block(block)

        # noinspection PyUnresolvedReferences
        pages[pc.slug] = pc

    return pages


def parse_block(block) -> Container:
    # <!-- slug:legal-notice -->

    slug_pattern = re.compile(r"^<!-- ::slug:(.*)-->$", re.M)
    match = slug_pattern.search(block)
    slug = match.group(1).strip()

    title_pattern = re.compile(r"^<!-- ::title:(.*)-->$", re.M)
    match = title_pattern.search(block)
    title = match.group(1).strip()

    rpl_pattern = re.compile(r"^<!-- ::.* -->$", re.M)

    # every match of that pattern should be replaced by empty string
    block2 = rpl_pattern.sub(lambda _: "", block)

    ctn = Container(slug=slug, title=title, content=block2)
    return ctn


mathjax_pattern = re.compile('.*class *=.?MathJax_Preview.*', re.MULTILINE)


def recognize_mathjax(html):
    res_iter = mathjax_pattern.finditer(html)
    try:
        next(res_iter)
    except StopIteration:
        # iterator was empty (nothing found)
        return False
    else:
        # iterator was not empty (something found)
        return True


split_url_pattern = re.compile(r"^(https?://.*?/)(.*)$")


def split_url(url: str) -> (str, str):
    match = split_url_pattern.match(url)

    if not match:
        raise ValueError(f"invalid url: {url}")

    return match.group(1), match.group(2)


def obfuscate_source_url(url: str) -> str:
    part1, part2 = split_url(url)
    res = f"{part1}{encrypt_str(part2)}"

    return res


def deobfuscate_source_url(url: str) -> str:
    part1, part2 = split_url(url)
    res = f"{part1}{decrypt_str(part2)}"
    return res


def encrypt_str(s: str) -> str:

    mybytes = s.encode("utf8")
    f = Fernet(settings.URL_ENCRYPTION_KEY)
    return f.encrypt(mybytes).decode("utf8")


def decrypt_str(s: str) -> str:
    mybytes = s.encode("utf8")
    f = Fernet(settings.URL_ENCRYPTION_KEY)
    return f.decrypt(mybytes).decode("utf8")


def custom_bleach(html_src, handle_mathjax=True):
    """
    The bleach sanitizer converts `&` → `&amp;`, `<` → `&lt;` etc.
    Inside some tags this is not desired. This function is a workaround for this.

    Idea:
    1. replace the content of the respective span and div tags with a dummy string.
    2. apply bleach
    3. perform inverse replacement


    :param html_src:        the html source which has to be sanitized
    :param handle_mathjax:  flag whether to handle mathjax. apply bleach directly if false.
    :return:            the sanitized html source
    """
    bleach_kwargs = dict(tags=settings.BLEACH_ALLOWED_TAGS, attributes=settings.BLEACH_ALLOWED_ATTRIBUTES)

    if handle_mathjax:
        soup = BeautifulSoup(html_src, 'html.parser')

        tags1 = soup.find_all("script", attrs={'type': 'math/tex'})
        tags2 = soup.find_all("script", attrs={'type': 'math/tex; mode=display'})
        tags = tags1 + tags2
        content_store = {}
        tag_template = '<{tag} type="{type_}">{content}</{tag}>'

        for i, tag in enumerate(tags):
            key = f"__replacement{i}__"
            content_store[key] = tag.contents[0]
            new_tag = tag_template.format(tag=tag.name, type_=tag.attrs["type"], content=key)
            tag.replace_with(new_tag)

        sanitized_html = bleach.clean(soup.decode(formatter=None), **bleach_kwargs)

        # apply inverse replacement (inspired by https://stackoverflow.com/a/64621297/333403)
        pattern = re.compile("|".join(content_store.keys()))
        final_sanitized_html = pattern.sub(lambda m: content_store[re.escape(m.group(0))], sanitized_html)
    else:
        # this saves time if html_src does not contain mathjax
        final_sanitized_html = bleach.clean(html_src, **bleach_kwargs)

    return final_sanitized_html
