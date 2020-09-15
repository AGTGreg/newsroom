from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('api/get-data/', views.get_data, name='get_data'),
    path('api/start-scraping', views.start_scaping, name="start_scraping"),

    path('edit-article/<int:pk>', views.edit_article, name="edit_article"),
]
