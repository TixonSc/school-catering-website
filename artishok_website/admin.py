from django.contrib import admin
from .models import *


class ArchivedObjectAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return self.model.all_objects.all()


admin.site.register([MenuItem, Meal, Pupil, Cart,
                    CartItem, Profile, Unit, Ingredient, Order, OrderItem])

admin.site.register(Dish, ArchivedObjectAdmin)
admin.site.register(School, ArchivedObjectAdmin)
admin.site.register(Menu, ArchivedObjectAdmin)
admin.site.register(Class, ArchivedObjectAdmin)
admin.site.register(Child, ArchivedObjectAdmin)
admin.site.register(Product, ArchivedObjectAdmin)
