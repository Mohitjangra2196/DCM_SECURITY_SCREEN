# gatepass_app/models.py
from django.db import models

class GatePass(models.Model):
    """
    Model representing a GatePass, mapped to an existing Oracle view/table 'GATEPASS'.
    It is set to managed = False as Django will not manage its schema.
    """
    GATEPASS_NO = models.CharField(max_length=60, primary_key=True) # Assuming GATEPASS_NO is unique and primary key
    GATEPASS_DATE = models.DateField()
    PAYCODE = models.CharField(max_length=60)
    NAME = models.CharField(max_length=300, null=True, blank=True)
    DEPARTMENT = models.CharField(max_length=300, null=True, blank=True)
    GATEPASS_TYPE = models.CharField(max_length=150, null=True, blank=True)
    REMARKS = models.CharField(max_length=765, null=True, blank=True)
    REQUEST_TIME = models.CharField(max_length=60, null=True, blank=True)
    AUTH = models.CharField(max_length=1, null=True, blank=True) # Updated max_length to 1
    AUTH1_BY = models.CharField(max_length=24, null=True, blank=True)
    AUTH1_STATUS = models.CharField(max_length=1, null=True, blank=True) # Updated max_length to 1
    AUTH1_DATE = models.DateField(null=True, blank=True)
    AUTH1_REMARKS = models.CharField(max_length=150, null=True, blank=True)
    FINAL_STATUS = models.CharField(max_length=1, null=True, blank=True) # Updated max_length to 1 (A = Approved)
    OUT_TIME = models.DateTimeField(null=True, blank=True) # Reverted to DateTimeField based on sample data
    OUT_BY = models.CharField(max_length=60, null=True, blank=True) # Represents who marked out
    IN_TIME = models.DateTimeField(null=True, blank=True) # Reverted to DateTimeField based on sample data
    IN_BY = models.CharField(max_length=60, null=True, blank=True) # Represents who marked in
    INOUT_STATUS = models.CharField(max_length=1, null=True, blank=True) # Updated max_length to 1 (O = Out, I = In)
    EARLY_LATE = models.CharField(max_length=1, null=True, blank=True)

    # New columns added and type adjusted based on Oracle schema and sample data
    IN_OUT_TIME = models.CharField(max_length=30, null=True, blank=True)
    BYPASS_REASON = models.CharField(max_length=1500, null=True, blank=True)
    EMP_TYPE = models.CharField(max_length=1, null=True, blank=True)
    USER_ID = models.CharField(max_length=60, null=True, blank=True)
    LUNCH = models.CharField(max_length=1, null=True, blank=True)
    UNIT_NAME = models.CharField(max_length=8, null=True, blank=True)
    EL_MIN = models.IntegerField(null=True, blank=True) # NUMBER in Oracle typically maps to IntegerField in Django
    SYS_DATE = models.DateTimeField(null=True, blank=True) # Changed to DateTimeField based on sample data

    class Meta:
        managed = False  # Django will not manage this table/view's schema
        db_table = 'GATEPASS' # The actual view name in Oracle
        # If you have multiple apps and this model might conflict,
        # you might need to specify app_label, e.g., app_label = 'gatepass_app'