from django.db.models import Q, Sum
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.views import View

from rest_framework.decorators import api_view # request methods GET, POST, PUT, DELETE
from rest_framework.response import Response
import json

from .models import *
from .forms import *
from .decorators import *
import datetime
import pandas

# ----------------------------------------------------------------
#   ADDITION functions
# ----------------------------------------------------------------

@login_required
def get_current_user(request) -> User:
    return request.user


@profile_required
def get_current_profile(request) -> Profile:
    if request.user:
        return Profile.objects.get(user=request.user)
    return None


def get_start_available_date(): 
    today = datetime.datetime.now().date()
    weekday_today = today.weekday()
    start_this_week_date = today - datetime.timedelta(weekday_today)
    start_next_week_date = start_this_week_date + datetime.timedelta(7 if weekday_today < 5 else 14) # перевірка на день тижня  якщо вже п'ятниця скіп на +1 тижденьІ
    return start_next_week_date


def available_dates_to_order_for_school(school_id):
    COUNT_OF_DAYS_FOR_MENU = 21
    start_next_week = get_start_available_date()
    print(f"START {start_next_week}")
    dates = list()
    for i in range(COUNT_OF_DAYS_FOR_MENU):
        day = Meal.objects.filter(
            date=(start_next_week + datetime.timedelta(i)), school_id=school_id)
        if day:
            dates.append(day[0].date)
    print(f"dates {dates}")
    return dates


def get_cart_items_by_child(child):
    return Order.objects.filter(
        pupil_id=child.pupil_id,
        profile_id=child.parent_id
    )


@api_view(['POST'])
@profile_required
def post_order_count(request):
    menu_item_id = request.POST['item_id']
    meal_id = request.POST['meal_id']
    pupil_id = request.POST['pupil_id']
    profile = get_current_profile(request)
    pupil = Pupil.objects.get(id=pupil_id)
    meal = Meal.objects.get(id=meal_id)
    menu_item = MenuItem.objects.get(id=menu_item_id)
    count = int(0)

    if 'new_count' in request.POST:
        new_count = int(request.POST['new_count'])

        if new_count > 0:
            order, flag = Order.objects.get_or_create(
                profile_id=profile,
                pupil_id=pupil,
                menu_item_id=menu_item,
                meal_id=meal,
                price=menu_item.price * (new_count - 1),
                count=(new_count - 1),
                status=Order.CART
            )
            order.count = new_count
            order.price = menu_item.price * new_count
            order.save()
            count = order.count
        else:
            try:
                order = Order.objects.get(
                    profile_id=profile,
                    pupil_id=pupil,
                    menu_item_id=menu_item,
                    meal_id=meal,
                    status=Order.CART
                )

                order.delete()

            #error not found
            except Exception as e:
                print(f"ERROR {e}") #exception

            finally:
                data = { 'count': count }

    else:
        try:
            order = Order.objects.get(
                profile_id=profile,
                pupil_id=pupil,
                menu_item_id=menu_item,
                meal_id=meal,
                status=Order.CART
            )

            count = order.count

        #error not found
        except Exception as e:
            print(f"ERROR {e}") #exception

        finally:
            pass
    data = { 'count': count }
    return JsonResponse(data)


# @api_view(['POST'])
@profile_required
def reserving_orders(request, pupil_id):
    profile = get_current_profile(request)
    pupil = Pupil.objects.get(id=pupil_id)
    child = Child.objects.get(
        pupil_id=pupil,
        parent_id=profile
    )
    
    orders_cart = Order.objects.filter(
        pupil_id=child.pupil_id,
        profile_id=profile,
        status=Order.CART,
    )

    for order in list(orders_cart):
        order.status = Order.RESERVED
        profile.debt -= order.price # TODO: defense
        order.save()
        profile.save()
    
    return redirect('orders')


@api_view(['GET'])
@profile_required
def cancel_order(request, order_id):
    Order.objects.get(id=order_id).cancel()
    return redirect('orders')


# TODO: some logs
def delete_all_overdue_orders_in_carts():
    orders = Order.objects.filter(status=Order.CART)
    next_availible_date = get_start_available_date()
    for order in orders:
        if order.meal_id.date < next_availible_date:
            order.delete()

def delete_all_overdue_orders_by_profile(profile: Profile):
    orders = Order.objects.filter(
        profile_id=profile,
        status=Order.CART
    )
    next_availible_date = get_start_available_date()
    for order in orders:
        if order.meal_id.date < next_availible_date:
            order.delete()

# ----------------------------------------------------------------
#   SERVER JSON RETRIVE FUNCS
# ----------------------------------------------------------------




