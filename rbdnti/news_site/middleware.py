# middleware.py
from .models import ViewStatistic, Section, Category, News
from django.utils import timezone

class StatisticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Собираем статистику только для GET запросов
        if request.method == 'GET' and not request.path.startswith('/admin/'):
            self.track_view(request)
            
        return response
    
    def track_view(self, request):
        """Простой трекинг просмотров"""
        try:
            path = request.path
            
            # Пропускаем статику и служебные пути
            if any(path.startswith(p) for p in ['/static/', '/admin/', '/favicon.ico']):
                return
                
            ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # Определяем тип страницы
            section, category, news = self.analyze_path(path)
            
            ViewStatistic.objects.create(
                ip_address=ip,
                user_agent=user_agent,
                path=path,
                section=section,
                category=category,
                news=news
            )
            
        except Exception as e:
            print(f"Error tracking view: {e}")
    
    def get_client_ip(self, request):
        """Получение IP клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def analyze_path(self, path):
        """Анализ пути для определения объекта"""
        section = None
        category = None
        news = None
        
        # Главная страница
        if path == '/':
            return None, None, None
            
        # Детальная страница новости
        elif path.startswith('/news/'):
            try:
                news_id = int(path.split('/')[-2])
                news = News.objects.filter(id=news_id).first()
                if news:
                    return news.section, news.category, news
            except (ValueError, IndexError):
                pass
                
        # Разделы и категории
        path_parts = [p for p in path.split('/') if p]
        
        if path_parts:
            # Ищем раздел
            section_slug = path_parts[0]
            section = Section.objects.filter(slug=section_slug).first()
            
            # Ищем категорию если есть дополнительные части пути
            if section and len(path_parts) > 1:
                category_path = '/'.join(path_parts[1:])
                category = self.find_category_by_path(section, category_path)
        
        return section, category, news
    
    def find_category_by_path(self, section, category_path):
        """Поиск категории по пути"""
        if not section:
            return None
            
        slugs = [slug for slug in category_path.split('/') if slug]
        if not slugs:
            return None
            
        category = None
        parent = None
        for slug in slugs:
            try:
                category = Category.objects.get(section=section, slug=slug, parent=parent)
                parent = category
            except Category.DoesNotExist:
                return None
        return category
    
    