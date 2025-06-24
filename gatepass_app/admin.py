# gatepass_app/admin.py
from django.contrib import admin
# UserAdmin and TextInput are no longer needed here as SecurityGuardAdmin is removed
# from django.contrib.auth.admin import UserAdmin
# from django.forms import TextInput

from .models import GatePass # Only GatePass is imported now

# The SecurityGuardAdmin registration is removed.


@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    """
    Admin interface for the GatePass model.
    This model is mapped to an Oracle view and is read-only in the admin,
    preventing additions, deletions, or direct changes.
    """
    # Columns displayed in the list view of GatePass entries
    list_display = (
        'GATEPASS_NO', 'NAME', 'DEPARTMENT', 'FINAL_STATUS', 'INOUT_STATUS',
        'OUT_TIME', 'OUT_BY', 'IN_TIME', 'IN_BY'
    )
    # Fields that can be searched
    search_fields = ('GATEPASS_NO', 'NAME', 'PAYCODE')
    # Fields that can be filtered
    list_filter = ('FINAL_STATUS', 'INOUT_STATUS', 'DEPARTMENT')

    # All fields are read-only since this model maps to a database view (managed=False).
    # This prevents accidental modifications through the Django admin.
    readonly_fields = [f.name for f in GatePass._meta.get_fields()]

    def has_add_permission(self, request):
        """Disables the 'Add' button for GatePass objects in the admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disables the 'Delete' button for GatePass objects in the admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disables the 'Change' button for GatePass objects in the admin."""
        return False