@api_view(['GET'])
@profile_required
def retrieve_orders_json(request):
    profile = get_current_profile(request)
    orders = Order.objects.filter(profile_id=profile)
    orders_json = serializers.serialize('json', orders)
    return JsonResponse(orders_json, safe=False)

# Non safe JSON serialization
def json_(objects):
    return serializers.serialize('json', [objects])

@api_view(['GET'])
@profile_required
def response_mod_meals_json(request):
    today = datetime.datetime.now().date()
    endday = today + datetime.timedelta(28)
    data = {
        'schools': list(
            {
                'data': None,
                'meals': None,
            }
        ),
    }

    schools = School.objects.filter()
    for school in schools:
        meals = Meal.objects.filter(
            school_id=school,
            date__gt=today,
            date__lte=endday
        )
        data['schools'].append({
            'data': json.dumps(school),
            'meals': json_(meals)
        })
    
    return JsonResponse(data, safe=False)

@api_view(['GET'])
@profile_required
def response_meals_json(request, school_id, date):
    school = School.objects.get(id=school_id)
    meals = Meal.objects.filter(
        school_id=school,
        date=date
    )
    print(f"date {date} meals {list(meals)}")

    meals_json = serializers.serialize('json', meals)
    data = {
        'meals': meals_json,
    }
    return JsonResponse(data, safe=False)


@api_view(['GET'])
@profile_required
def retrieve_schools_json(request):
    schools = School.objects.filter()
    schools_json = serializers.serialize('json', schools)
    data = {
        'schools': schools_json,
    }
    return JsonResponse(data, safe=False)


@api_view(['GET'])
@profile_required
def retrieve_schools_and_classes_json(request):
    schools = School.objects.filter()
    classes = Class.objects.filter()
    schools_json = serializers.serialize('json', schools)
    classes_json = serializers.serialize('json', classes)
    data = {
        'schools': schools_json,
        'classes': classes_json,
    }
    return JsonResponse(data, safe=False)





# ----------------------------------------------------------------
#   USER VIEWS
# ----------------------------------------------------------------
#   Registration  | login|logout | Profile | Children | Orders
# ----------------------------------------------------------------
#   pages
# ----------------------------------------------------------------


def home_view(request):
    profile = get_current_profile(request)
    context = {
        'profile': profile,
    }
    return render(request, 'home.html', context)


