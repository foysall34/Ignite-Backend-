from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):


    list_display = ('email', 'role', 'is_active', 'is_staff', 'is_superuser')


    list_filter = ('is_active', 'is_staff', 'is_superuser', 'role', 'groups')


    search_fields = ('email', 'role')


    ordering = ('email',)



    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('role',)}),
        # The 'Permissions' section is crucial for controlling user access.
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'), # password2 is for confirmation
        }),
    )

    REQUIRED_FIELDS = []