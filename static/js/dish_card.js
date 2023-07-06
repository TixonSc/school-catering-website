function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);

    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
}


$(document).ready(function() {
    var meals = $('.meal')

    meals.each(function() {
        var mealId = $(this).data('meal-id');
        var items = $(this).find('.item');

        items.each(function() {
            var itemId = $(this).data('item-id');
            var counter = $(this).find('.counter');

            $.ajax({
                url: '/count_portions/',
                type: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                data: {
                    item_id: itemId,
                    cart_id: cartId,
                    meal_id: mealId,
                },
                success: function(response) {
                    counter.text(response.count);
                },
                error: function() {
                    console.log('Помилка при отриманні даних для страви з ідентифікатором ' + itemId);
                }
            });
        });
    });
});


// функція отримання значення лічильника з серверу
function new_count_portions(itemId, mealId, newCount) {
    console.log('new_count_portions', itemId, mealId, newCount);
    var meal = $('.meal[data-meal-id="' + mealId + '"]');
    var item = meal.find('.item[data-item-id="' + itemId + '"]');
    var counter = item.find('.counter');

    $.ajax({
        url: '/count_portions/',
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        data: {
            item_id: itemId,
            cart_id: cartId,
            meal_id: mealId,
            new_count: newCount,
        },
        success: function(response) {
            console.log('new_count_portions:SUCCESS', itemId, mealId, newCount);
            console.log('new_count_portions:RESPONCE', response);
            console.log('new_count_portions:couter', counter.text());
            counter.text(response.count);
            console.log('new_count_portions:end', counter.text());
        },
        error: function() {
            console.log('Помилка при отриманні даних для страви з ідентифікатором ' + itemId);
        }
    });
}



function getCounter(itemId, mealId) {
    console.log('getCounter:', itemId, mealId);
    var meal = $('.meal[data-meal-id="' + mealId + '"]');
    var item = meal.find('.item[data-item-id="' + itemId + '"]');
    var counter = item.find('.counter');
    console.log('getCounter:COUNTER', counter.text());
    return counter
}


function clickMinus(itemId, mealId) {
    console.log('clickMinus', itemId, mealId);
    var counter = getCounter(itemId, mealId)
    let newCount = parseInt(counter.text()) - 1;
    console.log('clickMinus:NEW_COUNT', newCount);
    if (newCount >= 0){
        if (new_count_portions(itemId, mealId, newCount)) {
            counter.text(newCount);
    }}
}

function clickPlus(itemId, mealId) {
    console.log('clickPlus', itemId, mealId);
    var counter = getCounter(itemId, mealId)
    console.log('clickMinus:COUNTER', counter.text());
    let newCount = parseInt(counter.text()) + 1;
    console.log('clickPlus:NEW_COUNT', newCount);
    if (newCount >= 0){
        if (new_count_portions(itemId, mealId, newCount)) {
        counter.text(newCount);
    }}
}
