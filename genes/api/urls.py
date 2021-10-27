from django.urls import path
from django.conf.urls import url
from django.urls import include
from api import views

urlpatterns = [
    path('about', views.about, name='about'),
    path('find', views.find, name='find'),
    path('search', views.search, name='search'),
    path('databases', views.databases, name='databases'),
]
