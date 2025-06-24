# gatepass_app/serializers.py
from rest_framework import serializers
from .models import GatePass # Only GatePass is imported now


# SecurityGuardSerializer is removed.

class GatePassSerializer(serializers.ModelSerializer):
    """
    Serializer for the GatePass model.
    Lists all fields from the model, as it's typically used for read-only operations
    given that the model's managed=False and maps to a view.
    Most fields are set as read-only to prevent updates via the API, aligning with its view-like nature.
    """
    class Meta:
        model = GatePass
        # Explicitly list all fields from the GatePass model.
        # 'id' is excluded because GATEPASS_NO is the primary key.
        fields = [
            'GATEPASS_NO', 'GATEPASS_DATE', 'PAYCODE', 'NAME', 'DEPARTMENT',
            'GATEPASS_TYPE', 'REMARKS', 'REQUEST_TIME', 'AUTH', 'AUTH1_BY',
            'AUTH1_STATUS', 'AUTH1_DATE', 'AUTH1_REMARKS', 'FINAL_STATUS',
            'OUT_TIME', 'OUT_BY', 'IN_TIME', 'IN_BY', 'INOUT_STATUS'
        ]
        # Define fields that should not be modifiable via API.
        # This aligns with the GatePass model being a view (managed=False).
        read_only_fields = [
            'GATEPASS_NO', 'GATEPASS_DATE', 'PAYCODE', 'NAME', 'DEPARTMENT',
            'GATEPASS_TYPE', 'REMARKS', 'REQUEST_TIME', 'AUTH', 'AUTH1_BY',
            'AUTH1_STATUS', 'AUTH1_DATE', 'AUTH1_REMARKS', 'FINAL_STATUS'
        ]

    # Note: If you need to update OUT_TIME, OUT_BY, IN_TIME, IN_BY via API,
    # you might need to implement a custom update method in your ViewSet
    # or override the serializer's update method if your database allows direct writes
    # to the underlying table for these specific columns.


class EmployeeDetailsSerializer(serializers.Serializer):
    """
    Serializer for employee details fetched from an external source (e.g., 'emp_mst@dl10gto12c').
    This is not tied to a Django model.
    """
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    grade = serializers.CharField(max_length=255)
    desig = serializers.CharField(max_length=255)
