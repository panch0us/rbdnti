from django.urls import path
from . import views

app_name = 'news_site'  # ✅ Добавьте эту строку

urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:section_slug>/', views.section_view, name='section'),
    path('<slug:section_slug>/<path:category_path>/', views.category_view, name='category'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
]