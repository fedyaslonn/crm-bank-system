document.addEventListener('DOMContentLoaded', function () {
    const tradesType = document.getElementById('id_trades_type');
    const currencyFrom = document.getElementById('id_currency_from');
    const currencyTo = document.getElementById('id_currency_to');
    const amountFrom = document.getElementById('id_amount_from');
    const amountTo = document.getElementById('id_amount_to');
    const feeAmountDisplay = document.getElementById('fee_amount');
    const transactionFeePercentage = parseFloat(document.querySelector('script').textContent.trim()); // Получаем значение из шаблона

    // Функция для блокировки/разблокировки валютных полей
    function updateFields() {
        const tradeType = tradesType.value;

        if (tradeType === 'USD_to_Crypto') {
            currencyFrom.value = 'USD';
            currencyFrom.setAttribute('disabled', 'disabled');
            currencyTo.removeAttribute('disabled');
        } else if (tradeType === 'Crypto_to_USD') {
            currencyTo.value = 'USD';
            currencyTo.setAttribute('disabled', 'disabled');
            currencyFrom.removeAttribute('disabled');
        } else {
            currencyFrom.removeAttribute('disabled');
            currencyTo.removeAttribute('disabled');
        }
    }

    // Функция для расчёта комиссии
    function calculateFee() {
        const amount = parseFloat(amountTo.value) || 0; // Значение из поля "Количество предлагаемой валюты"
        const fee = amount * (transactionFeePercentage / 100); // Рассчёт комиссии
        feeAmountDisplay.textContent = fee.toFixed(2); // Отображение комиссии с округлением до 2 знаков
    }

    // Вызов функций и добавление слушателей
    updateFields();
    tradesType.addEventListener('change', updateFields);
    amountTo.addEventListener('input', calculateFee); // Перерасчёт комиссии при изменении значения в "amount_to"
});