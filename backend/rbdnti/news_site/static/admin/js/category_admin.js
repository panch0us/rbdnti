// category_admin.js - Чистый JavaScript для фильтрации родительских категорий
// Этот код обеспечивает динамическую фильтрацию родительских категорий в форме категорий

// Ждем полной загрузки DOM перед выполнением кода
document.addEventListener('DOMContentLoaded', function() {
    // Находим поля выбора раздела и родительской категории по их ID в HTML
    const sectionField = document.getElementById('id_section');
    const parentField = document.getElementById('id_parent');
    
    // Проверяем, что оба поля существуют на странице
    if (sectionField && parentField) {
        
        /**
         * Функция загрузки родительских категорий для выбранного раздела
         * @param {string} sectionId - ID выбранного раздела
         * @param {string} excludeId - ID категории для исключения (чтобы нельзя было выбрать себя родителем)
         * @param {string} selectedParentId - ID текущей выбранной родительской категории
         */
        function loadCategories(sectionId, excludeId = null, selectedParentId = null) {
            // Если раздел не выбран, очищаем поле родительской категории
            if (!sectionId) {
                parentField.innerHTML = '<option value="">---------</option>';
                return;
            }
            
            // Формируем URL для AJAX запроса
            let url = '/admin/news_site/category/get-parents/?section_id=' + sectionId;
            // Добавляем параметр исключения, если передан (для предотвращения циклических ссылок)
            if (excludeId) {
                url += '&exclude_id=' + excludeId;
            }
            
            // Отправляем AJAX запрос для получения родительских категорий
            fetch(url)
                .then(response => response.json())  // Преобразуем ответ в JSON
                .then(data => {
                    // Очищаем текущий список родительских категорий
                    parentField.innerHTML = '<option value="">---------</option>';
                    
                    // Добавляем каждую родительскую категорию из ответа сервера
                    data.results.forEach(function(item) {
                        const option = document.createElement('option');
                        option.value = item.id;
                        option.textContent = item.title;  // Используем полный путь категории
                        
                        // Если это редактирование существующей категории и ID совпадает, выбираем этого родителя
                        if (selectedParentId && item.id == selectedParentId) {
                            option.selected = true;
                        }
                        
                        parentField.appendChild(option);
                    });
                })
                .catch(error => {
                    // Обрабатываем ошибки при загрузке категорий
                    console.error('Error loading categories:', error);
                });
        }
        
        // Добавляем обработчик события изменения выбора раздела
        sectionField.addEventListener('change', function() {
            const sectionId = this.value;
            // Получаем ID текущей категории (если редактируем существующую)
            const currentCategoryId = document.getElementById('id_id') ? document.getElementById('id_id').value : null;
            // Загружаем категории для выбранного раздела, исключая текущую категорию
            loadCategories(sectionId, currentCategoryId);
        });
        
        // Инициализация при загрузке страницы
        // Если раздел уже выбран (при редактировании существующей категории)
        if (sectionField.value) {
            // Получаем ID текущей категории (если есть)
            const currentCategoryId = document.getElementById('id_id') ? document.getElementById('id_id').value : null;
            // Получаем текущее значение родительской категории
            const selectedParentId = parentField.value;
            
            // Загружаем категории с учетом текущего выбранного родителя
            loadCategories(sectionField.value, currentCategoryId, selectedParentId);
        }
    }
});