# Тут шось весить з ноушн про баг
def register_view(request):
    if request.method == 'POST':
        form_data = request.POST.copy()
        form_data['username'] = form_data['username'].lower()
        form = CustomUserCreationForm(form_data)
        if form.is_valid():
            form.data['email'] = form_data['username']
            user = form.save()
            login(request, user)
            return redirect('create_profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    else:
        return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ----------------------PROFILE-------------------------------

# Create
@login_required
def create_profile_view(request):
    message = ''
    current_user = get_current_user(request)
    new_profile = Profile(user=current_user)
    form = ProfileForm(instance=new_profile)

    if request.method == 'POST':
        if 'confirm_button' in request.POST:
            form_data = request.POST.copy()
            code = form_data['school_code']
            print(f"CODE\t{code}")
            school = School.objects.filter(code=code)
            if school.count() > 0:
                form = ProfileForm(request.POST, instance=new_profile)
                if form.is_valid():
                    form.save()
                    prof = get_current_profile(request)
                    prof.school_id = school.first()
                    prof.save()
                return redirect('profile')
            else:
                message = "Не вірний код школи!"
    context = {
        'profile': new_profile,
        'form': form,
        'message': message
    }
    return render(request, 'profile/create.html', context)


# View
@profile_required
def profile_view(request):
    profile = get_current_profile(request)
    profile_form = ProfileForm(instance=profile)
    children = Child.objects.filter(parent_id=profile.id)
    verifieds = children.filter(verified=1)
    requests = children.filter(verified=0)
    context = {
        'profile': profile,
        'profile_form': profile_form,
        'verifieds': verifieds,
        'requests': requests,
    }
    return render(request, 'profile/view.html', context)


# Edit
@profile_required
def edit_profile_view(request):
    profile = get_current_profile(request)
    profile_form = ProfileForm(instance=profile)

    if request.method == 'POST':
        if 'edit_profile_button' in request.POST:
            profile_form = ProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
            return redirect('profile')

    context = {
        'profile': profile,
        'profile_form': profile_form
    }
    return render(request, 'profile/edit.html', context)

# --------------------CHILDREN---------------------------------

# View
@profile_required
def children_view(request):
    profile = get_current_profile(request)
    children = Child.objects.filter(
        parent_id=profile.id,
        verified__in=[Child.REQUEST, Child.CONFIRMED]
    )

    if not children:
        return redirect('add_child')

    cards = list()
    for child in children:
        if child.verified == Child.REQUEST:
            cards.append({'child': child, 'cart': get_cart_items_by_child(child)})
        if child.verified == Child.CONFIRMED:
            cards.append({'child': child, 'cart': None})

    context = {
        'profile': profile,
        'cards': cards,
    }
    return render(request, 'children/view.html', context)


# TODO: rework this - will optimized and shortest
# Add
@profile_required
def add_child_view(request):
    profile = get_current_profile(request)
    classes = Class.objects.filter(school_id=profile.school_id)

    if request.method == 'POST':
        if 'confirm_button' in request.POST:
            form = PupilForm(request.POST)
            if form.is_valid():
                class_id = request.POST.get('class-select')
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                birth_date = form.cleaned_data['birth_date']
                # Check if child already exists in the specified class
                existing_pupil = Pupil.objects.filter(
                    class_id=class_id,
                    first_name=first_name,
                    last_name=last_name
                ).first()

                if existing_pupil:
                    if not Child.objects.filter(
                        parent_id=profile,
                        pupil_id=existing_pupil
                    ).first():
                        # Child already exists, create a new Child object
                        child = Child.objects.create(
                            parent_id=profile,
                            pupil_id=existing_pupil,
                            verified=Child.REQUEST
                        )
                        child.save()
                else:
                    # Child doesn't exist, create a new Pupil object and then a Child object
                    class_obj = Class.objects.get(id=class_id)
                    pupil = Pupil.objects.create(
                        class_id=class_obj,
                        first_name=first_name,
                        last_name=last_name,
                        birth_date=birth_date
                    )
                    pupil.save()
                    child = Child.objects.create(
                        parent_id=profile,
                        pupil_id=pupil,
                        verified=Child.REQUEST
                    )
                    child.save()
                return redirect('children')  # Redirect to a success page
    else:
        form = PupilForm()

    context = {
        'profile': profile,
        'form': form,
        'classes': classes
    }
    return render(request, 'children/child_request.html', context)


# Delete
@api_view(['POST'])
@profile_required
@csrf_protect
def delete_child(request, child_id):
    profile = get_current_profile(request)
    child = Child.objects.get(id=child_id, parent_id=profile)
    if child:
        child.archive()
    return redirect('children')


# ----------------------------------------------------------------
#                   Menu -> Cart -> Order
# ----------------------------------------------------------------

# Menu-days
def available_menus_view(request, child_id):
    profile = get_current_profile(request)
    child = Child.objects.get(id=child_id, parent_id=profile)
    school = School.objects.get(id=profile.school_id.id)
    dates = available_dates_to_order_for_school(school)
    meals = Meal.objects.filter(school_id=school, date__in=dates)
    cards = list()

    for date in dates:
        meals_date = meals.filter(date=date)
        if meals_date:
            cards.append(
                {
                    'meals': meals_date,
                    'date': date,
                }
            )

    print(f"\n\tDATES {dates}")

    context = {
        'profile': profile,
        'cards': cards,
        'child': child,
    }
    return render(request, 'menu/dates.html', context=context)


# Menu-day
def menu_date_view(request, child_id, date):
    profile = get_current_profile(request)
    child = Child.objects.get(id=child_id)
    school = profile.school_id
    dates_of_menu = available_dates_to_order_for_school(school)
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    if not (date in dates_of_menu):
        return redirect('menus', child_id=child_id)
    
    meals = Meal.objects.filter(
        date=date,
        school_id=school
    )
    data = list()

    for meal in meals:
        data.append(
            {
                'meal': meal,
                'items': MenuItem.objects.filter(menu_id=meal.menu_id.id)
            }
        )

    context = {
        'profile': profile,
        'child': child,
        'data': data,
        'date': date,
        'dates': dates_of_menu,
    }
    return render(request, 'menu/date_menu.html', context)


# Cart
def cart_view(request, child_id):
    profile = get_current_profile(request)
    delete_all_overdue_orders_by_profile(profile)
    child = Child.objects.get(id=child_id)
    cart = Order.objects.filter(
        profile_id=profile,
        pupil_id=child.pupil_id
    )
    meal_ids = cart.values_list('meal_id', flat=True)
    meal_ids = list(set(meal_ids))
    meals = Meal.objects.filter(id__in=meal_ids)
    dates = meals.values_list('date', flat=True)
    dates = list(set(dates))

    data = {'days': list()}
    for date in dates:
        day_meals = meals.filter(date=date)
        data['days'].append({
            'date': date,
            'meals': list(
                [
                    {
                        'meal' : meal,
                        'items': cart.filter(meal_id=meal)
                    } for meal in day_meals
                ]
            ),
        })

    # orders_form = OrderForm(instance=order)
    # if request.method == 'POST':
    #     if 'confirm_button' in request.POST:
    #         for order in cart:
    #             orders_form = OrderForm(request.POST, instance=order)
    #             if orders_form.is_valid():
    #                 orders_form.save()
    #                 comment = orders_form.data['comment']
    #                 order.comment = comment
    #                 order.save()
    #         reserving_orders(request)
    #         return redirect('orders')

    context = {
        'profile': profile,
        'child': child,
        'cart': cart,
        'data': data,
        # 'comment': orders_form,
    }
    return render(request, 'cart/cart.html', context)


# Orders
@profile_required
def orders_view(request):
    profile = get_current_profile(request)
    orders = Order.objects.filter(profile_id=profile)

    if not orders.exists():
        context = {
            'profile': profile,
            'orders_json': None,
            'orders': None,
        }
        return render(request, 'orders/orders.html', context)
    
    pupil_ids = orders.values_list('pupil_id', flat=True)
    pupil_ids = list(set(pupil_ids))
    pupils = Pupil.objects.filter(id__in=pupil_ids)
    pupils_list = list(pupils)
    prices = orders.values_list('price', flat=True)
    prices = list(prices)
    context = {
        'profile': profile,
        'orders': orders,
        'pupils': pupils_list,
    }
    return render(request, 'orders/orders.html', context)


# Order by date
@profile_required
def order_view(request, order_id):
    profile = get_current_profile(request)
    children = Child.objects.filter(parent_id=profile)
    pupils = Pupil.objects.filter(id__in=children.values_list('pupil_id', flat=True))
    order = get_object_or_404(Order, pk=order_id)
    pupil = order.pupil_id

    if not (pupil in pupils):
        return redirect('orders')

    order_items = Order.objects.filter()
    meal_ids = order_items.values_list('meal_id', flat=True)
    meal_ids = list(set(meal_ids))
    meals = Meal.objects.filter(id__in=meal_ids)
    meals = meals.order_by('date', 'time')
    dates = meals.values_list('date', flat=True)
    dates = list(set(dates))

    data = {'days': list()}
    for date in dates:
        day_meals = meals.filter(date=date)
        data['days'].append({
            'date': date,
            'meals': list(
                [
                    {
                        'meal' : meal,
                        'items': order_items.filter(meal_id=meal)
                    } for meal in day_meals
                ]
            ),
        })

    context = {
        'profile': profile,
        'order': order,
        'data': data,
    }
    return render(request, 'orders/order.html', context)


# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------
#
#                    MODERATOR VIEWS
#
# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------


def sidebar_by_profile(p: Profile) -> dict:
    menu_items = {}
    if p.role == Profile.MODERATOR or p.role == Profile.ADMIN:  # модератору та адміну більшість пунктів меню
        menu_items = {
            'meals': 'Прийоми їжі',
            'list_dishes': 'Страви',
            'list_menus': 'Меню',
            'list_products': 'Продукти',
            'list_schools': 'Школи',
        }
    if p.role == Profile.SHCOOL_MANAGER:  # керівнику школи додаємо їхню школу
        menu_items['view_school'] = get_object_or_404(
            School, pk=p.school_id.id)
    if p.role == Profile.ADMIN:  # адміну пункт андміна
        menu_items['table_orders'] = 'Замовлення'
        menu_items['admin:index'] = 'Панель адміністратора'

    return menu_items


# returns dict of next week's - weekday:date
def next_week_dates(date: datetime.date):
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'НД']
    # Add the difference between the current day of the week and Monday to the input date to get the next Monday
    monday = date + datetime.timedelta(days=(7 - date.weekday()))
    # Create a dictionary of dates for the next week, starting with Monday
    dates = {day: monday + datetime.timedelta(days=i)
             for i, day in enumerate(days)}
    # Format the dates as strings in the desired format
    formatted_dates = {day: date.strftime(
        '%d.%m.%Y') for day, date in dates.items()}
    return formatted_dates


