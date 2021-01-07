from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.home_page_view, name='landingpage'),
    path('form/<int:form_data_len>', views.home_page_view, name='landingpage_with_form_data'),
    path(r'debug', views.debug_view, name='debugpage0'),
    path(r'debug/<int:xyz>', views.debug_view, name='debugpage_with_argument'),
]
