# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q
import os
from django.conf import settings
from .models import Section, Category, News, NewsFile, ViewStatistic, DownloadStatistic

def get_ticker_quotes():
    """Загружает цитаты для бегущей строки"""
    quotes_file = os.path.join(settings.BASE_DIR, 'news_site', 'static', 'news_site', 'data', 'quotes.txt')
    
    try:
        with open(quotes_file, 'r', encoding='utf-8') as f:
            quotes = [line.strip() for line in f if line.strip()]
    except:
        quotes = [
            "Наука - это организованное знание. Герберт Спенсер",
            "Информация - это не знание. Альберт Эйнштейн",
            "Знание - это сила. Фрэнсис Бэкон"
        ]
    
    return quotes

def get_client_ip(request):
    """Получение IP клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def tracked_download(request, file_id):
    """Простое скачивание с трекингом БЕЗ JavaScript"""
    news_file = get_object_or_404(NewsFile, id=file_id)
    
    # Записываем статистику
    DownloadStatistic.objects.create(
        news_file=news_file,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    # Перенаправляем на реальный файл
    return redirect(news_file.file.url)

def index(request):
    sections = Section.objects.all()
    latest_news = News.objects.select_related('section', 'category').prefetch_related('files').order_by('-created_at')[:5]
    ticker_quotes = get_ticker_quotes()
    
    return render(request, 'news_site/index.html', {
        'sections': sections,
        'latest_news': latest_news,
        'ticker_quotes': ticker_quotes
    })

def section_view(request, section_slug):
    section = get_object_or_404(Section, slug=section_slug)
    categories = Category.objects.filter(section=section, parent__isnull=True)
    news_list = News.objects.filter(section=section, category__isnull=True).prefetch_related('files')
    ticker_quotes = get_ticker_quotes()
    
    return render(request, 'news_site/section.html', {
        'section': section,
        'categories': categories,
        'news': news_list,
        'ticker_quotes': ticker_quotes
    })

def category_view(request, section_slug, category_path):
    section = get_object_or_404(Section, slug=section_slug)
    slugs = [slug for slug in category_path.strip('/').split('/') if slug]

    category = None
    parent = None
    for slug in slugs:
        category = get_object_or_404(Category, section=section, slug=slug, parent=parent)
        parent = category

    subcategories = Category.objects.filter(parent=category)
    news_list = News.objects.filter(category=category).prefetch_related('files')
    ticker_quotes = get_ticker_quotes()

    return render(request, 'news_site/category.html', {
        'section': section,
        'category': category,
        'subcategories': subcategories,
        'news': news_list,
        'ticker_quotes': ticker_quotes
    })

def news_detail(request, news_id):
    news = get_object_or_404(News.objects.prefetch_related('files'), id=news_id)
    ticker_quotes = get_ticker_quotes()
    
    return render(request, 'news_site/news_detail.html', {
        'news': news,
        'ticker_quotes': ticker_quotes
    })

def statistics_view(request):
    """Страница статистики - упрощенная версия"""
    # Получаем параметры фильтрации
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    # Парсим даты
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    except ValueError:
        start_date = None
        end_date = None
    
    # Базовые queryset с фильтрацией
    news_queryset = News.objects.all()
    views_queryset = ViewStatistic.objects.all()
    downloads_queryset = DownloadStatistic.objects.all()
    
    if start_date:
        news_queryset = news_queryset.filter(created_at__gte=start_date)
        views_queryset = views_queryset.filter(created_at__gte=start_date)
        downloads_queryset = downloads_queryset.filter(downloaded_at__gte=start_date)
    
    if end_date:
        end_date_plus_one = end_date + timedelta(days=1)
        news_queryset = news_queryset.filter(created_at__lt=end_date_plus_one)
        views_queryset = views_queryset.filter(created_at__lt=end_date_plus_one)
        downloads_queryset = downloads_queryset.filter(downloaded_at__lt=end_date_plus_one)
    
    # Основная статистика
    total_news = News.objects.count()
    total_news_period = news_queryset.count()
    total_views = ViewStatistic.objects.count()
    total_downloads = DownloadStatistic.objects.count()
    total_views_period = views_queryset.count()
    total_downloads_period = downloads_queryset.count()
    
    # Статистика по годам
    current_year = timezone.now().year
    news_by_year = []
    views_by_year = []
    downloads_by_year = []
    
    for year in range(2020, current_year + 1):
        news_count = News.objects.filter(created_at__year=year).count()
        views_count = ViewStatistic.objects.filter(created_at__year=year).count()
        downloads_count = DownloadStatistic.objects.filter(downloaded_at__year=year).count()
        
        if news_count > 0:
            news_by_year.append({'year': year, 'count': news_count})
        if views_count > 0:
            views_by_year.append({'year': year, 'count': views_count})
        if downloads_count > 0:
            downloads_by_year.append({'year': year, 'count': downloads_count})
    
    # Популярные новости и файлы
    popular_news = News.objects.annotate(
        views_count=Count('viewstatistic')
    ).order_by('-views_count')[:10]
    
    popular_files = NewsFile.objects.annotate(
        downloads_count=Count('downloadstatistic')
    ).order_by('-downloads_count')[:10]
    
    # Последние скачивания
    recent_downloads = DownloadStatistic.objects.select_related('news_file').order_by('-downloaded_at')[:20]
    
    context = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_news': total_news,
        'total_news_period': total_news_period,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'total_views_period': total_views_period,
        'total_downloads_period': total_downloads_period,
        'news_by_year': reversed(news_by_year),
        'views_by_year': reversed(views_by_year),
        'downloads_by_year': reversed(downloads_by_year),
        'current_year': current_year,
        'popular_news': popular_news,
        'popular_files': popular_files,
        'recent_downloads': recent_downloads,
        'ticker_quotes': get_ticker_quotes(),
    }
    
    return render(request, 'news_site/statistics.html', context)