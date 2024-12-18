$(document).ready(function () {
    // Поиск по отправителю
    $('#searchInput').on('input', function () {
        const query = $(this).val();
        filterTransactions(query, $('#typeFilter').val());
    });

    $('#typeFilter').on('change', function () {
        const type = $(this).val();
        filterTransactions($('#searchInput').val(), type);
    });

    // Кнопка "Применить"
    $('#applyFilter').on('click', function () {
        const searchQuery = $('#searchInput').val();
        const typeFilter = $('#typeFilter').val();
        filterTransactions(searchQuery, typeFilter);
    });

    function filterTransactions(searchQuery, typeFilter) {
    $.ajax({
        url: "{% url 'transactions_list' %}",
        method: "GET",
        data: {
            search: searchQuery,
            type: typeFilter
        },
        success: function (data) {
            $('#transactionsContainer').html(data);
        },
        error: function () {
            alert('Ошибка загрузки данных. Проверьте подключение.');
        }
    });
}

});