import re
from datetime import datetime
from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator
from .models import *


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        validators=[
            EmailValidator(
                message="Введіть правильну електронну пошту.",
                code='invalid_email'
            )
        ]
    )


class PupilForm(forms.ModelForm):
    date_regex = r'^(0[1-9]|[12][0-9]|3[0-1])\.(0[1-9]|1[0-2])\.\d{4}$'

    birth_date = forms.CharField(label='Дата народження')

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        if not re.match(self.date_regex, birth_date):
            raise forms.ValidationError('Некорректна дата народження!')

        # Преобразование даты в формат YYYY-MM-DD
        try:
            birth_date = datetime.strptime(birth_date, '%d.%m.%Y').strftime('%Y-%m-%d')
        except ValueError:
            raise forms.ValidationError('Некорректна дата народження!')

        return birth_date

    class Meta:
        model = Pupil
        fields = ['first_name', 'last_name', 'birth_date']
        labels = ['Ім\'я', 'Прізвище', 'Дата народження']


class ProfileForm(forms.ModelForm):
    phone_regex = r'^\+?[0-9]{1,3}\s?\(?\d{1,}\)?[-.\s]?\d{1,}[-.\s]?\d{1,}[-.\s]?\d{1,}[-.\s]?\d{1,}$'
    phone_number = forms.CharField(label='Номер телефону')

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if not re.match(self.phone_regex, phone_number):
            raise forms.ValidationError('Некорректний номер телефону!')
        return phone_number
    
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'phone_number']
        labels = {
            'first_name': 'Ім`я:',
            'last_name': 'Прізвище:',
            'phone_number': 'Номер телефону:'
        }


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['name', 'description', 'img_link'] 


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['main_dish_id', 'product_id', 'product_dish_id']


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name']


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['menu_id', 'dish_id', 'price', 'weight']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'unit_id', 'is_meat', 'is_fish', 'is_gluten', 'is_lactose', 'is_bob', 'is_glucose']
        labels = {
            'name': 'Назва продукту',
            'unit_id': 'Одиниця виміру',
            'is_meat': 'М\'ясо',
            'is_fish': 'Риба',
            'is_gluten': 'Глютен',
            'is_lactose': 'Лактоза',
            'is_bob': 'Бобові',
            'is_glucose': 'Глюкоза',
        }


class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['school_id', 'menu_id', 'name', 'date', 'time']
        labels = {
            'school_id': 'Школа',
            'menu_id': 'Меню',
            'name': 'Назва',
            'date': 'Дата',
            'time': 'Час',
        }


class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['comment']
        labels = {
            'comment': 'Коментар до замовлення',
        }
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 10, 'cols': 50})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].required = False