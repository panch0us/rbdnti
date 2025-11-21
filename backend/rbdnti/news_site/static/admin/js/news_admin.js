// news_admin.js - Чистый JavaScript для фильтрации категорий в форме новостей
// Этот код обеспечивает динамическую фильтрацию категорий в зависимости от выбранного раздела

// Ждем полной загрузки DOM перед выполнением кода
document.addEventListener('DOMContentLoaded', function() {
    // Находим поля выбора раздела и категории по их ID в HTML
    const sectionField = document.getElementById('id_section');
    const categoryField = document.getElementById('id_category');
    
    // Проверяем, что оба поля существуют на странице
    if (sectionField && categoryField) {
        
        /**
         * Функция загрузки категорий для выбранного раздела
         * @param {string} sectionId - ID выбранного раздела
         * @param {string} selectedCategoryId - ID текущей выбранной категории (для редактирования)
         */
        function loadCategories(sectionId, selectedCategoryId = null) {
            // Если раздел не выбран, очищаем поле категории
            if (!sectionId) {
                categoryField.innerHTML = '<option value="">---------</option>';
                return;
            }
            
            // Отправляем AJAX запрос для получения категорий выбранного раздела
            fetch('/admin/news_site/news/get-categories/?section_id=' + sectionId)
                .then(response => response.json())  // Преобразуем ответ в JSON
                .then(data => {
                    // Очищаем текущий список категорий
                    categoryField.innerHTML = '<option value="">---------</option>';
                    
                    // Добавляем каждую категорию из ответа сервера
                    data.results.forEach(function(item) {
                        const option = document.createElement('option');
                        option.value = item.id;
                        option.textContent = item.title;  // Используем полный путь категории
                        
                        // Если это редактирование существующей новости и ID совпадает, выбираем эту категорию
                        if (selectedCategoryId && item.id == selectedCategoryId) {
                            option.selected = true;
                        }
                        
                        categoryField.appendChild(option);
                    });
                })
                .catch(error => {
                    // Обрабатываем ошибки при загрузке категорий
                    console.error('Error loading categories:', error);
                });
        }
        
        // Добавляем обработчик события изменения выбора раздела
        sectionField.addEventListener('change', function() {
            // При изменении раздела загружаем соответствующие категории
            loadCategories(this.value);
        });
        
        // Инициализация при загрузке страницы
        // Если раздел уже выбран (при редактировании существующей новости)
        if (sectionField.value) {
            const selectedCategoryId = categoryField.value; // Получаем текущее значение категории
            // Загружаем категории для выбранного раздела, сохраняя текущую выбранную категорию
            loadCategories(sectionField.value, selectedCategoryId);
        }
    }
});