from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q
import os
import random
from django.conf import settings
from .models import Section, Category, News, NewsFile, ViewStatistic, DownloadStatistic, Subdivision
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import defaultdict


def news_archive(request):
    """Архив всех новостей с пагинацией"""
    all_news = News.objects.select_related('section', 'category', 'author', 'subdivision').prefetch_related('files').all()
    
    paginator = Paginator(all_news, 100)
    page = request.GET.get('page')
    
    try:
        news_list = paginator.page(page)
    except PageNotAnInteger:
        news_list = paginator.page(1)
    except EmptyPage:
        news_list = paginator.page(paginator.num_pages)
    
    ticker_quotes = get_ticker_quotes()
    
    context = {
        'news_list': news_list,
        'total_news': all_news.count(),
        'ticker_quotes': ticker_quotes,
        'title': 'Архив новостей'
    }
    
    return render(request, 'news_site/news_archive.html', context)


def get_ticker_quotes():
    """Загружает цитаты для бегущей строки в случайном порядке"""
    quotes_file = os.path.join(settings.BASE_DIR, 'news_site', 'static', 'news_site', 'data', 'quotes.txt')
    
    try:
        with open(quotes_file, 'r', encoding='utf-8') as f:
            quotes = [line.strip() for line in f if line.strip()]
    except:
        quotes = [
            "Наука - это организованное знание. Герберт Спенсер",
            "Информация - это не знание. Альберт Эйнштейн",
            "Знание - это сила. Фрэнсис Бэкон",
            "Технология - это то, чего не было, когда мы родились. Алан Кей",
            "Будущее уже наступило, оно просто неравномерно распределено. Уильям Гибсон"
        ]
    
    random.shuffle(quotes)
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
    
    DownloadStatistic.objects.create(
        news_file=news_file,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    return redirect(news_file.file.url)


def index(request):
    sections = Section.objects.all()
    latest_news = News.objects.select_related('section', 'category', 'author', 'subdivision').prefetch_related('files')[:3]
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
    news = get_object_or_404(News.objects.select_related('author', 'subdivision').prefetch_related('files'), id=news_id)
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
    
    news_list = News.objects.select_related('section', 'category', 'author', 'subdivision').prefetch_related('files').all()
    
    if query:
        news_list = news_list.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
    
    if section_filter:
        news_list = news_list.filter(section__slug=section_filter)
    
    if category_filter:
        news_list = news_list.filter(category__id=category_filter)
    
    sections = Section.objects.all()
    
    categories = Category.objects.all()
    if section_filter:
        categories = categories.filter(section__slug=section_filter)
    
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
    """Упрощенная статистика с детальным анализом разделов и категорий"""
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    selected_section_id = request.GET.get('section_id')
    selected_category_id = request.GET.get('category_id')
    analyze_type = request.GET.get('analyze_type', 'section')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    except ValueError:
        start_date = None
        end_date = None
    
    def get_filtered_queryset(queryset, date_field='created_at'):
        filtered = queryset
        if start_date:
            filtered = filtered.filter(**{f'{date_field}__gte': start_date})
        if end_date:
            end_date_plus_one = end_date + timedelta(days=1)
            filtered = filtered.filter(**{f'{date_field}__lt': end_date_plus_one})
        return filtered
    
    news_queryset = get_filtered_queryset(News.objects.all())
    views_queryset = get_filtered_queryset(ViewStatistic.objects.all(), 'created_at')
    downloads_queryset = get_filtered_queryset(DownloadStatistic.objects.all(), 'downloaded_at')
    
    unique_users = get_filtered_queryset(ViewStatistic.objects.all(), 'created_at').values('ip_address').distinct().count()
    
    total_news_period = news_queryset.count()
    total_views_period = views_queryset.count()
    total_downloads_period = downloads_queryset.count()
    
    # Статистика по подразделениям
    subdivision_stats = {}
    all_subdivisions = Subdivision.objects.all()
    
    for subdivision in all_subdivisions:
        subdivision_news_count = news_queryset.filter(subdivision=subdivision).count()
        if subdivision_news_count > 0:
            subdivision_stats[subdivision.name] = subdivision_news_count
    
    # Сортируем по количеству новостей (убывание)
    subdivision_stats = dict(sorted(subdivision_stats.items(), key=lambda x: x[1], reverse=True))
    
    all_sections = Section.objects.all()
    
    selected_section = None
    section_categories = []
    analysis_results = None
    
    if selected_section_id:
        selected_section = get_object_or_404(Section, id=selected_section_id)
        
        def get_categories_with_paths(section, parent=None, path=""):
            categories = []
            for category in Category.objects.filter(section=section, parent=parent).order_by('title'):
                current_path = f"{path}/{category.title}" if path else category.title
                categories.append({
                    'id': category.id,
                    'title': category.title,
                    'full_path': current_path,
                    'parent': parent
                })
                categories.extend(get_categories_with_paths(section, category, current_path))
            return categories
        
        section_categories = get_categories_with_paths(selected_section)
        
        def get_all_subcategory_ids(category_id):
            category_ids = [category_id]
            for child in Category.objects.filter(parent_id=category_id):
                category_ids.extend(get_all_subcategory_ids(child.id))
            return category_ids
        
        if analyze_type == 'section' or selected_category_id:
            if analyze_type == 'section':
                target_name = selected_section.title
                
                target_news = news_queryset.filter(section=selected_section)
                
                target_files = NewsFile.objects.filter(news__section=selected_section)
                if start_date or end_date:
                    target_files = get_filtered_queryset(target_files, 'created_at')
                
                target_views = views_queryset.filter(section=selected_section)
                
                target_downloads = downloads_queryset.filter(news_file__news__section=selected_section)
                
                # Статистика по подразделениям для раздела
                section_subdivision_stats = {}
                for subdivision in all_subdivisions:
                    subdivision_news_count = target_news.filter(subdivision=subdivision).count()
                    if subdivision_news_count > 0:
                        section_subdivision_stats[subdivision.name] = subdivision_news_count
                
                section_subdivision_stats = dict(sorted(section_subdivision_stats.items(), key=lambda x: x[1], reverse=True))
                
                categories_stats = []
                for category in Category.objects.filter(section=selected_section, parent__isnull=True):
                    all_category_ids = get_all_subcategory_ids(category.id)
                    
                    cat_news = news_queryset.filter(category__in=all_category_ids)
                    
                    cat_files = NewsFile.objects.filter(news__category__in=all_category_ids)
                    if start_date or end_date:
                        cat_files = get_filtered_queryset(cat_files, 'created_at')
                    
                    cat_views = views_queryset.filter(category__in=all_category_ids)
                    
                    cat_downloads = downloads_queryset.filter(news_file__news__category__in=all_category_ids)
                    
                    # Статистика по подразделениям для категории
                    category_subdivision_stats = {}
                    for subdivision in all_subdivisions:
                        subdivision_news_count = cat_news.filter(subdivision=subdivision).count()
                        if subdivision_news_count > 0:
                            category_subdivision_stats[subdivision.name] = subdivision_news_count
                    
                    category_subdivision_stats = dict(sorted(category_subdivision_stats.items(), key=lambda x: x[1], reverse=True))
                    
                    categories_stats.append({
                        'id': category.id,
                        'title': category.title,
                        'full_path': category.get_full_path(),
                        'news_count': cat_news.count(),
                        'files_count': cat_files.count(),
                        'views_count': cat_views.count(),
                        'downloads_count': cat_downloads.count(),
                        'subdivision_stats': category_subdivision_stats
                    })
                
                analysis_results = {
                    'full_path': target_name,
                    'total_news': target_news.count(),
                    'total_files': target_files.count(),
                    'total_views': target_views.count(),
                    'total_downloads': target_downloads.count(),
                    'subdivision_stats': section_subdivision_stats,
                    'categories_stats': categories_stats
                }
                
            elif selected_category_id:
                selected_category = get_object_or_404(Category, id=selected_category_id)
                all_category_ids = get_all_subcategory_ids(selected_category_id)
                
                target_news = news_queryset.filter(category__in=all_category_ids)
                
                target_files = NewsFile.objects.filter(news__category__in=all_category_ids)
                if start_date or end_date:
                    target_files = get_filtered_queryset(target_files, 'created_at')
                
                target_views = views_queryset.filter(category__in=all_category_ids)
                
                target_downloads = downloads_queryset.filter(news_file__news__category__in=all_category_ids)
                
                # Статистика по подразделениям для категории
                category_subdivision_stats = {}
                for subdivision in all_subdivisions:
                    subdivision_news_count = target_news.filter(subdivision=subdivision).count()
                    if subdivision_news_count > 0:
                        category_subdivision_stats[subdivision.name] = subdivision_news_count
                
                category_subdivision_stats = dict(sorted(category_subdivision_stats.items(), key=lambda x: x[1], reverse=True))
                
                analysis_results = {
                    'full_path': selected_category.get_full_path(),
                    'total_news': target_news.count(),
                    'total_files': target_files.count(),
                    'total_views': target_views.count(),
                    'total_downloads': target_downloads.count(),
                    'subdivision_stats': category_subdivision_stats,
                    'categories_stats': None
                }
    
    context = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'unique_users': unique_users,
        'total_news_period': total_news_period,
        'total_views_period': total_views_period,
        'total_downloads_period': total_downloads_period,
        'subdivision_stats': subdivision_stats,
        'all_sections': all_sections,
        'selected_section_id': selected_section_id,
        'selected_category_id': selected_category_id,
        'analyze_type': analyze_type,
        'selected_section': selected_section,
        'section_categories': section_categories,
        'analysis_results': analysis_results,
        'ticker_quotes': get_ticker_quotes(),
    }
    
    return render(request, 'news_site/statistics.html', context)


@staff_member_required
def ckeditor_files_view(request):
    """Просмотр файлов, загруженных через CKEditor с рекурсивным поиском"""
    ckeditor_upload_path = os.path.join(settings.MEDIA_ROOT, 'news_files/ckeditor_uploads/')
    
    def get_files_recursively(directory):
        all_files = []
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
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
                    all_files.extend(get_files_recursively(item_path))
        return all_files
    
    files = get_files_recursively(ckeditor_upload_path)
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
        filepath = request.POST.get('filepath')
        
        if filepath:
            file_path = os.path.join(settings.MEDIA_ROOT, filepath)
        elif filename:
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