# returns dict of current week's - weekday:date
def current_week_dates(date: datetime.date):
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'НД']
    # Subtract the current day of the week from the input date to get the previous Monday
    monday = date - datetime.timedelta(days=date.weekday())
    # Create a dictionary of dates for the current week, starting with Monday
    dates = {day: monday + datetime.timedelta(days=i)
             for i, day in enumerate(days)}
    # Format the dates as strings in the desired format
    formatted_dates = {day: date.strftime(
        '%d.%m.%Y') for day, date in dates.items()}
    return formatted_dates


# Parses list of Child objects to desired list of dicts
def children2dict(raw: list, l: list = []):
    l = []
    for child in raw:
        l.append({
            'student_name': child.pupil_id.first_name + ' ' + child.pupil_id.last_name,
            'student_data': {
                'birth_date': child.pupil_id.birth_date
            },
            'school': child.pupil_id.class_id.school_id.name,
            'class': child.pupil_id.class_id.name,
            'parent_name': child.parent_id.first_name + ' ' + child.parent_id.last_name,
            'parent_data': {
                'phone_number': child.parent_id.phone_number,
                'user_email': child.parent_id.user.email
            },
            'id': child.id
        })
    return l


@role_required(Profile.ADMIN, Profile.MODERATOR) # MB: dont need
def create_empty_product(request):
    new_product = Product.objects.create(
        name='Новий продукт',
        is_meat=False,
        is_fish=False,
        is_gluten=False,
        is_lactose=False,
        is_bob=False,
        is_glucose=False
    )
    return redirect('edit_product', product_id=new_product.id)


