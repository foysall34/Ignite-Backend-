from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User, Profile

class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "role",
        "plan_type",
        "is_plan_paid",
        "plan_start_date",
        "plan_end_date",
        "is_active",
    )

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Plan Info', {
            'fields': (
                'plan_type',
                'is_plan_paid',
                'plan_start_date',
                'plan_end_date',
            )
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )

    readonly_fields = ('plan_start_date', 'plan_end_date')

    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
