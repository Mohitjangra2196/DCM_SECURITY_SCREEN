# gatepass_app/serializers.py
from rest_framework import serializers
from .models import SecurityGuard, GatePass

class SecurityGuardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityGuard
        fields = ['id', 'username', 'unique_code', 'grade', 'desig']
        # You might want to make unique_code read_only for API, depending on your use case
        read_only_fields = ['unique_code']

class GatePassSerializer(serializers.ModelSerializer):
    # If you want to include the full SecurityGuard object for OUT_BY/IN_BY,
    # you'd need a different approach (e.g., SerializerMethodField or Nested Serializer)
    # For now, let's just expose the unique_code as in your model.

    class Meta:
        model = GatePass
        # Exclude 'id' since GATEPASS_NO is your primary key
        # We need to explicitly list fields because of the 'managed = False'
        fields = [
            'GATEPASS_NO', 'GATEPASS_DATE', 'PAYCODE', 'NAME', 'DEPARTMENT',
            'GATEPASS_TYPE', 'REMARKS', 'REQUEST_TIME', 'AUTH', 'AUTH1_BY',
            'AUTH1_STATUS', 'AUTH1_DATE', 'AUTH1_REMARKS', 'FINAL_STATUS',
            'OUT_TIME', 'OUT_BY', 'IN_TIME', 'IN_BY', 'INOUT_STATUS'
        ]
        # Make most fields read-only, except for the ones you want to update via API
        read_only_fields = [
            'GATEPASS_NO', 'GATEPASS_DATE', 'PAYCODE', 'NAME', 'DEPARTMENT',
            'GATEPASS_TYPE', 'REMARKS', 'REQUEST_TIME', 'AUTH', 'AUTH1_BY',
            'AUTH1_STATUS', 'AUTH1_DATE', 'AUTH1_REMARKS', 'FINAL_STATUS'
        ]

    # Custom update method because your GatePass model is 'managed = False'
    # and updates rely on raw SQL in your views. DRF's default update might not work directly.
    # We will override the update method in the ViewSet if needed for partial updates.


class EmployeeDetailsSerializer(serializers.Serializer):
    # This serializer is for your custom get_employee_details API,
    # which fetches data from 'emp_mst@dl10gto12c' not a Django model.
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    grade = serializers.CharField(max_length=255)
    desig = serializers.CharField(max_length=255)