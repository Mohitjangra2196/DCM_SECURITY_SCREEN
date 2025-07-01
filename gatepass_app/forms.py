# gatepass_app/forms.py
from django import forms
from django.utils import timezone
import pytz
from datetime import timedelta, datetime

class ManualGatePassForm(forms.Form):
    PAYCODE = forms.CharField(
        max_length=60,
        label="Pay Code",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    EMPLOYEE_NAME = forms.CharField(
        max_length=100,
        label="Employee Name",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    DEPARTMENT_NAME = forms.CharField(
        max_length=100,
        label="Department",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    GATEPASS_TYPE_CHOICES = [
        ('Official', 'Official'),
        ('Personal', 'Personal'),
    ]
    GATEPASS_TYPE = forms.ChoiceField(
        choices=GATEPASS_TYPE_CHOICES,
        label="Gatepass Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    mark_out_duration = forms.ChoiceField(
        label="Short leave Time",
        choices=[
            ('30', '30 min'),
            ('60', '1 hr'),
            ('90', '1 hr 30 min'),
            ('120', '2 hr'),
            ('150', '2 hr 30 min'),
            ('180', '3 hr'),
            ('210', '3 hr 30 min'),
            ('240', '4 hr'),
            ('270', '4 hr 30 min'),
            ('300', '5 hr'),
            ('330', '5 hr 30 min'),
            ('360', '6 hr'),
            ('390', '6 hr 30 min'),
            ('420', '7 hr'),
            ('450', '7 hr 30 min'),
            ('480', '8 hr'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='30' # Default to 30 min
    )

    MARK_IN_TIME = forms.CharField(
        label="Mark In Time",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    MARK_OUT_TIME_DISPLAY = forms.CharField(
        label="Mark Out Time",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use a consistent timezone for all time operations
        ist_timezone = pytz.timezone('Asia/Kolkata')
        current_time_aware_ist = timezone.now().astimezone(ist_timezone)

        # Format MARK_IN_TIME for display (M/D/YYYY H:MM:SS AM/PM)
        self.fields['MARK_IN_TIME'].initial = current_time_aware_ist.strftime('%#m/%#d/%Y %#I:%M:%S %p')

        # Calculate and format initial MARK_OUT_TIME_DISPLAY
        try:
            initial_duration_minutes = int(self.fields['mark_out_duration'].initial)
            # Mark Out Time = Mark In Time - Duration (Reversed Logic)
            initial_mark_out_time = current_time_aware_ist - timedelta(minutes=initial_duration_minutes)
            
            # Format MARK_OUT_TIME_DISPLAY for display
            self.fields['MARK_OUT_TIME_DISPLAY'].initial = initial_mark_out_time.strftime('%#m/%#d/%Y %#I:%M:%S %p')

        except (ValueError, TypeError):
            self.fields['MARK_OUT_TIME_DISPLAY'].initial = ''

        for name, field in self.fields.items():
            if name not in ['GATEPASS_TYPE', 'mark_out_duration']:
                field.widget.attrs.update({'class': 'form-control'})


class ManualMarkOutForm(forms.Form):
    PAYCODE = forms.CharField(
        max_length=60,
        label="Pay Code",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    EMPLOYEE_NAME = forms.CharField(
        max_length=100,
        label="Employee Name",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    DEPARTMENT_NAME = forms.CharField(
        max_length=100,
        label="Department",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    GATEPASS_TYPE_CHOICES = [
        ('Official', 'Official'),
        ('Personal', 'Personal'),
    ]
    GATEPASS_TYPE = forms.ChoiceField(
        choices=GATEPASS_TYPE_CHOICES,
        label="Gatepass Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    MARK_OUT_TIME_DISPLAY = forms.CharField(
        label="Mark Out Time",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use a consistent timezone for all time operations
        ist_timezone = pytz.timezone('Asia/Kolkata')
        current_time_aware_ist = timezone.now().astimezone(ist_timezone)

        # Mark Out Time is simply the current time
        self.fields['MARK_OUT_TIME_DISPLAY'].initial = current_time_aware_ist.strftime('%#m/%#d/%Y %#I:%M:%S %p')

        for name, field in self.fields.items():
            if name not in ['GATEPASS_TYPE']:
                field.widget.attrs.update({'class': 'form-control'})