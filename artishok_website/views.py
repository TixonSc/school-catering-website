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


def available_days_to_order_for_school(school):
    COUNT_OF_DAYS_FOR_MENU = 21
    start_next_week = get_start_available_date()
    dates = list()
    for i in range(COUNT_OF_DAYS_FOR_MENU):
        day = Meal.objects.filter(
            date=(start_next_week + datetime.timedelta(i)), school_id=school)
        if day:
            dates.append(day[0].date)
    return dates


def get_start_available_date(): 
    today = datetime.datetime.now().date()
    weekday_today = today.weekday()
    start_this_week_date = today - datetime.timedelta(weekday_today)
    start_next_week_date = start_this_week_date + datetime.timedelta(7 if weekday_today < 5 else 14) # перевірка на день тижня  якщо вже п'ятниця скіп на +1 тижденьІ
    return start_next_week_date


def carts_deleteORcreate_by_children(request):
    children = Child.objects.filter(profile_id=get_current_profile(request))
    to_del_cart = children.filter(verified__in=[0, 2])
    to_add_cart = children.filter(verified=1)
    for child in to_del_cart:
        Cart.objects.filter(pupil_id=child.pupil_id.id).delete()
    for child in to_add_cart:
        Cart.objects.create(pupil_id=child.pupil_id.id).save()


def get_cart_by_child(child):
    return Cart.objects.get(pupil_id=child.pupil_id.id)


@api_view(['POST'])
@profile_required
def count_portions(request):
    menu_item_id = request.POST['item_id']
    cart_id = request.POST['cart_id']
    meal_id = request.POST['meal_id']
    count = int(0)

    try:
        cart = Cart.objects.get(id=cart_id)
        menu_item = MenuItem.objects.get(id=menu_item_id)
        meal = Meal.objects.get(id=meal_id)
        cart_item = CartItem.objects.filter(
            menu_item_id=menu_item, cart_id=cart, meal_id=meal
        ).first()

        if 'new_count' in request.POST:
            new_count = int(request.POST['new_count'])

            if new_count < 0:
                data = { 'count': count }
                return JsonResponse(data)
            
            if cart_item:
                if new_count == 0:
                    cart_item.delete()
                else:
                    cart_item.count_portion = new_count
                    cart_item.save()
                    count = cart_item.count_portion
            else:
                new_cart_item = CartItem.objects.create(
                    menu_item_id=menu_item, cart_id=cart, meal_id=meal, count_portion=new_count
                )
                new_cart_item.save()
                count = new_cart_item.count_portion

        else:
            if cart_item:
                count = cart_item.count_portion
            else:
                print(f"< error 404 >")
                #error not found
    except Exception as e:
        print(f"ERROR {e}") #exception

    finally:
        data = { 'count': count }
        return JsonResponse(data)


# @api_view(['POST'])
@profile_required
def order_formation(request, cart:Cart):
    order = Order.objects.create(
        pupil_id=cart.pupil_id,
        profile_id=get_current_profile(request),
        price=0,
        datetime=datetime.datetime.now(),
        status=0,
        comment=cart.comment
    )
    price = 0

    cart_items = CartItem.objects.filter(cart_id=cart)
    for cart_item in list(cart_items):
        order_item = OrderItem.objects.create(
            order_id=order,
            menu_item_id=cart_item.menu_item_id,
            meal_id=cart_item.meal_id,
            price=cart_item.menu_item_id.price,
            count_portion=cart_item.count_portion
        )
        order_item.save()
        price += order_item.price
    
    order.price = price
    order.save()
    cart_items.delete()
    cart.comment = ""
    cart.save()
    return order


@api_view(['POST'])
@profile_required
def cancel_order(request):
    order_id = request.POST('order_id')
    order = Order.objects.get(id=order_id)

    order.price # return to balance
    # when balance will released TODO: return value of price to profile balance

    order.status = 4
    order.save()
    return redirect('orders')


