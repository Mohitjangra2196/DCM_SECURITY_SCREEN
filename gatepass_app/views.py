# gatepass_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection # For raw SQL queries
from django.utils import timezone
from .models import GatePass
from django.http import JsonResponse # Added this import
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta # Added datetime and timedelta import here

# Import the new form
from .forms import ManualGatePassForm

# DRF Imports
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import GatePassSerializer

# Import for timezone handling
from pytz import timezone as pytz_timezone

# Define the Oracle server's actual timezone (IST)
ORACLE_SERVER_TIMEZONE = pytz_timezone('Asia/Kolkata')

User = get_user_model() # Get the currently active user model (which is now Django's default User)

@login_required
def home_screen(request):
    # Filter out superusers from the list of security guards
    # is_superuser=False will exclude any user marked as a superuser.
    security_guards = User.objects.filter(is_superuser=False).order_by('username') # Corrected order_ok_by to order_by
    return render(request, 'gatepass_app/home_screen.html', {'security_guards': security_guards})



@login_required
def mark_out_screen(request):
    employees_to_mark_out = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT GATEPASS_NO, (NAME||' ('||PAYCODE||')') NAME, DEPARTMENT, REMARKS, AUTH1_BY, AUTH1_DATE, REQUEST_TIME, GATEPASS_TYPE FROM GATEPASS WHERE FINAL_STATUS = 'A' AND OUT_TIME IS NULL AND EARLY_LATE <> 'L'")
        columns = [col[0] for col in cursor.description]
        raw_employees = cursor.fetchall()

    for row in raw_employees:
        employee_dict = dict(zip(columns, row))
        auth1_by_code_raw = employee_dict.get('AUTH1_BY')
        GatePass_type_code_raw = employee_dict.get('GATEPASS_TYPE')

        if auth1_by_code_raw is None :
            if GatePass_type_code_raw == 'Official' :
                employee_dict['AUTH1_BY_DISPLAY'] = "ByPass - Official"
            elif GatePass_type_code_raw == 'Personal' :
                employee_dict['AUTH1_BY_DISPLAY'] = "ByPass - Personal"
        else :
            if GatePass_type_code_raw == 'Official':
                employee_dict['AUTH1_BY_DISPLAY'] = "Approved - Official"
            elif GatePass_type_code_raw == 'Personal':
                employee_dict['AUTH1_BY_DISPLAY'] = "Approved - Personal"
        employees_to_mark_out.append(employee_dict)

    return render(request, 'gatepass_app/mark_out_screen.html', {'employees': employees_to_mark_out})



