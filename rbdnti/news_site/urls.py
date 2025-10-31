from django.urls import path
from . import views

app_name = 'news_site'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_news, name='search_news'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('download/<int:file_id>/', views.tracked_download, name='tracked_download'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    # ✅ Изменяем URL - убираем 'admin/' из пути
    path('ckeditor-files/', views.ckeditor_files_view, name='ckeditor_files'),
    path('delete-ckeditor-file/', views.delete_ckeditor_file, name='delete_ckeditor_file'),
    path('<slug:section_slug>/', views.section_view, name='section'),
    path('<slug:section_slug>/<path:category_path>/', views.category_view, name='category'),
]