# @can_access_cart()
def delete_overdue_cart_items(cart:Cart):
    cart_items = CartItem.objects.filter(cart_id=cart)
    next_availible_date = get_start_available_date()
    for cart_item in cart_items:
        if cart_item.meal_id.date < next_availible_date:
            cart_item.delete()

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
    current_user = get_current_user(request)
    new_profile = Profile(user=current_user, role=0)
    form = ProfileForm(instance=new_profile)

    if request.method == 'POST':
        if 'confirm_button' in request.POST:
            form = ProfileForm(request.POST, instance=new_profile)
            if form.is_valid():
                form.save()
            return redirect('profile')
    context = {
        'profile': new_profile,
        'form': form,
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
        parent_id=profile,
        verified__in=[0, 1]
    )

    if not children:
        return redirect('add_child')

    cards = list()
    for child in children:
        if child.verified == 1:
            cards.append({'child': child, 'cart': get_cart_by_child(child)})
        if child.verified == 0:
            cards.append({'child': child, 'cart': None})

    context = {
        'profile': profile,
        'cards': cards,
    }
    return render(request, 'children/view.html', context)


# Add
@profile_required
def add_child_view(request):
    profile = get_current_profile(request)
    schools = School.objects.all()
    classes = Class.objects.all()
    schools_json = serializers.serialize('json', schools)
    classes_json = serializers.serialize('json', classes)

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
                            verified=0
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
                        verified=0
                    )
                    child.save()
                return redirect('children')  # Redirect to a success page
    else:
        form = PupilForm()

    context = {
        'profile': profile,
        'form': form,
        'schools_json': schools_json,
        'classes_json': classes_json
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
@can_access_cart()
def menu_days_view(request, cart_id):
    profile = get_current_profile(request)
    cart = Cart.objects.get(id=cart_id)
    school = cart.pupil_id.class_id.school_id
    dates = available_days_to_order_for_school(school)
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

    context = {
        'profile': profile,
        'cart': cart,
        'cards': cards,
    }
    return render(request, 'menu/days_menu.html', context=context)


# Menu-day
@can_access_cart()
def menu_day_view(request, cart_id, date):
    profile = get_current_profile(request)
    cart = Cart.objects.get(id=cart_id)
    school = cart.pupil_id.class_id.school_id
    dates_of_menu = available_days_to_order_for_school(school)
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    if not (date in dates_of_menu):
        return redirect('menu_days', cart_id=cart.id)
    
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
        'cart': cart,
        'data': data,
        'date': date,
        'dates': dates_of_menu,
    }
    return render(request, 'menu/day_menu.html', context)


