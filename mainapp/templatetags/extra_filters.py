from django import template
from django.conf import settings

# noinspection PyUnresolvedReferences
from mainapp import util

register = template.Library()


render_markdown = register.filter(util.render_markdown)


@register.filter
def get_last_deployment(_):

    last_deployment = getattr(settings, "LAST_DEPLOYMENT", "<not available>")
    return last_deployment


# maybe a restart of the server is neccessary after chanching this file
