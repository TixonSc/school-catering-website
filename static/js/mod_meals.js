var schools;
var data;
var calendar = {};
var selectedSchoolId;
var btn_add = $('#btn-add');

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);

    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
}

async function getSome(str, data) {
    url = '/get/' + str;
    data.forEach(element => {
        url += '/' + element;
    });
    try {
        const response = await fetch(url);
        console.log("request by:", url);
        const data = await response.json();
        console.log("json:", data);
        const data_dict = {
            'dates': JSON.parse(data.dates),
        };
        console.log("data:", data_dict);
        return data_dict;
    } catch (error) {
        console.error('Сталася помилка:', error);
        return undefined;
    }
}

async function getModMeals() {
    try {
        const response = await fetch('/get/mod_meals/');
        const data = await response.json();
        console.log("data:", data);
        console.log("jsondata:", JSON.parse(data));
        const data_dict = {
            'schools': JSON.parse(data.schools),
        };
        const dict_dict = {
            'schools': {}
        };
        console.log("data_dict:", data_dict);
        return data_dict;
    } catch (error) {
        console.error('Сталася помилка:', error);
        return undefined;
    }
}

async function getSchools() {
    try {
        const response = await fetch('/get/schools');
        const data = await response.json();
        console.log("data:", data);
        console.log("data:schools", JSON.parse(data.schools));
        const data_dict = {
            'schools': JSON.parse(data.schools),
        };
        console.log("data_dict:", data_dict);
        return data_dict;
    } catch (error) {
        console.error('Сталася помилка:', error);
        return undefined;
    }
}

async function getMeals(date) {
    let url = '/get/meals/' + selectedSchoolId + '/' + toNormalDate(date) + '/';
    try {
        const response = await fetch(url);
        const data = await response.json();
        // console.log("data:", data);
        // console.log("data:meals", JSON.parse(data.meals));
        const data_dict = {
            'meals': JSON.parse(data.meals),
        };
        console.log("data_dict:", data_dict);
        return data_dict;
    } catch (error) {
        console.error('Сталася помилка:', error);
        return undefined;
    }
}

function toNormalDate(date) {
    return new Date(date).toISOString().split('T')[0];
}

function firstDate() {
    var date = new Date();
    date.setDate(date.getDate() + (8 - date.getDay()));
    return date;
}

function lastDate() {
    var date = new Date();
    date.setDate(firstDate().getDate() + (3 * 7 - 1));//
    return date;
}

function rangeDate() {
    var range = [];
    first = firstDate();
    last = lastDate();
    date = first;

    while (date <= last) {
        range.push(toNormalDate(date));
        date.setDate(date.getDate() + 1);
    }
    return range;
}

function DayDate(datetime) {
    let date  = toNormalDate(datetime);
    switch(new Date(datetime).getDay()){
        case 0: return 'Неділя<br>'    + date;
        case 1: return 'Понеділок<br>' + date;
        case 2: return 'Вівторок<br>'  + date;
        case 3: return 'Середа<br>'    + date;
        case 4: return 'Четвер<br>'    + date;
        case 5: return 'П\'ятниця<br>' + date;
        case 6: return 'Субота<br>'    + date;
    }
}

function mealsDate(date) {
    (async() => {
        let data_dict = await getMeals(date);
        let meals = data_dict.meals;
        if (meals.length > 0) {
            calendar[date] = meals;
            console.log(date, meals);
        }
    })();
}

function htmlMeals(date) {
    let htmlElement = ``;
    let meals = calendar[date];
    meals.forEach(meal => {
        htmlElement +=
            `
            <div id="meal-${meal.pk}">
            ${meal}
            </div>
            `;
    });
    return htmlElement;
}

function htmlDate(date) {
    let mls;
    console.log(calendar[date]);
    if (Reflect.has(calendar, date)) {
        console.log("DATE REAL", calendar);
        mls = htmlMeals(date);
    }
    else {
        console.log("NOT REAL", calendar, "FOR", date);
        mls = "NONE";
    }

    let htmlElement =
        `
        <div class="card">
            <fieldset>
                <legend>${DayDate(date)}</legend>
                <br>
                ${mls}
            </fieldset>
        </div>
        `;
    return htmlElement;
}

function updateCalendar() {
    let first = firstDate();
    let last = lastDate();
    let range = rangeDate();

    range.forEach(date => {
        mealsDate(date);
    });
    console.log("CALENDAR", calendar);

    $('#calendar').empty();
    range.forEach(date => {
        $('#calendar').append(htmlDate(date));
    });
}

function addMeal () {
    data = {
        'date': $('#date').val(),
        'time': $('#time').val(),
        'name': $('#name').val(),
        'school_id': $('#school-select').val(),
        'menu_id': $('#menu_id').val(),
    };

    console.log("MEAL DATA:", data);

    $.ajax({
        url: '/add/meal/',
        type: 'POST',
        data: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        success: function(response) {
            console.log(response);
        }
    });
}

function btnByFields() {
    let enabled = !isValidFields()
    $('#btn-add').prop('disabled', enabled);
    console.log(btn_add);
}

function isValidFields() { 
    if($('#date').val() === '') {
        console.log("no");
        return false;
    }
    if($('#time').val() === '') {
        console.log("no");
        return false;
    }
    if($('#name').val() === '') {
        console.log("no");
        return false;
    }
    if($('#menu_id').val() === '') {
        console.log("no");
        return false;
    }
    if($('#school-select').val() === '') {
        console.log("no");
        return false;
    }
    console.log("ok");
    return true
}

$(document).ready(function() {
    (async() => {
        data = await getModMeals();
        console.log(data);

        $('#date').change(btnByFields);
        $('#time').change(btnByFields); 
        $('#name').change(btnByFields);
        $('#menu_id').change(btnByFields);
        $('#school-select').change(btnByFields);

        $('#btn-add').on('click', (event) => {
            addMeal();
            updateCalendar();
        });

        var dateSelect = document.querySelector('input[type=date]');
        dateSelect.value = toNormalDate(firstDate());
        dateSelect.min = toNormalDate(firstDate());
        dateSelect.max = toNormalDate(lastDate());

        let data_dict = await getSchools();
        schools = data_dict.schools;
        
        var schoolSelect = $('#school-select');
        for (var i = 0; i < schools.length; i++) {
            schoolSelect.append($('<option>', {
                value: schools[i].pk,
                text: schools[i].fields.name
            }));
        }
        
        schoolSelect.change(function() {
            selectedSchoolId = $(this).val();
            updateCalendar();
        });
    })();
});