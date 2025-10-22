from django.urls import path
from . import views

app_name = 'news_site'

urlpatterns = [
    path('', views.index, name='index'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    path('<slug:section_slug>/', views.section_view, name='section'),
    path('<slug:section_slug>/<path:category_path>/', views.category_view, name='category'),
]