def purchase_week_dates():
    COUNT_OF_DAYS = 7
    start_next_week = get_start_available_date()
    dates = list()
    for i in range(COUNT_OF_DAYS):
        dates.append(start_next_week + datetime.timedelta(i))
    return dates


def order_items_by_dates(dates: list):
    meals = Meal.objects.filter(date__in=dates)
    order_items = Order.objects.filter(meal_id__in=meals)
    return order_items
  

def products_from_dishes(dishes: list|Dish): # recursive function for products from dish list
    products = {}
    ingredients = Ingredient.objects.filter(main_dish_id__in=dishes)
    for ingredient in ingredients:
        if ingredient.product_dish_id:
            products.update(
                products_from_dishes(ingredient.product_dish_id)
            )
        if ingredient.product_id: # fill dict
            products[ingredient.product_id.id] = ingredient.product_id
    return products


# table PURCHASE
def table_purchase_formation():
    dates_week = purchase_week_dates()
    waiting_orders = Order.objects.filter(status=0, datetime__lt=min(dates_week))
    order_items = order_items_by_dates(
        dates_week
    ).filter(order_id__in=waiting_orders)
    dishes = [item.menu_item_id.dish_id for item in order_items]
    products = products_from_dishes(dishes)
    table = pandas.DataFrame(
        {
            'Продукти': [value.name for value in products.values()],
            'Кількість': 0, # products.values()
        },
        index=products.keys()
    )
    return table

def DataFrame_by_order_items(order_items: Order.objects.__class__):
    t_dict = {
        'Школа': [],
        'Клас': [],
        'Учень': [],
        'Прийом їжі': [],
        'Дата': [],
        'Час': [],
        'Страва': [],
        'Порцій': [],
        'Вага порції': [],
    }
    for order_item in order_items:
        t_dict['Школа'].append(order_item.order_id.pupil_id.class_id.school_id.name)
        t_dict['Клас'].append(order_item.order_id.pupil_id.class_id.name)
        t_dict['Учень'].append(order_item.order_id.pupil_id.info())
        t_dict['Прийом їжі'].append(order_item.meal_id.name)
        t_dict['Дата'].append(order_item.meal_id.date)
        t_dict['Час'].append(order_item.meal_id.time)
        t_dict['Страва'].append(order_item.menu_item_id.dish_id.name)
        t_dict['Порцій'].append(order_item.count_portion)
        t_dict['Вага порції'].append(order_item.menu_item_id.weight)
    return pandas.DataFrame(t_dict)


def order_items_by_data(data:dict, status) -> Order.objects.__class__:
    date = data['date'] or datetime.datetime.today().date()
    school_id = data['school']
    class_id = data['class']
    
    if school_id == "all":
        schools = School.objects.all()
        classes = Class.objects.filter(school_id__in=schools)
        pupils = Pupil.objects.filter(class_id__in=classes)
        meals = Meal.objects.filter(date=date, school_id__in=schools)
        orders = Order.objects.filter(
            status=status, 
            datetime__lt=date,
            pupil_id__in=pupils
        )
        order_items = Order.objects.filter(meal_id__in=meals, order_id__in=orders)
        return order_items

    elif class_id == "all":
        classes = Class.objects.filter(school_id=school_id)
        pupils = Pupil.objects.filter(class_id__in=classes)
        meals = Meal.objects.filter(date=date, school_id=school_id)
        orders = Order.objects.filter(
            status=status, 
            datetime__lt=date,
            pupil_id__in=pupils
        )
        order_items = Order.objects.filter(meal_id__in=meals, order_id__in=orders)
        return order_items

    else:
        pupils = Pupil.objects.filter(class_id=class_id)
        meals = Meal.objects.filter(date=date, school_id=school_id)
        orders = Order.objects.filter(
            status=status, 
            datetime__lt=date,
            pupil_id__in=pupils
        )
        order_items = Order.objects.filter(meal_id__in=meals, order_id__in=orders)
        return order_items


