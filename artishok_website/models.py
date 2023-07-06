from django.db import models
from django.contrib.auth.models import User
from django.db.models.query import QuerySet


class MyModelManager(models.Manager):
    # handle archived models when _model_.objects.all()
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().exclude(archived=True)


class ArchivedModel(models.Model):
    # model that supports archivation
    archived = models.BooleanField(
        default=False, verbose_name="Видалено (в архіві)")

    objects = MyModelManager()  # custom manager
    all_objects = models.Manager()  # default manager

    def archive(self):
        self.archived = True
        self.save()

    class Meta:
        abstract = True

# Models with no ForeignKeys. Independent models


class Dish(ArchivedModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="Назва")
    description = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Опис")
    img_link = models.URLField(
        blank=True, null=True, verbose_name="Посилання на зображення")

    def __str__(self):
        return (f"ID:{self.id}:{self.name}")

    class Meta:
        verbose_name = "Страва"
        verbose_name_plural = "Страви"


class School(ArchivedModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Назва")

    def info(self):
        return (f"{self.name}")
    
    def __str__(self):
        return (f"ID:{self.id}:{self.name}")

    class Meta:
        verbose_name = "Школа"
        verbose_name_plural = "Школи"


class Menu(ArchivedModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Назва")

    def __str__(self):
        return (f"ID:{self.id}:{self.name}")

    class Meta:
        verbose_name = "Меню"
        verbose_name_plural = "Меню"


class Unit(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="Назва")

    def __str__(self):
        return (f"ID:{self.id}:{self.name}")

    class Meta:
        verbose_name = "Одиниця виміру"
        verbose_name_plural = "Одиниці виміру"


# Dependent models

class MenuItem(models.Model):
    id = models.AutoField(primary_key=True)
    menu_id = models.ForeignKey(
        Menu, on_delete=models.SET_NULL, null=True, verbose_name="Меню")
    dish_id = models.ForeignKey(
        Dish, on_delete=models.SET_NULL, null=True, verbose_name="Страва")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Ціна")
    weight = models.IntegerField(blank=True, null=True, verbose_name="Вага")

    def __str__(self):
        return (f"{self.dish_id}:{self.dish_id.name} в {self.menu_id.name} ")

    class Meta:
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункти меню"


class Meal(models.Model):
    id = models.AutoField(primary_key=True)
    school_id = models.ForeignKey(
        School, on_delete=models.CASCADE, verbose_name="Школа")
    menu_id = models.ForeignKey(
        Menu, on_delete=models.CASCADE, verbose_name="Меню")
    name = models.CharField(max_length=100, verbose_name="Назва")
    date = models.DateField(verbose_name="Дата")
    time = models.TimeField(blank=True, null=True, verbose_name="Час")

    def info(self) -> str:
        return (f"{self.name} {self.date} {self.time}")

    def __str__(self):
        return (f"ID:{self.id}:{self.name}:{self.date}:{self.time} з {self.menu_id.name} до {self.school_id.name}")

    class Meta:
        verbose_name = "Прийом їжі"
        verbose_name_plural = "Прийоми їжі"

# generate a dict meal_forms: with
# {school_name:"name",
#      dates: {mon:"09.06.2000",
#             tue:"10.06.2000",
#             . . .}
# }
#


class Class(ArchivedModel):
    id = models.AutoField(primary_key=True)
    school_id = models.ForeignKey(
        School, on_delete=models.CASCADE, verbose_name="Школа")
    name = models.CharField(max_length=64, verbose_name="Назва")

    def info(self):
        return (f"{self.name}")

    def __str__(self):
        return (f"ID:{self.id}:{self.name} в {self.school_id.name}")

    class Meta:
        verbose_name = "Клас"
        verbose_name_plural = "Класи"


class Pupil(models.Model):
    id = models.AutoField(primary_key=True)
    class_id = models.ForeignKey(
        Class, on_delete=models.CASCADE, verbose_name="Клас")
    first_name = models.CharField(max_length=64, verbose_name="Ім'я")
    last_name = models.CharField(max_length=64, verbose_name="Прізвище")
    birth_date = models.DateField(
        blank=True, null=True, verbose_name="Дата народження")

    def info(self):
        return (f"{self.first_name} {self.last_name}")

    def __str__(self):
        return (f"ID:{self.id}:{self.first_name} {self.last_name}")

    class Meta:
        verbose_name = "Учень"
        verbose_name_plural = "Учні"


class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    pupil_id = models.ForeignKey(
        Pupil, on_delete=models.CASCADE, verbose_name="Учень")
    comment = models.CharField(
        null=True, max_length=512, verbose_name="Коментар")

    def __str__(self):
        return (f"ID:{self.id}:{self.pupil_id.first_name}")
 
    class Meta:
        verbose_name = "Кошик"
        verbose_name_plural = "Кошики"


class CartItem(models.Model):
    id = models.AutoField(primary_key=True)
    menu_item_id = models.ForeignKey(
        MenuItem, on_delete=models.CASCADE, verbose_name="Пункт меню")
    cart_id = models.ForeignKey(
        Cart, on_delete=models.CASCADE, verbose_name="Кошик")
    meal_id = models.ForeignKey(
        Meal, on_delete=models.CASCADE, verbose_name="Прийом їжі")  # Шо за бланк
    count_portion = models.IntegerField(default=0, verbose_name="Порції")

    def __str__(self):
        return (f"ID:{self.id}:{self.menu_item_id.dish_id.name} {self.count_portion} до {self.meal_id.name}")

    class Meta:
        verbose_name = "Пункт кошика"
        verbose_name_plural = "Пункти кошика"


class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    role = models.IntegerField(choices=(
        (0, 'Користувач'),
        (1, 'Модератор'),
        (2, 'Керівник школи'),
        (3, 'Керівник класу'),
        (4, 'Адмін'),
    ),
        default=0
    )
    first_name = models.CharField(max_length=64, verbose_name="Ім'я")
    last_name = models.CharField(max_length=64, verbose_name="Прізвище")
    phone_number = models.CharField(
        max_length=28, verbose_name="Номер телефону")
    school_id = models.ForeignKey(School, on_delete=models.SET_NULL,
                                  blank=True, null=True, verbose_name="Повний доступ до школи")
    class_id = models.ForeignKey(Class, on_delete=models.SET_NULL,
                                 blank=True, null=True, verbose_name="Повний доступ до класу")

    def __str__(self):
        return (f"ID:{self.id}:{self.first_name} {self.last_name} ({self.user.email})")

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"


class Child(ArchivedModel):
    id = models.AutoField(primary_key=True)
    parent_id = models.ForeignKey(
        Profile, on_delete=models.CASCADE, verbose_name="Батько")
    pupil_id = models.ForeignKey(
        Pupil, on_delete=models.CASCADE, verbose_name="Учень")
    verified = models.IntegerField(verbose_name='Підтверджено', choices=(
        (0, 'Очікує'),
        (1, 'Підтверджено'),
        (2, 'Відхилено')
    ),
        default=0
    )

    def __str__(self):
        return (f"id({self.id}):{self.pupil_id.first_name} - {self.parent_id.user.email}")

    class Meta:
        verbose_name = "Дитина"
        verbose_name_plural = "Діти"


class Product(ArchivedModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, verbose_name="Назва продукту")
    unit_id = models.ForeignKey(
        Unit, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Одиниця виміру")

    is_meat = models.BooleanField(verbose_name="М'ясо")
    is_fish = models.BooleanField(verbose_name="Риба")
    is_gluten = models.BooleanField(verbose_name="Глютен")
    is_lactose = models.BooleanField(verbose_name="Лактоза")
    is_bob = models.BooleanField(verbose_name="Бобові")
    is_glucose = models.BooleanField(verbose_name="Глюкоза")

    def __str__(self):
        return (f"ID:{self.id}:{self.name}")

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукти"


class Ingredient(models.Model): # TODO: Count of Product
    id = models.AutoField(primary_key=True)
    main_dish_id = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name="dish", verbose_name="Основна страва")
    product_dish_id = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name="product", blank=True,
        null=True, verbose_name="Страва як інгредієнт основної")
    product_id = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=True,
        null=True, verbose_name="Продукт як інгредієнт")

    def __str__(self):
        return (f"ID:{self.id}:{self.product_dish_id.name if self.product_dish_id else self.product_id.name}")

    class Meta:
        verbose_name = "Інгредієнт"
        verbose_name_plural = "Інгредієнти"


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    pupil_id = models.ForeignKey(
        Pupil, on_delete=models.PROTECT, verbose_name="Учень")
    profile_id = models.ForeignKey(
        Profile, on_delete=models.PROTECT, verbose_name="Профіль")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Ціна")
    datetime = models.DateTimeField(verbose_name="Дата та час")
    status = models.IntegerField(
        verbose_name="Статус",
        choices=(
            (0, 'Очікує'),
            (1, 'Готується'),
            (2, 'Виконано'),
            (3, 'Відхилено'),
        ),
        default=0
    )
    comment = models.CharField(
        null=True, max_length=512, verbose_name="Коментар")

    def __str__(self):
        return (f"ID:{self.id} від {self.profile_id.first_name} на {self.pupil_id.first_name} СТАТУС:{self.status}")

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(
        Order, on_delete=models.PROTECT, verbose_name="Замовлення")
    menu_item_id = models.ForeignKey(
        MenuItem, on_delete=models.PROTECT, verbose_name="Пункт меню")
    meal_id = models.ForeignKey(
        Meal, on_delete=models.SET_NULL, null=True, verbose_name="Прийом їжі")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Ціна")
    count_portion = models.IntegerField(default=0, verbose_name="Порції")
    status = models.IntegerField(
        verbose_name="Статус",
        choices=(
            (0, 'Очікує'),
            (1, 'Готується'),
            (2, 'Виконано'),
            (3, 'Відхилено'),
        ),
        default=0
    )

    def __str__(self):
        return (f"ID:{self.id}:{self.menu_item_id.dish_id.name} для {self.order_id.pupil_id.id}")

    class Meta:
        verbose_name = "Пункт замовлення"
        verbose_name_plural = "Пункти замовлення"
