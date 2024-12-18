// Получение элементов формы
const amountInput = document.getElementById('amount');
const cryptoSelect = document.getElementById('crypto-select');
const cryptoOutput = document.getElementById('crypto-output');
const cryptoRateInput = document.getElementById('crypto-rate');
const cryptoHiddenInput = document.getElementById('crypto-hidden');

// Функция для обновления расчета криптовалюты
function updateCryptoOutput() {
    // Получение значений из полей
    const amountInUSD = parseFloat(amountInput.value) || 0; // Сумма в USD
    const cryptoRate = parseFloat(
        cryptoSelect.options[cryptoSelect.selectedIndex].getAttribute('data-rate')
    ) || 1; // Текущий курс криптовалюты

    // Расчет количества криптовалюты с высокой точностью
    const cryptoAmount = (amountInUSD / cryptoRate).toFixed(8); // Округление до 8 знаков

    // Обновление видимого поля с округлением
    cryptoOutput.value = parseFloat(cryptoAmount).toFixed(8) + ' ' + cryptoSelect.value.toUpperCase();

    // Передача точных данных в скрытые поля
    cryptoRateInput.value = cryptoRate; // Передача курса
    cryptoHiddenInput.value = cryptoAmount; // Передача точного количества криптовалюты
}

// Добавление обработчиков событий для ввода суммы и выбора криптовалюты
amountInput.addEventListener('input', updateCryptoOutput);
cryptoSelect.addEventListener('change', updateCryptoOutput);

// Проверка данных перед отправкой формы
document.querySelector('form').addEventListener('submit', function (e) {
    const amountInUSD = parseFloat(amountInput.value) || 0; // Сумма в USD
    const cryptoRate = parseFloat(cryptoRateInput.value) || 0; // Курс криптовалюты
    const recalculatedCryptoAmount = (amountInUSD / cryptoRate).toFixed(8); // Пересчет на клиенте

    // Проверка на расхождение значений
    if (parseFloat(cryptoOutput.value) !== parseFloat(recalculatedCryptoAmount)) {
        e.preventDefault(); // Остановить отправку формы
        alert('Ошибка: расхождение в расчетах. Пожалуйста, обновите страницу.');
    }
});

// Инициализация значений при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    updateCryptoOutput();
});
