// Гівно-гівна
var orders = [];
var filteredOrders = [];

var minPrice;
var maxPrice;
var minDate;
var maxDate;
var countOrders_ofStatuses = {};
var countOrders_ofPupils = {};

var statusFilter;
var pupilFilter;
const minRangeBetweenPrices = 1;
var priceRangeElement;
var priceInputRanges;
var priceInputNumbers;
var fromDateInput;
var toDateInput;

var selectedPupils = [];
var selectedStatuses = [];
var enteredMinPrice;
var enteredMaxPrice;
var selectedFromDate = undefined;
var selectedToDate = undefined;
var selectedSort;

function toNormalDate(date) {
    return new Date(date).toISOString().split('T')[0];
}

function reviewOrders() {
    if (orders.length > 1) {
        // Ініціалізуємо змінні значеннями першого замовлення
        const firstOrder = orders[0];
        minPrice = parseFloat(firstOrder.fields.price);
        maxPrice = parseFloat(firstOrder.fields.price);
        minDate = toNormalDate(firstOrder.fields.datetime);
        maxDate = toNormalDate(firstOrder.fields.datetime);

        // Проходимося по всіх замовленнях
        for (const order of orders) {
            const price = parseFloat(order.fields.price);
            const date = toNormalDate(order.fields.datetime);

            // Оновлюємо мінімальну та максимальну ціну
            if (price < minPrice) {
                minPrice = price;
            }
            if (price > maxPrice) {
                maxPrice = price;
            }

            // Оновлюємо мінімальну та максимальну дату
            if (date < minDate) {
                minDate = date;
            }
            if (date > maxDate) {
                maxDate = date;
            }

            // Рахуємо кількість замовлень за кожним статусом
            const status = order.fields.status;
            if (status in countOrders_ofStatuses) {
                countOrders_ofStatuses[status]++;
            } else {
                countOrders_ofStatuses[status] = 1;
            }

            // Рахуємо кількість замовлень для кожного учня
            const pupil = order.fields.pupil_id;
            if (pupil in countOrders_ofPupils) {
                countOrders_ofPupils[pupil]++;
            } else {
                countOrders_ofPupils[pupil] = 1;
            }
        }
        console.log(minPrice, "|", maxPrice);
        console.log(minDate, "|", maxDate);
        console.log(countOrders_ofStatuses);
        console.log(countOrders_ofPupils);
    }
    else {
        // TODO: всього одне замовлення, може обійтись без фільтрів та сортування
    }
}

async function getOrders() {
    try {
        const response = await fetch('/get/orders');
        const data = await response.json();
        console.log("getOrders:data:", data);
        const orders = JSON.parse(data);
        console.log("getOrders:orders:", orders);
        return orders;
    } catch (error) {
        console.error('getOrders:Сталася помилка:', error);
        return undefined;
    }
}
// (async () => {
//     try {
//         const orders = await getOrders();
//     } catch (error) {
//          console.error('Сталася помилка під час отримання списку замовлень:', error);
//     }
// })();


function updateSelectedPupils() {
    selectedPupils = [];
    $('.pupil-checkbox:checked').each(function() {
        selectedPupils.push(parseInt($(this).val()));
    });
}

function updateSelectedStatuses() {
    selectedStatuses = [];
    $('.status-checkbox:checked').each(function() {
        selectedStatuses.push(parseInt($(this).val()));
    });
}

function checkEnteredMinPrice() {
    if (enteredMinPrice < minPrice) {
        enteredMinPrice = minPrice;
    }
    if (enteredMinPrice >= enteredMaxPrice - minRangeBetweenPrices) {
        enteredMinPrice = enteredMaxPrice - minRangeBetweenPrices;
    }
}

function checkEnteredMaxPrice() {
    if (enteredMaxPrice > maxPrice) {
        enteredMaxPrice = maxPrice;
    }
    if (enteredMaxPrice <= enteredMinPrice + minRangeBetweenPrices) {
        enteredMaxPrice = enteredMinPrice + minRangeBetweenPrices;
    }
}

function updatePriceSlider() {
    priceRangeElement.style.left = ((enteredMinPrice - minPrice) / (maxPrice - minPrice)) * 100 + "%";
    priceRangeElement.style.right = 100 - ((enteredMaxPrice - minPrice) / (maxPrice - minPrice)) * 100 + "%";
}

