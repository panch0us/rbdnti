// category_admin.js - Чистый JavaScript для фильтрации категорий
document.addEventListener('DOMContentLoaded', function() {
    const sectionField = document.getElementById('id_section');
    const parentField = document.getElementById('id_parent');
    
    if (sectionField && parentField) {
        function loadCategories(sectionId, excludeId = null, selectedParentId = null) {
            if (!sectionId) {
                parentField.innerHTML = '<option value="">---------</option>';
                return;
            }
            
            let url = '/admin/news_site/category/get-parents/?section_id=' + sectionId;
            if (excludeId) {
                url += '&exclude_id=' + excludeId;
            }
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    parentField.innerHTML = '<option value="">---------</option>';
                    
                    data.results.forEach(function(item) {
                        const option = document.createElement('option');
                        option.value = item.id;
                        option.textContent = item.title;
                        
                        // Если это редактирование существующей категории, выбираем текущего родителя
                        if (selectedParentId && item.id == selectedParentId) {
                            option.selected = true;
                        }
                        
                        parentField.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Error loading categories:', error);
                });
        }
        
        sectionField.addEventListener('change', function() {
            const sectionId = this.value;
            const currentCategoryId = document.getElementById('id_id') ? document.getElementById('id_id').value : null;
            loadCategories(sectionId, currentCategoryId);
        });
        
        // Инициализация при загрузке страницы
        if (sectionField.value) {
            const currentCategoryId = document.getElementById('id_id') ? document.getElementById('id_id').value : null;
            const selectedParentId = parentField.value; // Получаем текущее значение родительской категории
            
            // Загружаем категории с учетом текущего выбранного родителя
            loadCategories(sectionField.value, currentCategoryId, selectedParentId);
        }
    }
});