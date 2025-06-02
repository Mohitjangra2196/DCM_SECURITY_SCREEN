# gatepass_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

# gatepass_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class SecurityGuard(AbstractUser):
    unique_code = models.CharField(max_length=60, unique=True, verbose_name="Unique Code (Employee Code)")
    grade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Grade")
    desig = models.CharField(max_length=200, blank=True, null=True, verbose_name="Designation")
    
    def __str__(self):
        return self.username


class GatePass(models.Model):
    GATEPASS_NO = models.CharField(max_length=60, primary_key=True) # Assuming GATEPASS_NO is unique
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
    OUT_BY = models.CharField(max_length=60, null=True, blank=True)
    IN_TIME = models.DateTimeField(null=True, blank=True)
    IN_BY = models.CharField(max_length=60, null=True, blank=True)
    INOUT_STATUS = models.CharField(max_length=3, null=True, blank=True) # O = Out, I = In

    class Meta:
        managed = False  # Django will not manage this table/view's schema
        db_table = 'GATEPASS' # The actual view name in Oracle
        # You might need to specify the app_label if you have multiple apps
        # app_label = 'gatepass_app'


# Consider a separate model for actual gatepass movements if the view is not directly updatable for IN/OUT statuses
# class GatePassMovement(models.Model):
#     gatepass_no = models.ForeignKey(GatePass, on_delete=models.CASCADE, to_field='GATEPASS_NO')
#     out_time = models.DateTimeField(null=True, blank=True)
#     out_by = models.ForeignKey(SecurityGuard, on_delete=models.SET_NULL, null=True, related_name='marked_out')
#     in_time = models.DateTimeField(null=True, blank=True)
#     in_by = models.ForeignKey(SecurityGuard, on_delete=models.SET_NULL, null=True, related_name='marked_in')
#     status = models.CharField(max_length=3, default='O') # 'O' for Out, 'I' for In
#     # Add any other fields if needed for auditing the movements    