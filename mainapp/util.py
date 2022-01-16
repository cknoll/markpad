import os
from django.conf import settings
import re
from cryptography.fernet import Fernet

# noinspection PyUnresolvedReferences
from ipydex import IPS, activate_ips_on_exception

activate_ips_on_exception()


class Container(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


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


def split_url(url: str) -> (str, str):
    pattern = re.compile(r"^(https?://.*?/)(.*)$")
    match = pattern.match(url)

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
