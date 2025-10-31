from django.db import models
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
import os
from django.utils import timezone

class Section(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"

class Category(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='categories', verbose_name="Раздел")
    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(verbose_name="URL")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="Родительская категория")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        unique_together = ('section', 'slug', 'parent')
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.get_full_path()

    def get_full_path(self):
        path = [self.title]
        parent = self.parent
        while parent:
            path.insert(0, parent.title)
            parent = parent.parent
        return " / ".join(path)

    def get_path(self):
        path = [self.slug]
        parent = self.parent
        while parent:
            path.insert(0, parent.slug)
            parent = parent.parent
        return "/".join(path)

class News(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='news', verbose_name="Раздел")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='news', verbose_name="Категория")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    content = RichTextUploadingField(blank=True, verbose_name="Содержание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-created_at']

class NewsFile(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='files', verbose_name="Новость")
    file = models.FileField(upload_to='news_files/', verbose_name="Файл")
    filename = models.CharField(max_length=255, blank=True, verbose_name="Имя файла")
    # ✅ Добавляем поле created_at
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = self.file.name
        if not self.id:  # Только при создании
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.filename

    class Meta:
        verbose_name = "Файл новости"
        verbose_name_plural = "Файлы новостей"
        ordering = ['-created_at']

class ViewStatistic(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    path = models.CharField(max_length=500, verbose_name="Путь")
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Раздел")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    news = models.ForeignKey(News, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Новость")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Статистика просмотров"
        verbose_name_plural = "Статистика просмотров"
        ordering = ['-created_at']

class DownloadStatistic(models.Model):
    news_file = models.ForeignKey(NewsFile, on_delete=models.CASCADE, verbose_name="Файл")
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Время скачивания")

    class Meta:
        verbose_name = "Статистика скачиваний"
        verbose_name_plural = "Статистика скачиваний"
        ordering = ['-downloaded_at']