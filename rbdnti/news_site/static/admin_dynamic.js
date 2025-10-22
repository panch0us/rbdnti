// admin_dynamic.js
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    // === Категории (Parent) ===
    const sectionField = document.getElementById('id_section');
    const parentField = document.getElementById('id_parent');

    if (sectionField && parentField) {
      sectionField.addEventListener('change', function () {
        const sectionId = this.value;
        if (!sectionId) {
          parentField.innerHTML = '<option value="">---------</option>';
          return;
        }

        fetch(`/admin/news_site/category/get-parents/?section_id=${sectionId}`)
          .then(response => response.json())
          .then(data => {
            const results = data.results;
            parentField.innerHTML = '<option value="">---------</option>';
            results.forEach(function (item) {
              const opt = document.createElement('option');
              opt.value = item.id;
              opt.textContent = item.title;
              parentField.appendChild(opt);
            });
          });
      });
    }

    // === Новости (Category) ===
    const sectionFieldNews = document.getElementById('id_section');
    const categoryField = document.getElementById('id_category');

    if (sectionFieldNews && categoryField) {
      sectionFieldNews.addEventListener('change', function () {
        const sectionId = this.value;
        if (!sectionId) {
          categoryField.innerHTML = '<option value="">---------</option>';
          return;
        }

        fetch(`/admin/news_site/news/get-categories/?section_id=${sectionId}`)
          .then(response => response.json())
          .then(data => {
            const results = data.results;
            categoryField.innerHTML = '<option value="">---------</option>';
            results.forEach(function (item) {
              const opt = document.createElement('option');
              opt.value = item.id;
              opt.textContent = item.title;
              categoryField.appendChild(opt);
            });
          });
      });
    }
  });
})();