function updateInputPriceValuesByEntereds() {
    priceInputNumbers[0].value = enteredMinPrice;
    priceInputRanges[0].value = enteredMinPrice;
    priceInputNumbers[1].value = enteredMaxPrice;
    priceInputRanges[1].value = enteredMaxPrice;
}

function updateSelectedFromDateInput() {
    selectedFromDate = document.querySelector("#from-date").value;
}

function updateSelectedToDateInput() {
    selectedToDate = document.querySelector("#to-date").value;
}

function DayDate(datetime){
    let date  = toNormalDate(datetime);
    switch(new Date(datetime).getDay()){
        case 0: return 'Неділя|'    + date;
        case 1: return 'Понеділок|' + date;
        case 2: return 'Вівторок|'  + date;
        case 3: return 'Середа|'    + date;
        case 4: return 'Четвер|'    + date;
        case 5: return 'П\'ятниця|' + date;
        case 6: return 'Субота|'    + date;
    }
}

function NameStatus(statusNumber){
    switch(statusNumber){
        case 0: return 'Очікує';
        case 1: return 'Готується';
        case 2: return 'Виконано';
        case 3: return 'Скасовано';
    }
}

function updateOrdersList() {
    console.log("begin update list:", filteredOrders);
    filterOrders();
    sortBySelectedSort();
    $('#orders-list').empty();
    filteredOrders.forEach((order) => {
        //console.log("order:",  order.fields.datetime, order.fields.status);
        appendOrderToOrdersList(order);
    });
    console.log("end update list");
}

function sortBySelectedSort() {
    console.log("begin::sortBySelectedSort", selectedSort);
    switch(parseInt(selectedSort)){
        case 0:
            break;
        case 1:
            filteredOrders.sort((a, b) => a.fields.status - b.fields.status);
            break;
        case 2:
            filteredOrders.sort((a, b) => b.fields.price - a.fields.price);
            break;
        case 3:
            filteredOrders.sort((a, b) => a.fields.price - b.fields.price);
            break;
        case 4:
            filteredOrders.sort((a, b) => new Date(b.fields.datetime) - new Date(a.fields.datetime));
            break;
        case 5:
            filteredOrders.sort((a, b) => new Date(a.fields.datetime) - new Date(b.fields.datetime));
            break;
    }
    console.log("sorted list:", filteredOrders);
    console.log("end::sortBySelectedSort");
}

function filterOrders() {
    console.log("Start >>> filter")
    filteredOrders = orders.filter(order => {
        console.log("order ?:", order);
        if (!selectedStatuses.includes(order.fields.status)) {
            console.log("-status");
            return false;
        }
        if (!selectedPupils.includes(order.fields.pupil_id)) {
            console.log("-status");
            return false;
        }
        if (order.fields.price < enteredMinPrice || order.fields.price > enteredMaxPrice) {
            console.log("-price");
            return false;
        }
        if (toNormalDate(order.fields.datetime) < selectedFromDate) {
            console.log("-from-date");
            return false;
        }
        if (toNormalDate(order.fields.datetime) > selectedToDate) {
            console.log("-to-date");
            return false;
        }
        console.log("+ ok");
        return true;
    });
    console.log("filtered list:", filteredOrders);
    console.log("End >>> filter")
}

