# views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
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

def search_news(request):
    """Поиск новостей по заголовку и содержанию"""
    query = request.GET.get('q', '').strip()
    section_filter = request.GET.get('section', '')
    category_filter = request.GET.get('category', '')
    
    news_list = News.objects.select_related('section', 'category').prefetch_related('files').all()
    
    # Применяем поисковый запрос
    if query:
        news_list = news_list.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
    
    # Фильтрация по разделу
    if section_filter:
        news_list = news_list.filter(section__slug=section_filter)
    
    # Фильтрация по категории
    if category_filter:
        news_list = news_list.filter(category__id=category_filter)
    
    # Сортировка по дате
    news_list = news_list.order_by('-created_at')
    
    # Получаем все разделы для фильтра
    sections = Section.objects.all()
    
    # Получаем категории для выбранного раздела
    categories = Category.objects.all()
    if section_filter:
        categories = categories.filter(section__slug=section_filter)
    
    # Находим выбранные раздел и категорию для отображения в результатах
    selected_section = None
    selected_category = None
    
    if section_filter:
        selected_section = Section.objects.filter(slug=section_filter).first()
    
    if category_filter:
        selected_category = Category.objects.filter(id=category_filter).first()
    
    ticker_quotes = get_ticker_quotes()
    
    context = {
        'news_list': news_list,
        'query': query,
        'section_filter': section_filter,
        'category_filter': category_filter,
        'sections': sections,
        'categories': categories,
        'selected_section': selected_section,
        'selected_category': selected_category,
        'ticker_quotes': ticker_quotes,
        'results_count': news_list.count(),
    }
    
    return render(request, 'news_site/search_results.html', context)

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

@staff_member_required
def ckeditor_files_view(request):
    """Просмотр файлов, загруженных через CKEditor с рекурсивным поиском"""
    ckeditor_upload_path = os.path.join(settings.MEDIA_ROOT, 'news_files/ckeditor_uploads/')
    
    def get_files_recursively(directory):
        """Рекурсивно получаем все файлы из директории и поддиректорий"""
        all_files = []
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    # Получаем относительный путь для URL
                    relative_path = os.path.relpath(item_path, settings.MEDIA_ROOT)
                    file_url = os.path.join(settings.MEDIA_URL, relative_path)
                    file_size = os.path.getsize(item_path)
                    import datetime
                    file_time = os.path.getctime(item_path)
                    uploaded_time = datetime.datetime.fromtimestamp(file_time)
                    
                    all_files.append({
                        'name': item,
                        'path': item_path,
                        'url': file_url,
                        'size': file_size,
                        'uploaded': uploaded_time,
                        'relative_path': relative_path
                    })
                elif os.path.isdir(item_path):
                    # Рекурсивно ищем файлы в поддиректориях
                    all_files.extend(get_files_recursively(item_path))
        return all_files
    
    # Получаем все файлы рекурсивно
    files = get_files_recursively(ckeditor_upload_path)
    
    # Сортируем по дате загрузки (новые сначала)
    files.sort(key=lambda x: x['uploaded'], reverse=True)
    
    context = {
        'title': 'Файлы CKEditor',
        'files': files,
        'media_url': settings.MEDIA_URL,
        'ticker_quotes': get_ticker_quotes(),
    }
    return render(request, 'admin/news_site/ckeditor_files.html', context)

@staff_member_required
def delete_ckeditor_file(request):
    """Удаление файла CKEditor"""
    if request.method == 'POST':
        filename = request.POST.get('filename')
        filepath = request.POST.get('filepath')  # Полный путь к файлу
        
        if filepath:
            # Используем полный путь для удаления
            file_path = os.path.join(settings.MEDIA_ROOT, filepath)
        elif filename:
            # Старый способ для обратной совместимости
            file_path = os.path.join(settings.MEDIA_ROOT, 'news_files/ckeditor_uploads/', filename)
        else:
            messages.error(request, 'Не указан файл для удаления')
            return redirect('news_site:ckeditor_files')
            
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                messages.success(request, f'Файл "{os.path.basename(file_path)}" успешно удален')
            else:
                messages.error(request, f'Файл не найден: {file_path}')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении файла: {str(e)}')
        
    return redirect('news_site:ckeditor_files')