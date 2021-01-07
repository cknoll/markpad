import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.urls import reverse

from ipydex import IPS


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


def debug_view(request, xyz=0):

    z = 1

    if xyz == 1:
        # start interactive shell for debugging (helpful if called from the unittests)
        IPS()

    elif xyz == 2:
        return HttpResponseServerError("Errormessage")

    return HttpResponse('Some plain message')

