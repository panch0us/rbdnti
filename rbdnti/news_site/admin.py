from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import format_html
from .models import News, NewsFile, Section, Category

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
    list_display = ('title', 'section', 'category', 'created_at', 'files_count')
    list_filter = ('section', 'category', 'created_at')
    inlines = [NewsFileInline]
    
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
        ]
        return custom_urls + urls

    def upload_files_view(self, request, news_id):
        news = get_object_or_404(News, id=news_id)

        if request.method == 'POST':
            # Получаем файлы напрямую из request.FILES
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

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context['upload_files_url'] = f'/admin/news_site/news/{object_id}/upload-files/'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'parent', 'get_full_path')
    list_filter = ('section', 'parent')
    prepopulated_fields = {'slug': ('title',)}
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.section:
            form.base_fields['parent'].queryset = Category.objects.filter(section=obj.section)
        return form

@admin.register(NewsFile)
class NewsFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'news', 'file')
    list_filter = ('news__section',)
    search_fields = ('filename', 'news__title')