from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_page_view, name='landingpage'),
    path('p', views.ViewMdPreview.as_view(), name='md_preview'),
    path('p/<path:padurl>', views.ViewMdPreview.as_view(), name='md_preview'),
]
