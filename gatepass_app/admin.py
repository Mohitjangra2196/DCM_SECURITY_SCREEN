# gatepass_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import TextInput, DateInput
from .models import SecurityGuard, GatePass # Import your new fields



@admin.register(SecurityGuard)
class SecurityGuardAdmin(UserAdmin):
    list_display = ('username', 'unique_code', 'first_name', 'last_name', 'desig', 'is_staff', 'is_active')
    search_fields = ('username', 'unique_code', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Security Guard Info'), {'fields': ('unique_code', 'first_name', 'last_name', 'grade', 'desig')}), # Adjusted fields
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password', 'password2'),
        }),
        (('Security Guard Info'), {'fields': ('unique_code', 'first_name', 'last_name', 'grade', 'desig')}), # Adjusted fields
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    formfield_overrides = {
        SecurityGuard.unique_code: {
            'widget': TextInput(attrs={'autocomplete': 'employee-id', 'class': 'vTextField'}) # Add vTextField class for styling
        },
        SecurityGuard.grade: {
            'widget': TextInput(attrs={'autocomplete': 'off'})
        },
        SecurityGuard.desig: {
            'widget': TextInput(attrs={'autocomplete': 'organization-title'})
        },
        # first_name and last_name are already handled by UserAdmin's default widgets,
        # but you can override them if you want specific autocomplete attributes.
        # e.g., SecurityGuard.first_name: {'widget': TextInput(attrs={'autocomplete': 'given-name'})},
        # e.g., SecurityGuard.last_name: {'widget': TextInput(attrs={'autocomplete': 'family-name'})},
    }

    class Media:
        js = (
            'gatepass_app/js/admin_auto_fill.js',
        )
        
@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = (
        'GATEPASS_NO', 'NAME', 'DEPARTMENT', 'FINAL_STATUS', 'INOUT_STATUS',
        'OUT_TIME', 'OUT_BY', 'IN_TIME', 'IN_BY'
    )
    search_fields = ('GATEPASS_NO', 'NAME', 'PAYCODE')
    list_filter = ('FINAL_STATUS', 'INOUT_STATUS', 'DEPARTMENT')
    # Make it read-only in admin as it's a view
    readonly_fields = [f.name for f in GatePass._meta.get_fields()]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False