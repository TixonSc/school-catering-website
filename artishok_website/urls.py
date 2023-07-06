from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/login/', views.login_view), # handle automatic django's login error redirect 


    #PROFILE`s pages
    path('profile/', views.profile_view, name='profile'),
    path('profile/create/', views.create_profile_view, name='create_profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),


    #CHILDREN`s pages
    path('get/schools_classes/', views.retrieve_schools_and_classes_json, name='get_schools_classes'),
    path('children/', views.children_view, name='children'),
    path('children/add/', views.add_child_view, name='add_child'),
    path('children/delete/<int:child_id>/', views.delete_child, name='delete_child'),
    

    path('menu/<int:cart_id>/', views.menu_days_view, name='menu_days'),
    path('menu/<int:cart_id>/day/<str:date>/', views.menu_day_view, name='menu_day'),
    path('count_portions/', views.count_portions, name='count_portions'),
    path('cart/<int:cart_id>/', views.cart_view, name='cart'), #корзина конкретної дитини    
    # path('cart/<int:cart_id>/confirm/', views.confirm_cart, name='confirm_cart'), #підтвердження замовлення кошика


    path('get/orders/', views.retrieve_orders_json, name='get_orders'),
    path('orders/', views.orders_view, name='orders'), #всі замовлення по всім дітям користувача які були
    path('orders/child/<int:pupil_id>/', views.orders_view, name='orders'), #всі замовлення на конкретну дитину
    path('order/<int:order_id>/', views.order_view, name='order'), #конкретне замовлення на конкретну дитину
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'), #конкретне замовлення на конкретну дитину
    

    ### MOD URLS
    path('mod/', views.mod_index, name='mod_index'), 
    path('mod/update_request/<int:child_id>/<int:status>/', views.update_request, name='update_request'),
    path('mod/requests/', views.applications_page, name='applications'),
    path('mod/meals/', views.mod_list_meals, name='list_meals'),
    path('mod/meals/<int:year>-<int:month>-<int:day>/', views.mod_list_meals, name='list_meals'),
    path('mod/dishes/', views.mod_list_dishes, name='list_dishes'),
    path('mod/orders/', views.mod_list_orders, name='list_orders'),
    path('mod/menus/', views.mod_list_menus, name='list_menus'),
    path('mod/products/', views.mod_list_products, name='list_products'),
    path('mod/schools/', views.mod_list_schools, name='list_schools'),
    path('mod/schools/<int:school_id>/', views.mod_view_school, name='view_school'),
    # path('mod/schools/<int:school_id>/classes/', views.mod_list_classes, name='list_classes'),
    # path('mod/schools/<int:school_id>/classes/<int:class_id>', views.mod_list_pupils, name='list_pupils'),
    path('mod/add_op/', views.mod_add_operator, name='add_operator'),
    path('mod/rm_priv/<int:profile_id>', views.mod_remove_privileges, name='remove_privileges'),

    path('mod/dish/<int:dish_id>/change/', views.edit_dish, name='edit_dish'),
    path('mod/dish/<int:dish_id>/ingredient/<int:pk>/delete/', views.delete_ingredient, name='delete_ingredient'),
    path('mod/dish/create/', views.create_empty_dish, name='create_empty_dish'),

    path('mod/menu/<int:menu_id>/change/', views.edit_menu, name='edit_menu'),
    path('mod/menu/<int:menu_id>/menu_item/<int:pk>/delete/', views.delete_menu_item, name='delete_menu_item'),
    path('mod/menu/create/', views.create_empty_menu, name='create_empty_menu'),

    path('mod/product/<int:product_id>/change/', views.edit_product, name='edit_product'),
    path('mod/product/create/', views.create_empty_product, name='create_empty_product'),
    
    # txn code
    path('table/', views.table_view, name='table'),
    path('get/table/', views.retrieve_table, name='get_table'),
    path('mod/tables/create/', views.mod_creating_table, name='create_table'),


    path('admin/', admin.site.urls, name='admin'),
]
