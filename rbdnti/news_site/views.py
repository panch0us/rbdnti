from django.shortcuts import render, get_object_or_404
import os
from django.conf import settings
from .models import Section, Category, News

def get_ticker_quotes():
    """Загружает цитаты для бегущей строки из файла"""
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

def index(request):
    sections = Section.objects.all()
    latest_news = News.objects.select_related('section', 'category').prefetch_related('files').order_by('-created_at')[:10]
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