# table COOKING
def table_cooking_formation(data):
    
    order_items = order_items_by_data(data, 0)
    return DataFrame_by_order_items(order_items)


# table PREPARE
def table_prepare_formation(data):

    order_items = order_items_by_data(data, 1)
    return DataFrame_by_order_items(order_items)


def table_by_request(data):
    print(f"data:{data}")
    template_name = data['template']
    table = None
    match template_name:
        case "purchase":
            table = table_purchase_formation()
        case 'cooking':
            table = table_cooking_formation(data)
        case 'prepare':
            data['date'] = datetime.datetime.today().date()
            table = table_prepare_formation(data)
        case _:
            print(f"\ERROR: non correct request template name {template_name}")
    print(f"\n--Table--:\n{table}")
    return table


def table_to_json_responce(table: pandas.DataFrame):
    table_json = json.loads(table.to_json())
    print(f"JSON format:\n{table_json}")
    return table_json


def table_to_html_responce(table: pandas.DataFrame):
    table_html = table.to_html()
    print(f"HTML format:\n{table_html}")
    return HttpResponse(table_html)


def table_to_csv_responce(table: pandas.DataFrame):
    csv_data = table.to_csv(index=False)
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    return response


@api_view(['POST'])
@role_required(Profile.ADMIN)
def retrieve_table(request):
    table = table_by_request(request.data)
    if request.data['need'] == "html":
        return table_to_html_responce(table)
    if request.data['need'] == "file":
        return table_to_csv_responce(table)
    

@api_view(['POST'])
@role_required(Profile.ADMIN)
def add_meal(request):
    print(f"POST MEAL {request.data}")
    data = request.data
    date = data['date']
    time = data['time']
    name = data['name']
    school_id = int(data['school_id'])
    menu_id = int(data['menu_id'])
    school = School.objects.get(id=school_id)
    menu = Menu.objects.get(id=menu_id)
    meal = Meal.objects.create(
        date=date,
        time=time,
        name=name,
        school_id=school,
        menu_id=menu
    )
    meal.save()
    print(f"MEAL {meal}")
    data = {
        "success": False
    }
    return JsonResponse(data)

# ----------------------------------------------------------------
#           MOD VIEWS
# ----------------------------------------------------------------

def custom_render(request, file_path, additional_context: dict = {}):
    profile = get_current_profile(request)
    context = {
        'profile': profile,
        'sidebar': sidebar_by_profile(profile),
    }
    context.update(additional_context)
    return render(request, file_path, context)

# LISTS


@profile_required
def mod_index(request):
    return custom_render(request, 'mod/base_mod.html')


@csrf_protect
@role_required(Profile.ADMIN, Profile.MODERATOR)
def mod_list_dishes(request):
    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        if dish_id and request.POST.get('action') == 'archive':
            dish = Dish.objects.get(id=dish_id)
            dish.archive()
        return redirect('list_dishes')
    dishes = Dish.objects.all()
    return custom_render(request, 'mod/list_dishes.html', {'dishes': dishes})


@profile_required
@role_required(Profile.ADMIN)
def mod_table_orders(request):
    return custom_render(request, 'mod/tables/table_orders.html')

@role_required(Profile.ADMIN, Profile.MODERATOR)
def mod_list_menus(request):
    menus = Menu.objects.all()
    return custom_render(request, 'mod/list_menus.html', {'menus': menus})


@role_required(Profile.ADMIN, Profile.MODERATOR)
def mod_list_products(request):
    products = Product.objects.all()
    return custom_render(request, 'mod/list_products.html', {'products': products})


# REGISTER CHILD REQUESTS
@api_view(['POST'])
@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.SHCOOL_MANAGER,
    Profile.CLASS_MANAGER
)
def update_request(request, child_id, status):
    if status not in [Child.VERIFIED]:
        print(f"ERROR - Wrong status in request : {status}")
        return redirect('applications')
    
    child = Child.objects.get(pk=child_id)

    if child.verified == Child.CONFIRMED and Order.objects.filter(pupil_id=child.pupil_id, status=Order.ACCEPTED).exists():
        # TODO: error "this child have some orders in waiting"
        return redirect('applications')
    
    child.verified = status
    child.save()
    if status == Child.REQUEST or status == Child.REJECTED:
        Order.objects.filter(
            pupil_id=child.pupil_id,
            status=Order.CART
        ).delete()
        return redirect('applications')
    # TODO: error "status not normal"
    return redirect('applications')
    

