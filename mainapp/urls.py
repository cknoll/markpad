from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_page_view, name='landingpage'),
    path('about', views.StaticContent.as_view(), kwargs={"key": "about"}, name='about'),
    path('legal-notice', views.StaticContent.as_view(), kwargs={"key": "legal-notice"}, name='legal-notice'),
    path('p', views.ViewMdPreview.as_view(), name='md_preview'),
    path('p/<path:padurl>', views.ViewMdPreview.as_view(), name='md_preview'),
]
