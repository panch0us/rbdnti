// category_admin.js - Чистый JavaScript для фильтрации категорий
document.addEventListener('DOMContentLoaded', function() {
    const sectionField = document.getElementById('id_section');
    const parentField = document.getElementById('id_parent');
    
    if (sectionField && parentField) {
        function loadCategories(sectionId, excludeId = null) {
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
        
        if (sectionField.value) {
            const currentCategoryId = document.getElementById('id_id') ? document.getElementById('id_id').value : null;
            loadCategories(sectionField.value, currentCategoryId);
        }
    }
});