// news_admin.js - Чистый JavaScript для фильтрации категорий в новостях
document.addEventListener('DOMContentLoaded', function() {
    const sectionField = document.getElementById('id_section');
    const categoryField = document.getElementById('id_category');
    
    if (sectionField && categoryField) {
        function loadCategories(sectionId) {
            if (!sectionId) {
                categoryField.innerHTML = '<option value="">---------</option>';
                return;
            }
            
            fetch('/admin/news_site/news/get-categories/?section_id=' + sectionId)
                .then(response => response.json())
                .then(data => {
                    categoryField.innerHTML = '<option value="">---------</option>';
                    
                    data.results.forEach(function(item) {
                        const option = document.createElement('option');
                        option.value = item.id;
                        option.textContent = item.title;
                        categoryField.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Error loading categories:', error);
                });
        }
        
        sectionField.addEventListener('change', function() {
            loadCategories(this.value);
        });
        
        if (sectionField.value) {
            loadCategories(sectionField.value);
        }
    }
});