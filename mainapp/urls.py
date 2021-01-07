from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_page_view, name='landingpage'),
    path('p', views.ViewMdPreview.as_view(), name='md_preview'),
    path(r'debug', views.debug_view, name='debugpage0'),
    path(r'debug/<int:xyz>', views.debug_view, name='debugpage_with_argument'),
]
