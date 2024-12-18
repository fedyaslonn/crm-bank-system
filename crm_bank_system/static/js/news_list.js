document.addEventListener('DOMContentLoaded', function () {
    const readMoreButtons = document.querySelectorAll('.read-more-btn');

    readMoreButtons.forEach(button => {
        button.addEventListener('click', function () {
            const newsId = button.getAttribute('data-news-id');
            const newsItem = document.getElementById(`news-${newsId}`);
            const shortContent = newsItem.querySelector('.short-content');
            const fullContent = newsItem.querySelector('.full-content');

            // Переключаем видимость текста
            shortContent.classList.toggle('hidden');
            fullContent.classList.toggle('hidden');

            // Изменяем текст кнопки
            if (fullContent.classList.contains('hidden')) {
                button.textContent = 'Читать полностью';
                button.classList.remove('expanded');
            } else {
                button.textContent = 'Скрыть';
                button.classList.add('expanded');
            }
        });
    });
});
