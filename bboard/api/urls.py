from django.urls import path

from .views import bbs,BbDetailView,comments

urlpatterns = [
    path('bbs/',bbs),
    path('bbs/<int:pk>/',BbDetailView.as_view()),
    path('bbs/<int:pk>/comments/',comments),
]