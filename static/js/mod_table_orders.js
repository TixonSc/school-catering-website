var schools;
var classes;
var selectedSchoolId = 'all';
var selectedClassId = 'all';
var good_request = undefined;

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);

    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
}

async function getSchoolsAndClasses() {
    try {
        const response = await fetch('/get/schools_classes');
        const data = await response.json();
        console.log("data:", data);
        // console.log("data:schools", JSON.parse(data.schools));
        // console.log("data:classes", JSON.parse(data.classes));
        const data_dict = {
            'schools': JSON.parse(data.schools),
            'classes': JSON.parse(data.classes),
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

Date.prototype.lastDateThisWeek = function() {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + (6 - date.getDay()));
    return date;
}

function getDataFromSelectors(){
    var data = {};
    var selectedTemplate = document.querySelector('input[type=radio][name=template-radio]:checked');
    var selectedDate = document.querySelector('input[type=date]');
    var selectedDetail = document.querySelector('input[type=radio][name=detail-radio]:checked');
    selectedSchoolId;
    selectedClassId;

    switch (selectedTemplate.value) {
        case 'purchase':
            // next week
            data['template'] = 'purchase';
            break;

        case 'cooking':
            // date in this week
            data['template'] = 'cooking';
            data['date'] = selectedDate.value;
            data['school'] = selectedSchoolId;
            data['class'] = selectedClassId;
            break;

        case 'prepare':
            //only current date
            data['template'] = 'prepare';
            data['detail'] = selectedDetail.value;
            data['school'] = selectedSchoolId;
            data['class'] = selectedClassId;
            break;
    }
    // getTable(data);
    // console.log(data);
    return data;
}

async function requestTableHTML(data) {
    var htmlTable;
    data['need'] = "html";
    $.ajax({
        url: '/get/table/',  // URL вашого Django-контролера
        method: 'POST',
        data: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        success: function(response) {
            htmlTable = response;
            $('.table').empty();
            $('.table').html(htmlTable);
            console.log(htmlTable);
            if (parseInt( $('.dataframe tbody tr').length )> 0) {
                var btn = document.querySelector('#download-tab');
                btn.disabled = false;
                good_request = data
            }
            else {
                var btn = document.querySelector('#download-tab');
                btn.disabled = true;
            }
        }
    });
}

async function requestTableCSV() {
    good_request['need'] = "file";
    $.ajax({
        url: '/get/table/',  // URL вашого Django-контролера
        method: 'POST',
        data: JSON.stringify(good_request),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        xhrFields: {
            responseType: 'blob'
        },
        success: function (data) {
            var a = document.createElement('a');
            var url = window.URL.createObjectURL(data);
            a.href = url;
            a.download = 'data.csv';
            document.body.append(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        }
    });
}


function selectorsHiddens(data){
    var school_class = document.querySelector('.school-class');
    var date = document.querySelector('.date');
    var detail = document.querySelector('.detail');
    
    switch (data){
        case 'purchase':
            school_class.hidden = true;
            date.hidden = true;
            detail.hidden = true;
            break;

        case 'cooking':
            school_class.hidden = false;
            date.hidden = false;
            detail.hidden = true;
            break;

        case 'prepare':
            school_class.hidden = false;
            date.hidden = true;
            detail.hidden = false;
            break;
    }
}


// main function
$(document).ready(function() {
    (async() => {
        var templateSelects = document.querySelectorAll('.template-radio');
        templateSelects.forEach((selector) => {
            selector.addEventListener("change", (event) => {
                var selectors = document.querySelector('.selectors');
                var gen_tab_btn = document.querySelector('#gen-tab');
                gen_tab_btn.disabled = false;
                selectors.hidden = false;
                selectorsHiddens(event.target.value);
            });
        });

        var dateSelect = document.querySelector('input[type=date]');
        dateSelect.value = toNormalDate(new Date());
        dateSelect.min = toNormalDate(new Date());
        dateSelect.max = toNormalDate(new Date().lastDateThisWeek());
        
        let data_dict = await getSchoolsAndClasses();
        schools = data_dict.schools;
        classes = data_dict.classes;
        var schoolSelect = $('#school-select');
        for (var i = 0; i < schools.length; i++) {
            schoolSelect.append($('<option>', {
                value: schools[i].pk,
                text: schools[i].fields.name
            }));
        }
        schoolSelect.change(function() {
            selectedSchoolId = $(this).val();
            var classSelect = $('#class-select');
            classSelect.empty();
            classSelect.append($('<option>', {
                value: "all",
                text: "Всі класи"
            }));
            if (schoolSelect.val() != "all") {
                for (var i = 0; i < classes.length; i++) {
                    if (classes[i].fields.school_id == selectedSchoolId) {
                        classSelect.append($('<option>', {
                            value: classes[i].pk,
                            text: classes[i].fields.name
                        }));
                    }
                }
                classSelect.change(function() {
                    selectedClassId = $(this).val();
                    var schoolDetail = document.querySelector('.detail').querySelector('.school');
                    if (selectedClassId != "all") {
                        schoolDetail.hidden = true
                        schoolDetail.querySelector('#school.detail-radio').checked = false
                    }
                    else {
                        schoolDetail.hidden = false
                    }
                });
            }
        });

        var gen_tab_btn = document.querySelector('#gen-tab');
        gen_tab_btn.addEventListener('click', (event) => {
            data = getDataFromSelectors();
            requestTableHTML(data);
        });
        var download_btn = document.querySelector('#download-tab');
        download_btn.addEventListener('click', (event) => {
            requestTableCSV();
        });
    })();
});