@login_required
def process_mark_out(request, gatepass_no):
    if request.method == 'POST':
        current_time_aware_ist = timezone.now().astimezone(ORACLE_SERVER_TIMEZONE)
        naive_time_for_oracle = current_time_aware_ist.replace(tzinfo=None)

        security_guard_identifier = request.user.username

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE GATEPASS
                    SET OUT_TIME = :out_time, OUT_BY = :out_by, INOUT_STATUS = 'O'
                    WHERE GATEPASS_NO = :gatepass_no
                    """,
                    {'out_time': naive_time_for_oracle, 'out_by': security_guard_identifier, 'gatepass_no': gatepass_no}
                )
            messages.success(request, f"Employee {gatepass_no} marked out successfully.")
        except Exception as e:
            messages.error(request, f"Error marking out employee {gatepass_no}: {e}")
        return redirect('mark_out_screen')
    return redirect('mark_out_screen')


@login_required
def mark_in_screen(request):
    employees_to_mark_in = [] # Initialize an empty list

    with connection.cursor() as cursor:
        cursor.execute("SELECT GATEPASS_NO, (NAME||' ('||PAYCODE||')') NAME, DEPARTMENT, OUT_TIME, OUT_BY FROM GATEPASS WHERE INOUT_STATUS = 'O' AND EARLY_LATE <> 'E' ")
        columns = [col[0] for col in cursor.description]
        raw_employees = cursor.fetchall()

    out_by_identifiers = list(set([row[4] for row in raw_employees if row[4]]))

    security_guard_names = {}
    if out_by_identifiers:
        guards = User.objects.filter(username__in=out_by_identifiers)
        for guard in guards:
            security_guard_names[guard.username] = guard.username

    # This loop processes each employee and appends them to the list
    for row in raw_employees:
        employee_dict = dict(zip(columns, row))
        out_by_identifier = str(employee_dict.get('OUT_BY', '')).strip()
        employee_dict['OUT_BY_NAME'] = security_guard_names.get(out_by_identifier, out_by_identifier)

        raw_out_time_from_db = employee_dict.get('OUT_TIME')
        if raw_out_time_from_db:
            if timezone.is_naive(raw_out_time_from_db):
                aware_time_in_oracle_tz = ORACLE_SERVER_TIMEZONE.localize(raw_out_time_from_db)
            else:
                aware_time_in_oracle_tz = raw_out_time_from_db.astimezone(ORACLE_SERVER_TIMEZONE)
            # Format OUT_TIME for display in the M/D/YYYY H:MM:SS AM/PM format
            employee_dict['OUT_TIME'] = aware_time_in_oracle_tz.strftime('%#m/%#d/%Y %#I:%M:%S %p')

        # Append employee_dict inside the loop, after it's fully populated
        employees_to_mark_in.append(employee_dict)

    return render(request, 'gatepass_app/mark_in_screen.html', {'employees': employees_to_mark_in})



@login_required
def process_mark_in(request, gatepass_no):
    if request.method == 'POST':
        current_time_aware_ist = timezone.now().astimezone(ORACLE_SERVER_TIMEZONE)
        naive_time_for_oracle = current_time_aware_ist.replace(tzinfo=None)

        security_guard_identifier = request.user.username

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE GATEPASS
                    SET IN_TIME = :in_time, IN_BY = :in_by, INOUT_STATUS = 'I'
                    WHERE GATEPASS_NO = :gatepass_no
                    """,
                    {'in_time': naive_time_for_oracle, 'in_by': security_guard_identifier, 'gatepass_no': gatepass_no}
                )
            messages.success(request, f"Employee {gatepass_no} marked in successfully.")
        except Exception as e:
            messages.error(request, f"Error marking in employee {gatepass_no}: {e}")
        return redirect('mark_in_screen')
    return redirect('mark_in_screen')


# --- DRF API Views ---

class GatePassViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows GatePass records to be viewed or updated for IN/OUT.
    """
    queryset = GatePass.objects.all()
    serializer_class = GatePassSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = False
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        gatepass_no = instance.GATEPASS_NO
        security_guard_identifier = request.user.username

        update_fields = []
        params = {}

        out_time_data = request.data.get('OUT_TIME')
        in_time_data = request.data.get('IN_TIME')

        if out_time_data:
            try:
                # Assuming out_time_data is now ISO format (YYYY-MM-DDTHH:MM:SS) from JS
                out_time_obj = datetime.fromisoformat(out_time_data)
                if timezone.is_naive(out_time_obj):
                    out_time_aware_ist = ORACLE_SERVER_TIMEZONE.localize(out_time_obj)
                else:
                    out_time_aware_ist = out_time_obj.astimezone(ORACLE_SERVER_TIMEZONE)
                params['out_time'] = out_time_aware_ist.replace(tzinfo=None)
                update_fields.append("OUT_TIME = :out_time")
            except ValueError:
                return Response({"detail": "Invalid OUT_TIME format."}, status=status.HTTP_400_BAD_REQUEST)

        if in_time_data:
            try:
                # Assuming in_time_data is now ISO format (YYYY-MM-DDTHH:MM:SS) from JS
                in_time_obj = datetime.fromisoformat(in_time_data)
                if timezone.is_naive(in_time_obj):
                    in_time_aware_ist = ORACLE_SERVER_TIMEZONE.localize(in_time_obj)
                else:
                    in_time_aware_ist = in_time_obj.astimezone(ORACLE_SERVER_TIMEZONE)
                params['in_time'] = in_time_aware_ist.replace(tzinfo=None)
                update_fields.append("IN_TIME = :in_time")
            except ValueError:
                return Response({"detail": "Invalid IN_TIME format."}, status=status.HTTP_400_BAD_REQUEST)

        # Direct fields from request.data
        if 'OUT_BY' in request.data:
            update_fields.append("OUT_BY = :out_by")
            params['out_by'] = request.data['OUT_BY']
        if 'IN_BY' in request.data:
            update_fields.append("IN_BY = :in_by")
            params['in_by'] = request.data['IN_BY']
        if 'INOUT_STATUS' in request.data:
            update_fields.append("INOUT_STATUS = :inout_status")
            params['inout_status'] = request.data['INOUT_STATUS']

        # Auto-fill OUT_BY/IN_BY and INOUT_STATUS if time is provided but _BY is not
        if 'OUT_BY' not in request.data and out_time_data:
            update_fields.append("OUT_BY = :out_by_auto")
            params['out_by_auto'] = security_guard_identifier
            if 'INOUT_STATUS' not in request.data: # Only set status if not explicitly provided
                update_fields.append("INOUT_STATUS = 'O'")

        if 'IN_BY' not in request.data and in_time_data:
            update_fields.append("IN_BY = :in_by_auto")
            params['in_by_auto'] = security_guard_identifier
            if 'INOUT_STATUS' not in request.data: # Only set status if not explicitly provided
                update_fields.append("INOUT_STATUS = 'I'")


        if not update_fields:
            return Response({"detail": "No updatable fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        sql = f"UPDATE GATEPASS SET {', '.join(update_fields)} WHERE GATEPASS_NO = :gatepass_no"
        params['gatepass_no'] = gatepass_no

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                # Fetch the updated instance for the response
                updated_instance = GatePass.objects.get(pk=gatepass_no)
                serializer = self.get_serializer(updated_instance)
                return Response(serializer.data)
        except Exception as e:
            return Response({"detail": f"Error updating GatePass: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)



@login_required
def create_manual_gatepass_entry(request):
    if request.method == 'POST':
        form = ManualGatePassForm(request.POST)
        if form.is_valid():
            paycode = form.cleaned_data['PAYCODE']
            gatepass_type = form.cleaned_data['GATEPASS_TYPE']

            try:
                # MARK_IN_TIME from hidden input (now YYYY-MM-DDTHH:MM:SS from JS)
                mark_in_time_str = request.POST.get('MARK_IN_TIME')
                # MARK_OUT_TIME from hidden input (YYYY-MM-DDTHH:MM:SS from JS)
                mark_out_time_str = request.POST.get('MARK_OUT_TIME')

                # Use datetime.fromisoformat for both, as they now should consistently be 'YYYY-MM-DDTHH:MM:SS'
                mark_in_time_naive = datetime.fromisoformat(mark_in_time_str)
                mark_out_time_naive = datetime.fromisoformat(mark_out_time_str)

                # Make them timezone-aware using the ORACLE_SERVER_TIMEZONE (IST)
                mark_in_time_aware = ORACLE_SERVER_TIMEZONE.localize(mark_in_time_naive)
                mark_out_time_aware = ORACLE_SERVER_TIMEZONE.localize(mark_out_time_naive)

                # Convert to naive datetime objects for Oracle insertion if needed
                naive_mark_in_time_for_oracle = mark_in_time_aware.replace(tzinfo=None)
                naive_mark_out_time_for_oracle = mark_out_time_aware.replace(tzinfo=None)

            except (ValueError, TypeError) as e:
                messages.error(request, f"Error parsing time data: {e}. Please ensure correct time format.")
                form = ManualGatePassForm(request.POST) # Pass POST data back to re-render form with errors
                return render(request, 'gatepass_app/create_manual_gatepass.html', {'form': form})


            current_date_aware = timezone.now().astimezone(ORACLE_SERVER_TIMEZONE)
            current_date_naive = current_date_aware.date() # Get just the date part for GATEPASS_DATE


            with connection.cursor() as cursor:
                # Find the highest sequence number for today's manual entries
                cursor.execute(
                    f"SELECT MAX(GATEPASS_NO) FROM GATEPASS"
                )
                last_seq = cursor.fetchone()[0]
                if last_seq:
                    next_seq = int(last_seq) + 1
                else:
                    next_seq = 1
                new_gatepass_no = f"{next_seq}"

                # Fetch employee name and department from EMP_MST based on PAYCODE
                emp_name = None
                department = None
                try:
                    cursor.execute(
                        """
                        SELECT a.EMPNAME, b.DEPARTMENTNAME
                        FROM savior9x.tblemployee a, SAVIOR9X.TBLDEPARTMENT b
                        WHERE LTRIM(RTRIM(a.PAYCODE)) = :p_paycode AND a.DEPARTMENTCODE = b.DEPARTMENTCODE
                        """,
                        {'p_paycode': paycode}
                    )
                    emp_details = cursor.fetchone()
                    if emp_details:
                        emp_name = emp_details[0]
                        department = emp_details[1]
                    else:
                        messages.warning(request, f"Employee with Pay Code {paycode} not found in master data. Proceeding without name/department.")
                        # Set default values if not found, so insertion doesn't fail
                        emp_name = "UNKNOWN"
                        department = "UNKNOWN"
                except Exception as e:
                    messages.warning(request, f"Could not fetch employee details for Pay Code {paycode}: {e}. Proceeding with default values.")
                    emp_name = "DB_ERROR"
                    department = "DB_ERROR"

                security_guard_identifier = request.user.username

                try:
                    cursor.execute(
                        """
                        INSERT INTO GATEPASS (
                            GATEPASS_NO, GATEPASS_DATE, PAYCODE, NAME, DEPARTMENT, GATEPASS_TYPE,
                            REMARKS, OUT_TIME, OUT_BY, IN_TIME, IN_BY, INOUT_STATUS, FINAL_STATUS,
                            REQUEST_TIME, AUTH, AUTH1_BY, AUTH1_STATUS, AUTH1_DATE, AUTH1_REMARKS,EMP_TYPE,USER_ID,BYPASS_REASON
                        ) VALUES (
                            :gatepass_no, :gatepass_date, :paycode, :name, :department, :gatepass_type,
                            :remarks, :out_time, :out_by, :in_time, :in_by, :inout_status, :final_status,
                            :request_time, :auth, :auth1_by, :auth1_status, :auth1_date, :auth1_remarks,:emp_type,:user_id,:bypass_reason
                        )
                        """,
                        {
                            'gatepass_no': new_gatepass_no,
                            'gatepass_date': current_date_naive, # Gatepass date is today
                            'paycode': paycode,
                            'name': emp_name,
                            'department': department,
                            'gatepass_type': gatepass_type,
                            'remarks': 'Manual Entry: Without intimation leave taken', # Added more context
                            'out_time': naive_mark_out_time_for_oracle + timedelta(hours=5, minutes=30), # Use parsed value from frontend
                            'out_by': security_guard_identifier,
                            'in_time': naive_mark_in_time_for_oracle + timedelta(hours=5, minutes=30), # Use parsed value from frontend
                            'in_by': security_guard_identifier,
                            'inout_status': 'I', # Marked as 'In' since both times are provided for a manual entry
                            'final_status': 'A', # Assuming manually approved
                            'request_time': mark_in_time_aware.strftime('%I:%M:%S %p'), # Use MARK_IN_TIME as REQUEST_TIME
                            'auth': 'N', # N = Not required for approval, or set to 'Y' if manual entry bypasses auth.
                                         # Given AUTH1_STATUS is 'B', 'N' for AUTH makes sense (No approval needed).
                            'auth1_by': None, # No specific approver for manual bypass
                            'auth1_status': 'B', # B = By-passed
                            'auth1_date': None, # No approval date for bypass
                            'auth1_remarks': 'Manual Entry', # Specific remark for bypass
                            'emp_type': None, # Adjust if you have a specific employee type for manual entries
                            'user_id': security_guard_identifier, # User who created this entry
                            'bypass_reason': 'Marked by security - Manual', # More specific reason
                        }
                    )
                    messages.success(request, f"Manual Gatepass {new_gatepass_no} created successfully.")
                    return redirect('mark_in_screen')
                except Exception as e:
                    messages.error(request, f"Error creating manual gatepass: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ManualGatePassForm()
    return render(request, 'gatepass_app/create_manual_gatepass.html', {'form': form})



@login_required
def get_employee_details(request):
    """
    AJAX endpoint to fetch employee name and department based on paycode.
    """
    paycode = request.GET.get('paycode', None)
    employee_name = "N/A"
    department_name = "N/A"

    if paycode:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT a.EMPNAME, b.DEPARTMENTNAME
                    FROM savior9x.tblemployee a, SAVIOR9X.TBLDEPARTMENT b
                    WHERE LTRIM(RTRIM(a.PAYCODE)) = :p_paycode AND a.DEPARTMENTCODE = b.DEPARTMENTCODE
                    """,
                    {'p_paycode': paycode}
                )
                emp_details = cursor.fetchone()
                if emp_details:
                    employee_name = emp_details[0]
                    department_name = emp_details[1]
            except Exception as e:
                # Log the error, but return N/A to the frontend
                print(f"Database error fetching employee details for {paycode}: {e}")

    return JsonResponse({
        'employee_name': employee_name,
        'department_name': department_name
    })