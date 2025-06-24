# gatepass_app/models.py
from django.db import models
# from django.contrib.auth.models import AbstractUser # AbstractUser is no longer needed

# The SecurityGuard model definition is removed.
# If you need to store unique_code, grade, desig for other purposes,
# consider creating a separate 'Profile' model linked to Django's default User.


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
    AUTH = models.CharField(max_length=3, null=True, blank=True)
    AUTH1_BY = models.CharField(max_length=24, null=True, blank=True)
    AUTH1_STATUS = models.CharField(max_length=3, null=True, blank=True)
    AUTH1_DATE = models.DateField(null=True, blank=True)
    AUTH1_REMARKS = models.CharField(max_length=150, null=True, blank=True)
    FINAL_STATUS = models.CharField(max_length=3, null=True, blank=True) # A = Approved
    OUT_TIME = models.DateTimeField(null=True, blank=True)
    OUT_BY = models.CharField(max_length=60, null=True, blank=True) # Represents who marked out
    IN_TIME = models.DateTimeField(null=True, blank=True)
    IN_BY = models.CharField(max_length=60, null=True, blank=True) # Represents who marked in
    INOUT_STATUS = models.CharField(max_length=3, null=True, blank=True) # O = Out, I = In

    class Meta:
        managed = False  # Django will not manage this table/view's schema
        db_table = 'GATEPASS' # The actual view name in Oracle
        # If you have multiple apps and this model might conflict,
        # you might need to specify app_label, e.g., app_label = 'gatepass_app'
