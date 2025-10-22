document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('input[name="multiple_files"]');
    if (!fileInput) return;

    const infoDiv = document.createElement('div');
    fileInput.insertAdjacentElement('afterend', infoDiv);

    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const list = Array.from(this.files).map(f => `• ${f.name}`).join('<br>');
            infoDiv.innerHTML = `<p><b>Выбрано файлов:</b></p><div style="padding-left:10px;">${list}</div>`;
        } else {
            infoDiv.innerHTML = '';
        }
    });

    // Кнопка "Удалить все файлы"
    const inlineGroup = document.querySelector('#newsfile_set-group');
    if (inlineGroup) {
        const btn = document.createElement('button');
        btn.textContent = 'Удалить все файлы';
        btn.type = 'button';
        btn.className = 'deletelink';
        btn.style.marginBottom = '10px';
        btn.addEventListener('click', () => {
            if (confirm('Удалить все файлы этой новости?')) {
                const checkboxes = inlineGroup.querySelectorAll('input[type="checkbox"][name$="-DELETE"]');
                checkboxes.forEach(cb => cb.checked = true);
            }
        });
        inlineGroup.prepend(btn);
    }
});
