from django import forms
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import format_html
from django.http import JsonResponse

from .models import News, NewsFile, Section, Category, DownloadStatistic, Subdivision, TickerQuote

@admin.register(Subdivision)
class SubdivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)
    search_fields = ('name',)

class NewsFileInline(admin.TabularInline):
    model = NewsFile
    extra = 1
    fields = ('file', 'filename', 'download_link')
    readonly_fields = ('download_link',)
    
    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" download>📥 Скачать</a>', obj.file.url)
        return "-"
    
    download_link.short_description = "Скачать"

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'category', 'subdivision', 'author', 'order', 'created_at', 'files_count')
    list_filter = ('section', 'category', 'subdivision', 'author', 'created_at')
    search_fields = ('title', 'content')
    list_editable = ('order',)
    inlines = [NewsFileInline]
    
    # ✅ ДОБАВЛЕНО: Подключение JavaScript для фильтрации категорий
    class Media:
        js = ('admin/js/news_admin.js',)
    
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def files_count(self, obj):
        return obj.files.count()
    
    files_count.short_description = "Файлов"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:news_id>/upload-files/',
                self.admin_site.admin_view(self.upload_files_view),
                name='news_upload_files',
            ),
            path(
                'get-categories/',
                self.admin_site.admin_view(self.get_categories),
                name='news_get_categories',
            ),
        ]
        return custom_urls + urls

    def upload_files_view(self, request, news_id):
        news = get_object_or_404(News, id=news_id)

        if request.method == 'POST':
            files = request.FILES.getlist('files')
            if files:
                uploaded_count = 0
                for f in files:
                    NewsFile.objects.create(news=news, file=f, filename=f.name)
                    uploaded_count += 1
                
                self.message_user(
                    request, 
                    f"Успешно загружено файлов: {uploaded_count}", 
                    messages.SUCCESS
                )
            else:
                self.message_user(request, "Файлы не были выбраны", messages.WARNING)
                
            return redirect(f'/admin/news_site/news/{news_id}/change/')

        context = {
            'opts': self.model._meta,
            'news': news,
            'title': f"Массовая загрузка файлов для: {news.title}",
        }
        return render(request, 'admin/news_site/multi_upload.html', context)

    def get_categories(self, request):
        section_id = request.GET.get('section_id')
        if section_id:
            # ✅ ИСПРАВЛЕНО: Фильтруем категории по выбранному разделу
            categories = Category.objects.filter(section_id=section_id)
            results = [{'id': cat.id, 'title': cat.get_full_path()} for cat in categories]
            return JsonResponse({'results': results})
        return JsonResponse({'results': []})

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'subdivision', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'parent', 'subdivision', 'order', 'get_full_path')
    list_filter = ('section', 'parent', 'subdivision')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('title',)}
    
    class Media:
        js = ('admin/js/category_admin.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.section:
            form.base_fields['parent'].queryset = Category.objects.filter(section=obj.section)
        return form

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'get-parents/',
                self.admin_site.admin_view(self.get_parents),
                name='category_get_parents',
            ),
        ]
        return custom_urls + urls

    def get_parents(self, request):
        section_id = request.GET.get('section_id')
        if section_id:
            exclude_id = request.GET.get('exclude_id')
            categories = Category.objects.filter(section_id=section_id)
            if exclude_id:
                categories = categories.exclude(id=exclude_id)
            
            results = [{'id': cat.id, 'title': cat.get_full_path()} for cat in categories]
            return JsonResponse({'results': results})
        return JsonResponse({'results': []})

@admin.register(NewsFile)
class NewsFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'news', 'file', 'download_link', 'created_at')
    list_filter = ('news__section', 'created_at')
    search_fields = ('filename', 'news__title')
    readonly_fields = ('download_link', 'created_at')
    
    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" download>📥 Скачать</a>', obj.file.url)
        return "-"
    
    download_link.short_description = "Скачать"

@admin.register(DownloadStatistic)
class DownloadStatisticAdmin(admin.ModelAdmin):
    list_display = ['news_file', 'ip_address', 'downloaded_at']
    list_filter = ['downloaded_at']
    search_fields = ['news_file__filename', 'ip_address']




class TickerQuoteAdminForm(forms.ModelForm):
    txt_file = forms.FileField(
        required=False,
        label="Загрузить файл с цитатами (.txt)",
        help_text="Файл будет разбит по строкам. Существующие цитаты будут удалены."
    )
    
    class Meta:
        model = TickerQuote
        fields = ['txt_file']

@admin.register(TickerQuote)
class TickerQuoteAdmin(admin.ModelAdmin):
    form = TickerQuoteAdminForm
    list_display = ['text_preview', 'created_at']
    actions = ['delete_all_quotes']
    
    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = "Текст цитаты"
    
    def save_model(self, request, obj, form, change):
        txt_file = form.cleaned_data.get('txt_file')
        
        if txt_file:
            # Удаляем все существующие цитаты
            TickerQuote.objects.all().delete()
            
            # Читаем и парсим файл
            content = txt_file.read().decode('utf-8').strip()
            quotes = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Создаем новые цитаты
            for quote in quotes:
                TickerQuote.objects.create(text=quote)
            
            messages.success(request, f"Успешно загружено {len(quotes)} цитат")
        else:
            super().save_model(request, obj, form, change)
    
    def delete_all_quotes(self, request, queryset):
        count = TickerQuote.objects.count()
        TickerQuote.objects.all().delete()
        messages.success(request, f"Удалено {count} цитат")
    delete_all_quotes.short_description = "Удалить все цитаты"
    
    def has_add_permission(self, request):
        # Разрешаем добавлять только если нет цитат или через загрузку файла
        return True
    
    def has_change_permission(self, request, obj=None):
        # Запрещаем редактирование отдельных цитат
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Разрешаем удаление только массовое
        return obj is None