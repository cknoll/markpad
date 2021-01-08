from django import template

import markdown

register = template.Library()
md = markdown.Markdown(extensions=['extra'])


@register.filter
def render_markdown(txt):
    return md.convert(txt)

# maybe a restart of the server is neccessary after chanching this file
