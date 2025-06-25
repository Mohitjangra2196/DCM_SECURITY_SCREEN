from rest_framework import serializers
from .models import GatePass 


class GatePassSerializer(serializers.ModelSerializer):

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

        read_only_fields = [
            'GATEPASS_NO', 'GATEPASS_DATE', 'PAYCODE', 'NAME', 'DEPARTMENT',
            'GATEPASS_TYPE', 'REMARKS', 'REQUEST_TIME', 'AUTH', 'AUTH1_BY',
            'AUTH1_STATUS', 'AUTH1_DATE', 'AUTH1_REMARKS', 'FINAL_STATUS'
        ]
