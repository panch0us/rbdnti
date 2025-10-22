from django.db import models
from django.urls import reverse

class Section(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

class Category(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='categories')
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        unique_together = ('section', 'slug', 'parent')

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
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='news')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='news')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news_detail', args=[str(self.id)])

class NewsFile(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='news_files/')
    filename = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.filename or self.file.name

    def get_absolute_url(self):
        return self.file.url