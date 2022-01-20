from django import template

import markdown
from mainapp import util

register = template.Library()


render_markdown = register.filter(util.render_markdown)


# maybe a restart of the server is neccessary after chanching this file