function init_Filter() {
    statusFilter = $('#status-filter');
    pupilFilter = $('#pupil-filter');
    priceRangeElement = document.querySelector(".range-selected");
    priceInputRanges = document.querySelectorAll(".range-input input");
    priceInputNumbers = document.querySelectorAll(".range-price input");
    fromDateInput = $('#from-date');
    toDateInput = $('#to-date');
    //          Обробники подій
    statusFilter.find('.status-checkbox').each(
        function() {
            $(this).on('change', updateSelectedStatuses);
            $(this).on('change', updateOrdersList);
        }
    );
    pupilFilter.find('.pupil-checkbox').each(
        function() {
            $(this).on('change', updateSelectedPupils);
            $(this).on('change', updateOrdersList);
        }
    );
    // я їбав це скорочувати, чи оптимізувати. нехай поки так буде.
    priceInputRanges.forEach((input) => {
        input.min = minPrice;
        enteredMinPrice = minPrice;
        input.max = maxPrice;
        enteredMaxPrice = maxPrice;
        if (input.className === "min") {
            input.value = minPrice;
            input.addEventListener("input", (e) => {
                enteredMinPrice = parseInt(priceInputRanges[0].value);
                checkEnteredMinPrice();
                checkEnteredMaxPrice();
                updateInputPriceValuesByEntereds();
                updatePriceSlider();
            });
        }
        else if (input.className === "max") {
            input.value = maxPrice;
            input.addEventListener("input", (e) => {
                enteredMaxPrice = parseInt(priceInputRanges[1].value);
                checkEnteredMaxPrice();
                checkEnteredMinPrice();
                updateInputPriceValuesByEntereds();
                updatePriceSlider();
            });
        }
    });
    priceInputNumbers.forEach((input) => {
        if (input.className === "min") {
            input.value = minPrice;
            input.addEventListener("input", (e) => {
                enteredMinPrice = parseInt(priceInputNumbers[0].value);
                checkEnteredMinPrice();
                checkEnteredMaxPrice();
                updateInputPriceValuesByEntereds();
                updatePriceSlider();
            });
        }
        else if (input.className === "max") {
            input.value = maxPrice;
            input.addEventListener("input", (e) => {
                enteredMaxPrice = parseInt(priceInputNumbers[1].value);
                checkEnteredMaxPrice();
                checkEnteredMinPrice();
                updateInputPriceValuesByEntereds();
                updatePriceSlider();
            });
        }
    });
    fromDateInput.on('change', updateSelectedFromDateInput);
    fromDateInput.on('change', updateOrdersList);
    document.querySelector("#from-date").value = minDate;
    toDateInput.on('change', updateSelectedToDateInput);
    toDateInput.on('change', updateOrdersList);
    document.querySelector("#to-date").value = maxDate;
}

function init_Sort() {
    sortSelect = $('#sort-select');

    if (orders.length > 1) {
        sortSelect.append($('<option>', {
            value: '1',
            text: 'По статусу',
        }));
        sortSelect.append($('<option>', {
            value: '2',
            text: 'Від дорожчого',
        }));
        sortSelect.append($('<option>', {
            value: '3',
            text: 'Від дешевшого',
        }));
        sortSelect.append($('<option>', {
            value: '4',
            text: 'Від новішого',
        }));
        sortSelect.append($('<option>', {
            value: '5',
            text: 'Від старішого',
        }));
    }
    else {
        sortSelect.empty();
    }
    sortSelect.change(function() {
        selectedSort = $(this).val();
        updateOrdersList();
    });
}

function appendOrderToOrdersList(order) {
    let htmlElement =
            `
            <div class="card">
                <a href="/order/${order.pk}/">
                    <div class="card-data">
                        <div>
                            <h3 class="sub-title">
                                ${DayDate(order.fields.datetime)}
                            </h3>
                            <h3 class="sub-title">
                                Статус: ${NameStatus(order.fields.status)}
                            </h3>
                            <div class="info">
                                <p>Дитина: <span class="regular-text">${order.fields.pupil_id}</span></p>
                                <p>Коментар: <span class="regular-text">${order.fields.comment}</span></p>
                                <p>Замовник: <span class="regular-text">${order.fields.profile_id}</span></p>
                                <p>Вартість: <span class="regular-text">${order.fields.price}грн.</span></p>
                            </div>
                        </div>
                    </div>
                </a>
            </div>
            `;
    //console.log("html:",  htmlElement);
    $('#orders-list').append(htmlElement);
}

$(document).ready(function() {
    (async () => {
        try {
            orders = await getOrders();
            if (orders.length == 1) {
                appendOrderToOrdersList(orders[0]); // TODO: test on one order
            }
            else {
                reviewOrders();
                init_Filter();
                updateSelectedPupils();
                updateSelectedStatuses();
                updatePriceSlider();
                updateSelectedFromDateInput();
                updateSelectedToDateInput();
                init_Sort();
                console.log(
                    statusFilter,
                    pupilFilter,
                    "($('#price-filter'))",
                    fromDateInput,
                    toDateInput,
                    sortSelect,
                );
                updateOrdersList();
            }
        } catch (error) {
             console.error('Сталася помилка під час отримання списку замовлень:', error);
        }
    })();
});