# Cart
@can_access_cart()
def cart_view(request, cart_id):
    profile = get_current_profile(request)
    cart = get_object_or_404(Cart, pk=cart_id)
    delete_overdue_cart_items(cart)
    cart_items = CartItem.objects.filter(cart_id=cart)
    meal_ids = cart_items.values_list('meal_id', flat=True)
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
                        'items': cart_items.filter(meal_id=meal)
                    } for meal in day_meals
                ]
            ),
        })

    cart_form = CartForm(instance=cart)
    if request.method == 'POST':
        if 'confirm_button' in request.POST:
            cart_form = CartForm(request.POST, instance=cart)
            if cart_form.is_valid():
                cart_form.save()
                comment = cart_form.data['comment']
                cart.comment = comment
                cart.save()
                order_formation(request, cart)
            return redirect('orders')

    context = {
        'profile': profile,
        'cart': cart,
        'data': data,
        'comment': cart_form,
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


# Order
@profile_required
def order_view(request, order_id):
    profile = get_current_profile(request)
    children = Child.objects.filter(parent_id=profile)
    pupils = Pupil.objects.filter(id__in=children.values_list('pupil_id', flat=True))
    order = get_object_or_404(Order, pk=order_id)
    pupil = order.pupil_id

    if not (pupil in pupils):
        return redirect('orders')

    order_items = OrderItem.objects.filter(order_id=order)
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


# ----------------------------------------------------------------
#                   MODERATOR VIEWS
# ----------------------------------------------------------------


def make_sidebar(p: Profile) -> dict:
    menu_items = {}
    if p.role == 0 or p.role == 3:  # якщо звичайний користувач, або класний керівник - не завантажувати додаткові пункти меню
        return {}
    if p.role == 1 or p.role == 4:  # модератору та адміну більшість пунктів меню
        menu_items = {
            'list_meals': 'Прийоми їжі',
            'list_dishes': 'Страви',
            'list_menus': 'Меню',
            'list_products': 'Продукти',
            'list_schools': 'Школи',
        }
    if p.role == 2:  # керівнику школи додаємо їхню школу
        menu_items['view_school'] = get_object_or_404(
            School, pk=p.school_id.id)
    if p.role == 4:  # адміну пункт андміна
        menu_items['admin:index'] = 'Панель адміністратора'
        menu_items['table_orders'] = 'Замовлення'


    # menu_items = {
    #     'list_orders': 'Замовлення',
    #     'list_meals': 'Прийоми їжі',
    #     'list_dishes': 'Страви',
    #     'list_menus': 'Меню',
    #     'list_products': 'Продукти',
    #     'list_schools': 'Школи',
    #     'admin': 'Панель адміністратора'
    # }
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


@role_required(1, 4) # MB: dont need
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
    order_items = OrderItem.objects.filter(meal_id__in=meals)
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


# purchase - table
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
    
def table_by_order_items(order_items: OrderItem.objects.__class__):
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
    return t_dict

# cooking - table
def table_cooking_formation(data):
    date = data['date']
    school_id = data['school']
    class_id = data['class']
    status = 0

    def table_dict_by_(
            obj: School|Class|Pupil, 
            order_items: OrderItem.objects.__class__
        ):
        print(f"ARGS::{obj}, {list(order_items)}")

        if order_items.count() == 0:
            print(f"table_dict_by_:ERROR\n0 order items\n{order_items}")
            return {}

        table_dict = {
            obj.__class__._meta.verbose_name: [],
            'Прийом їжі': [],
            'Час': [],
            'Страва': [],
            'Порцій': [],
            'Вага порції': [],
        }
        menu_items_ids = order_items.values_list('menu_item_id', flat=True).distinct()

        for menu_item_id in menu_items_ids:
            order_items_by_menu_item = order_items.filter(menu_item_id=menu_item_id)
            order_item = order_items_by_menu_item.first()
            portions = sum(order_items_by_menu_item.aggregate(Sum("count_portion")).values())
            menu_item = order_item.menu_item_id
            meal = order_item.meal_id
            name = menu_item.dish_id.name
            
            table_dict[obj.__class__._meta.verbose_name].append(f"{obj.info()}")
            table_dict['Прийом їжі'].append(meal.name)
            table_dict['Час'].append(meal.time)
            table_dict['Страва'].append(name)
            table_dict['Порцій'].append(portions)
            table_dict['Вага порції'].append(menu_item.weight)
        print(f"TD::{table_dict}")
        return table_dict

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
        order_items = OrderItem.objects.filter(meal_id__in=meals, order_id__in=orders)
        return pandas.DataFrame(table_by_order_items(order_items))

    elif class_id == "all":
        classes = Class.objects.filter(school_id=school_id)
        pupils = Pupil.objects.filter(class_id__in=classes)
        meals = Meal.objects.filter(date=date, school_id=school_id)
        orders = Order.objects.filter(
            status=status, 
            datetime__lt=date,
            pupil_id__in=pupils
        )
        order_items = OrderItem.objects.filter(meal_id__in=meals, order_id__in=orders)
        return pandas.DataFrame(table_by_order_items(order_items))

    else:
        pupils = Pupil.objects.filter(class_id=class_id)
        meals = Meal.objects.filter(date=date, school_id=school_id)
        orders = Order.objects.filter(
            status=status, 
            datetime__lt=date,
            pupil_id__in=pupils
        )
        order_items = OrderItem.objects.filter(meal_id__in=meals, order_id__in=orders)
        return pandas.DataFrame(table_by_order_items(order_items))


# prepare
def table_prepare_formation(data):
    detail = data['detail']
    school = data['school']
    clss = data['class']


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
            table = table_prepare_formation(data)
        case _:
            print(f"\nError: non correct request template name {template_name}")
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
@role_required(4)
def retrieve_table(request):
    table = table_by_request(request.data)
    if request.data['need'] == "html":
        return table_to_html_responce(table)
    if request.data['need'] == "file":
        return table_to_csv_responce(table)
    

# ----------------------------------------------------------------
#           MOD VIEWS
# ----------------------------------------------------------------

# LISTS


@profile_required
def mod_index(request):
    return render(request, 'mod/base_mod.html', {'sb': make_sidebar(request.user.profile)})


@csrf_protect
@role_required(1, 4)
def mod_list_dishes(request):
    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        if dish_id and request.POST.get('action') == 'archive':
            dish = Dish.objects.get(id=dish_id)
            dish.archive()
        return redirect('list_dishes')
    dishes = Dish.objects.all()
    return render(request, 'mod/list_dishes.html', {'sb': make_sidebar(request.user.profile), 'dishes': dishes})


@profile_required
@role_required(4)
def mod_table_orders(request):
    profile = get_current_profile(request)
    context = {
        'profile': profile,
        'sb': make_sidebar(request.user.profile),
    }
    return render(request, 'mod/tables/table_orders.html', context)

@role_required(1, 4)
def mod_list_menus(request):
    menus = Menu.objects.all()
    return render(request, 'mod/list_menus.html', {'sb': make_sidebar(request.user.profile), 'menus': menus})


@role_required(1, 4)
def mod_list_products(request):
    products = Product.objects.all()
    return render(request, 'mod/list_products.html', {'sb': make_sidebar(request.user.profile), 'products': products})


# REGISTER CHILD REQUESTS
@api_view(['POST'])
@csrf_protect
@role_required(2, 3, 4)
def update_request(request, child_id, status):
    child = Child.objects.get(pk=child_id)

    if child.verified == 1 and Order.objects.filter(pupil_id=child.pupil_id, status=0).exists():
        # TODO: error "this child have some orders in waiting"
        return redirect('applications')
    
    child.verified = status
    child.save()
    if status == 1:
        Cart.objects.create(pupil_id=child.pupil_id).save()
        return redirect('applications')
    if status == 0 or status == 2:
        Cart.objects.filter(pupil_id=child.pupil_id).delete()
        return redirect('applications')
    # TODO: error "status not normal"
    return redirect('applications')
    


@csrf_protect
@role_required(1, 2, 3, 4)
def applications_page(request):
    profile = get_current_profile(request)
    if profile.role == 4 or profile.role == 1:  # mod or admin
        pending = children2dict(Child.objects.filter(verified=0))
        approved = children2dict(Child.objects.filter(verified=1))
        refused = children2dict(Child.objects.filter(verified=2))
    elif profile.role == 3:  # class mod
        pending = children2dict(Child.objects.filter(
            verified=0, pupil_id__class_id=profile.class_id))
        approved = children2dict(Child.objects.filter(
            verified=1, pupil_id__class_id=profile.class_id))
        refused = children2dict(Child.objects.filter(
            verified=2, pupil_id__class_id=profile.class_id))
    elif profile.role == 2:  # school mod
        pending = children2dict(Child.objects.filter(
            verified=0, pupil_id__class_id__school_id=profile.school_id))
        approved = children2dict(Child.objects.filter(
            verified=1, pupil_id__class_id__school_id=profile.school_id))
        refused = children2dict(Child.objects.filter(
            verified=2, pupil_id__class_id__school_id=profile.school_id))
    else:
        pending, approved, refused = [], [], []
    return render(request, 'mod/applications_page.html', {'pending': pending, 'approved': approved, 'refused': refused, 'sb': make_sidebar(request.user.profile)})


# DISH EDIT
@csrf_protect
@role_required(1, 4)
def edit_dish(request, dish_id: int):
    dish = get_object_or_404(Dish, pk=dish_id)
    ingredients = Ingredient.objects.filter(main_dish_id=dish_id)
    # страшно вирубай! ахах, в тебе також є пиздець нечитаємий.
    # Приємно думати що я не один рукопоп.
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
    return render(request, 'mod/edit_dish.html', {'dish_form': dish_form, 'dish': dish, 'ingredients': ingredients, 'products': products, 'dishes': dishes, 'sb': make_sidebar(request.user.profile)})


@role_required(1, 4)
def create_empty_dish(request):
    new_dish = Dish.objects.create(name='Нова Страва')
    return redirect('edit_dish', dish_id=new_dish.id)


@csrf_protect
@role_required(1, 4)
def delete_ingredient(request, pk, dish_id):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        ingredient.delete() # TODO: change this to .arhive()
        return redirect('edit_dish', dish_id=dish_id)


# MENU EDIT
@csrf_protect
@role_required(1, 4)
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
    return render(request, 'mod/edit_menu.html', {'menu_form': menu_form, 'menu': menu, 'menu_items': menu_items, 'dishes': dishes, 'sb': make_sidebar(request.user.profile)})


@role_required(1, 4)
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
@role_required(1, 4)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('list_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'mod/edit_product.html', {'form': form, 'sb': make_sidebar(request.user.profile)})


# MEALS EDIT
@csrf_protect
@role_required(1, 4)
def mod_list_meals(request, year: int = 0, month: int = 0, day: int = 0):
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
        return redirect('list_meals', year=year, month=month, day=day) if year and month and day else redirect('list_meals')
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
    return render(request, 'mod/list_meals.html', {'sb': make_sidebar(request.user.profile), 'meals': meals, 'menus': menus, 'dates': week, 'data': data})


# SCHOOLS EDIT
def gen_classes(school: School):
    class_objects = Class.objects.filter(school_id=school)
    classes = []
    for clss in class_objects:
        c = {}  # single class temp data
        c['class_id'] = clss
        c['operators'] = list(Profile.objects.filter(class_id=clss, role=3))
        c['pupils'] = {
            'approved': list(Pupil.objects.filter(class_id=clss, child__verified=1)),
            'pending': list(Pupil.objects.filter(class_id=clss, child__verified=0))
        }
        classes.append(c)
    return classes


@csrf_protect
@role_required(1, 4)
def mod_list_schools(request):  # TODO 
    # GENERATE DICT FOR SCHOOL: CLASSES AND OPERATORS
    school_objects = School.objects.all()
    schools = []
    for school in school_objects:
        s = {}  # single school temp data
        s['school_id'] = school
        s['operators'] = list(Profile.objects.filter(school_id=school, role=2))
        s['classes'] = list(Class.objects.filter(school_id=school))
        schools.append(s)
    #
    return render(request, 'mod/list_schools.html', {
        'sb': make_sidebar(request.user.profile),
        'schools': schools,
    })


@csrf_protect
@role_required(1, 2, 4)
def mod_view_school(request, school_id: int):
    try:
        school = School.objects.get(id=school_id)
    except School.DoesNotExist:
        return redirect('index')

    return render(request, 'mod/view_school.html', {
        'sb': make_sidebar(request.user.profile),
        'classes': gen_classes(school),
    })


@csrf_protect
@role_required(1, 2, 4)
def mod_add_operator(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)
            if not profile.role == 0:
                return redirect(request.META.get('HTTP_REFERER'))
            if 'class_id' in request.POST:  # change privileges for class operator
                class_id = request.POST.get('class_id')
                class_instance = get_object_or_404(Class, id=class_id)
                profile.role = 3
                profile.class_id = class_instance
            # change privileges for school operator
            elif 'school_id' in request.POST and not request.user.profile.role == 2:
                school_id = request.POST.get('school_id')
                school_instance = get_object_or_404(School, id=school_id)
                profile.role = 2
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
@role_required(1, 2, 4)
def mod_remove_privileges(request, profile_id: int):
    profile = get_object_or_404(Profile, id=profile_id)
    # Clear privileges
    profile.class_id = None
    profile.school_id = None
    profile.role = 0
    profile.save()
    return redirect(request.META.get('HTTP_REFERER'))


def mod_list_pupils(request):  # TODO mix with mod_request()
    pass