# TODO: full rework whith html
@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR,
    Profile.SHCOOL_MANAGER,
    Profile.CLASS_MANAGER
)
def applications_page(request):
    profile = get_current_profile(request)
    if profile.role == Profile.ADMIN or profile.role == Profile.MODERATOR:  # mod or admin
        pending = children2dict(Child.objects.filter(verified=Child.REQUEST))
        approved = children2dict(Child.objects.filter(verified=Child.CONFIRMED))
        refused = children2dict(Child.objects.filter(verified=Child.REJECTED))
    elif profile.role == Profile.CLASS_MANAGER:  # class mod
        pending = children2dict(
            Child.objects.filter(
                verified=Child.REQUEST, 
                pupil_id__class_id=profile.class_id
            )
        )
        approved = children2dict(
            Child.objects.filter(
                verified=1,
                pupil_id__class_id=profile.class_id
            )
        )
        refused = children2dict(Child.objects.filter(
            verified=2, pupil_id__class_id=profile.class_id))
    elif profile.role == Profile.SHCOOL_MANAGER:  # school mod
        pending = children2dict(Child.objects.filter(
            verified=Child.REQUEST, pupil_id__class_id__school_id=profile.school_id))
        approved = children2dict(Child.objects.filter(
            verified=1, pupil_id__class_id__school_id=profile.school_id))
        refused = children2dict(Child.objects.filter(
            verified=2, pupil_id__class_id__school_id=profile.school_id))
    else:
        pending, approved, refused = [], [], []
    context = {
        'pending': pending,
        'approved': approved,
        'refused': refused
    }
    return custom_render(request, 'mod/applications_page.html', context)


# DISH EDIT
@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def edit_dish(request, dish_id: int):
    dish = get_object_or_404(Dish, pk=dish_id)
    ingredients = Ingredient.objects.filter(main_dish_id=dish_id)
    products = Product.objects.exclude(id__in=[ing.product_id.id for ing in ingredients if ing.product_id]) if [
        ing.product_id for ing in ingredients] else Product.objects.all()
    dishes = Dish.objects.exclude(id__in=[
        ing.product_dish_id.id for ing in ingredients if ing.product_dish_id] + [dish_id])
    dish_form = DishForm(instance=dish)
    if request.method == 'POST':
        if 'dish_button' in request.POST:
            dish_form = DishForm(request.POST, instance=dish)
            if dish_form.is_valid():
                dish_form.save()
            return redirect('list_dishes')
        elif 'product_id' in request.POST:
            ingredient_form = IngredientForm(request.POST)
            if ingredient_form.is_valid():
                ingredient_form.save()
            return redirect('edit_dish', dish_id=dish_id)
    context = {
        'page': "",
        'dish_form': dish_form,
        'dish': dish,
        'ingredients': ingredients,
        'products': products,
        'dishes': dishes,
    }
    return custom_render(request, 'mod/edit_dish.html', context)


@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def create_empty_dish(request):
    new_dish = Dish.objects.create(name='Нова Страва')
    return redirect('edit_dish', dish_id=new_dish.id)


@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def delete_ingredient(request, pk, dish_id):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        ingredient.delete() # TODO: change this to .arhive()
        return redirect('edit_dish', dish_id=dish_id)


# MENU EDIT
@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def edit_menu(request, menu_id: int):
    menu = get_object_or_404(Menu, pk=menu_id)
    menu_items = MenuItem.objects.filter(menu_id=menu_id)
    dishes = Dish.objects.exclude(id__in=[i.dish_id.id for i in menu_items if i.dish_id]) if [
        i.dish_id.id for i in menu_items] else Dish.objects.all()
    menu_form = MenuForm(instance=menu)

    if request.method == 'POST':
        if 'menu_button' in request.POST:
            menu_form = MenuForm(request.POST, instance=menu)
            if menu_form.is_valid():
                menu_form.save()
            return redirect('list_menus')
        elif 'dish_id' in request.POST:
            menu_item_form = MenuItemForm(request.POST)
            if menu_item_form.is_valid():
                menu_item_form.save()
            return redirect('edit_menu', menu_id=menu_id)
    context = {
        'menu_form': menu_form,
        'menu': menu,
        'menu_items': menu_items,
        'dishes': dishes,
    }
    return custom_render(request, 'mod/edit_menu.html', context)


@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def create_empty_menu(request):
    new_menu = Menu.objects.create(name='Нове Меню')
    return redirect('edit_menu', menu_id=new_menu.id)


@csrf_protect
def delete_menu_item(request, pk, menu_id):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        menu_item.delete() # TODO: change this to .arhive()
        return redirect('edit_menu', menu_id=menu_id)


# PRODUCT EDIT
@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('list_products')
    else:
        form = ProductForm(instance=product)
    context = {'form': form}
    return custom_render(request, 'mod/edit_product.html', context)


