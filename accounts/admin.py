# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import User , Profile , Plan

# admin.site.register(Profile)
# admin.site.register(Plan)


# @admin.register(User)
# class UserAdmin(BaseUserAdmin):


#     list_display = ('email', 'role', 'is_active', 'is_staff','plan', 'is_superuser')


#     list_filter = ('is_active', 'is_staff', 'is_superuser', 'role', 'plan', 'groups' )


#     search_fields = ('email', 'role')


#     ordering = ('email',)



#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal info', {'fields': ('role', 'plan')}),
#         # The 'Permissions' section is crucial for controlling user access.
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login',)}),
#     )

#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'password', 'password2'), # password2 is for confirmation
#         }),
#     )

#     REQUIRED_FIELDS = []




from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, Plan

class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "role",
        "plan",
        "plan_start_date",
        "plan_end_date",
        "is_active",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Plan Info", {"fields": ("plan", "plan_start_date", "plan_end_date")}),
        ("Prompt Info", {"fields": ("monthly_prompt_count", "extra_prompts")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("OTP Info", {"fields": ("otp", "otp_created_at")}),
    )

    search_fields = ("email",)
    ordering = ("email",)

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Plan)
