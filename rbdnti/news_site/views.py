from django.shortcuts import render, get_object_or_404
from .models import Section, Category, News


def index(request):
    sections = Section.objects.all()
    latest_news = News.objects.select_related('section', 'category').prefetch_related('files').order_by('-created_at')[:5]
    return render(request, 'news_site/index.html', {
        'sections': sections,
        'latest_news': latest_news
    })


def section_view(request, section_slug):
    section = get_object_or_404(Section, slug=section_slug)
    categories = Category.objects.filter(section=section, parent__isnull=True)
    news_list = News.objects.filter(section=section, category__isnull=True).prefetch_related('files')
    return render(request, 'news_site/section.html', {
        'section': section,
        'categories': categories,
        'news': news_list
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

    return render(request, 'news_site/category.html', {
        'section': section,
        'category': category,
        'subcategories': subcategories,
        'news': news_list
    })


def news_detail(request, news_id):
    news = get_object_or_404(News.objects.prefetch_related('files'), id=news_id)
    return render(request, 'news_site/news_detail.html', {
        'news': news
    })