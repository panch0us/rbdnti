# urls.py
from django.urls import path
from . import views

app_name = 'news_site'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_news, name='search_news'),  # ДОБАВИТЬ эту строку
    path('statistics/', views.statistics_view, name='statistics'),
    path('download/<int:file_id>/', views.tracked_download, name='tracked_download'),
    # СНАЧАЛА конкретные пути, ПОТОМ общие
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),  # ДОБАВЬТЕ эту строку
    path('<slug:section_slug>/', views.section_view, name='section'),
    path('<slug:section_slug>/<path:category_path>/', views.category_view, name='category'),
]