# MEALS EDIT
@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def mod_meals_view(request, year: int = 0, month: int = 0, day: int = 0):
    if request.method == 'POST':
        name = request.POST.get('name')
        menu_id = request.POST.get('menu_id')
        date = datetime.datetime.strptime(
            request.POST.get('date'), '%d.%m.%Y').date()
        time = request.POST.get('time')
        school_id = request.POST.get('school_id')
        school_id = School.objects.get(id=school_id)
        menu_id = Menu.objects.get(id=menu_id)
        meal = Meal(name=name, menu_id=menu_id, date=date,
                    time=time, school_id=school_id)
        meal.save()
        return redirect('meals', year=year, month=month, day=day) if year and month and day else redirect('meals')
    date = datetime.date(
        year, month, day) if year and month and day else datetime.date.today()
    week: dict = next_week_dates(date)
    # dates = [datetime.datetime.strptime(date_string, '%d.%m.%Y').strftime('%Y-%-m-%-d') for date_string in week.values()]
    dates = [datetime.datetime.strptime(
        date_string, '%d.%m.%Y').date() for date_string in week.values()]
    print(dates)
    menus = Menu.objects.all()
    schools = School.objects.all()
    meals = Meal.objects.filter(date__in=dates)
    data = {}

    for school in schools:
        print(week)
        print(datetime.datetime.strptime(week['ПН'], '%d.%m.%Y').date())
        data[school] = [
            {
                'weekday': weekday,
                'date': da,
                'meals': [meal for meal in meals if meal.date == datetime.datetime.strptime(da, '%d.%m.%Y').date() and meal.school_id == school]
            } for weekday, da in week.items()]
        print(data)
        pass
    context = {
        'meals': meals,
        'menus': menus,
        'dates': week,
        'data': data
    }
    return custom_render(request, 'mod/meals.html', context)


# SCHOOLS EDIT
def gen_classes(school: School):
    class_objects = Class.objects.filter(school_id=school)
    classes = []
    for clss in class_objects:
        c = {}  # single class temp data
        c['class_id'] = clss
        c['operators'] = list(Profile.objects.filter(
                class_id=clss, 
                role=Profile.CLASS_MANAGER
            ))
        c['pupils'] = {
            'approved': list(Pupil.objects.filter(class_id=clss, child__verified=1)),
            'pending': list(Pupil.objects.filter(class_id=clss, child__verified=0))
        }
        classes.append(c)
    return classes


@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR
)
def mod_list_schools(request):  # TODO 
    # GENERATE DICT FOR SCHOOL: CLASSES AND OPERATORS
    school_objects = School.objects.all()
    schools = []
    for school in school_objects:
        s = {}  # single school temp data
        s['school_id'] = school
        s['operators'] = list(Profile.objects.filter(
                school_id=school,
                role=Profile.SHCOOL_MANAGER
            ))
        s['classes'] = list(Class.objects.filter(school_id=school))
        schools.append(s)
    #
    context = {'schools': schools}
    return custom_render(request, 'mod/list_schools.html', context)


@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR,
    Profile.SHCOOL_MANAGER
)
def mod_view_school(request, school_id: int):
    try:
        school = School.objects.get(id=school_id)
    except School.DoesNotExist:
        return redirect('index')
    context = {'classes': gen_classes(school)}
    return custom_render(request, 'mod/view_school.html', context)


@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR,
    Profile.SHCOOL_MANAGER
)
def mod_add_operator(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = get_current_profile(request)
            if not profile.role == Profile.USER:
                return redirect(request.META.get('HTTP_REFERER'))
            if 'class_id' in request.POST:  # change privileges for class operator
                class_id = request.POST.get('class_id')
                class_instance = get_object_or_404(Class, id=class_id)
                profile.role = Profile.CLASS_MANAGER
                profile.class_id = class_instance
            # change privileges for school operator
            elif 'school_id' in request.POST and not profile.role == Profile.SHCOOL_MANAGER:
                school_id = request.POST.get('school_id')
                school_instance = get_object_or_404(School, id=school_id)
                profile.role = Profile.SHCOOL_MANAGER
                profile.school_id = school_instance
            profile.save()
            # Redirect to a success page or another URL
            return redirect(request.META.get('HTTP_REFERER'))
        except User.DoesNotExist:
            # Handle case when user does not exist
            return redirect(request.META.get('HTTP_REFERER'))
    # Handle GET requests or any other scenario
    return redirect('home')


@csrf_protect
@role_required(
    Profile.ADMIN,
    Profile.MODERATOR,
    Profile.SHCOOL_MANAGER
)
def mod_remove_privileges(request, profile_id: int):
    profile = get_object_or_404(Profile, id=profile_id)
    # Clear privileges
    profile.class_id = None
    profile.school_id = None
    profile.role = Profile.USER
    profile.save()
    return redirect(request.META.get('HTTP_REFERER'))


def mod_list_pupils(request):  # TODO mix with mod_request()
    pass
