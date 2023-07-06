var schools;
var classes;

async function getSchoolsAndClasses() {
    try {
        const response = await fetch('/get/schools_classes');
        const data = await response.json();
        console.log("data:", data);
        console.log("data:schools", JSON.parse(data.schools));
        console.log("data:classes", JSON.parse(data.classes));
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

$(document).ready(function() {
    (async() => {
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
            var selectedSchoolId = $(this).val();
            var classSelect = $('#class-select');
            classSelect.empty();
            
            for (var i = 0; i < classes.length; i++) {
                if (classes[i].fields.school_id == selectedSchoolId) {
                    classSelect.append($('<option>', {
                        value: classes[i].pk,
                        text: classes[i].fields.name
                    }));
                }
            }
        });
    })();
});