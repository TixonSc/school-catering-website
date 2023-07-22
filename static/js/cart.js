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
                url: '/change-count/',
                type: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                data: { 
                    pupil_id: pupilId,
                    item_id: itemId,
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
    var meal = $('.meal[data-meal-id="' + mealId + '"]');
    var item = meal.find('.item[data-item-id="' + itemId + '"]');
    var counter = item.find('.counter');

    $.ajax({
        url: '/change-count/',
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        data: { 
            pupil_id: pupilId,
            item_id: itemId,
            meal_id: mealId,
            new_count: newCount,
        },
        success: function(response) {
            counter.text(response.count);
            if (response.count <= 0) {
                item.remove()
            }
        },
        error: function() {
            console.log('Помилка при отриманні даних для страви з ідентифікатором ' + itemId);
        }
    });
}


function getCounter(itemId, mealId) {
    var meal = $('.meal[data-meal-id="' + mealId + '"]');
    var item = meal.find('.item[data-item-id="' + itemId + '"]');
    var counter = item.find('.counter');
    return counter
}


function clickMinus(itemId, mealId) {
    var counter = getCounter(itemId, mealId)
    let newCount = parseInt(counter.text()) - 1;
    if (newCount >= 0){
        if (new_count_portions(itemId, mealId, newCount)) {
            counter.text(newCount);
    }}
}

function clickPlus(itemId, mealId) {
    var counter = getCounter(itemId, mealId)
    let newCount = parseInt(counter.text()) + 1;
    if (newCount >= 0){
        if (new_count_portions(itemId, mealId, newCount)) {
        counter.text(newCount);
    }}
}


function clickDelete(itemId, mealId) {
    new_count_portions(itemId, mealId, 0);
}