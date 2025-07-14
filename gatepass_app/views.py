# gatepass_app/views.py

#django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection , transaction # for oracle connects , auto commit and rollback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

#django.contrib imports
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# self created files import
from .models import GatePass
from .forms import ManualGatePassForm, ManualMarkOutForm # Import both forms

# Import logging for better error reporting
import logging
logger = logging.getLogger(__name__) # Get an instance of a logger


# Import for timezone handling
from django.utils import timezone
from django.conf import settings 
import pytz
from datetime import timedelta ,datetime



DELHI_TIME = pytz.timezone('Asia/Kolkata')


User = get_user_model() # Get the currently active user model (which is now Django's default User)

@login_required
def home_screen(request):
    # Filter out superusers from the list of security guards
    # is_superuser=False will exclude any user marked as a superuser.
    security_guards = User.objects.filter(is_superuser=False).order_by('username')
    return render(request, 'gatepass_app/home_screen.html', {'security_guards': security_guards})

@login_required
def mark_out_screen(request):
    employees_to_mark_out = []
    data = GatePass.objects.filter(
        FINAL_STATUS = 'A',
        INOUT_STATUS = 'X').exclude(
        EARLY_LATE = 'L',
    ).values(
        'NAME','PAYCODE','EMP_TYPE','DEPARTMENT','UNIT_NAME','GATEPASS_DATE',
        'GATEPASS_TYPE','LUNCH','GATEPASS_NO','FINAL_STATUS','SYS_DATE','REQUEST_TIME'
    ).order_by ('-GATEPASS_DATE','-REQUEST_TIME')

    VALID_TIME  = timezone.now().astimezone()  - timedelta(hours=24)

    for I in data :
        gatepass_date, Cross = (I['GATEPASS_DATE'], 'YES') if I['SYS_DATE'] < VALID_TIME else ("", 'NO')
        dept_unit = f"{I['DEPARTMENT']}" if 'UNIT' in  I['DEPARTMENT'].upper() else f"{I['DEPARTMENT']} {I['UNIT_NAME']}"
       
        status = 'Approved' if I['FINAL_STATUS'] == 'A' else 'ByPass'
        lunch = ' + Lunch' if  I['LUNCH'] == 'A' else ' '
        processed_employee_data = {
            'NAME_DISPLAY' : f"{I['NAME']} - {I['PAYCODE']} - {I['EMP_TYPE']}",
            'DEPARTMENT_DISPLAY' :f"{dept_unit} {gatepass_date}",
            'STATUS_TYPE' : f" {status} - {I['GATEPASS_TYPE']} {lunch}",
            'GATEPASS_NO' : I['GATEPASS_NO'],
            'EMP_TYPE' : I['EMP_TYPE'],
            'GATEPASS_DATE' : I['GATEPASS_DATE'],
            'IS_CROSS_DATE' : Cross,
        }

        employees_to_mark_out.append(processed_employee_data)

    return render(request, 'gatepass_app/mark_out_screen.html', {'employees': employees_to_mark_out})


@login_required
def mark_in_screen(request):
    employees_to_mark_in = []
    data = GatePass.objects.filter(
       INOUT_STATUS = 'O').exclude(EARLY_LATE = 'E').values(
           'NAME','PAYCODE','EMP_TYPE','DEPARTMENT','UNIT_NAME','OUT_TIME','SYS_DATE','GATEPASS_NO'
    ).order_by('-OUT_TIME')

    VALID_TIME = timezone.now().astimezone()  - timedelta(hours=24)
    for I in data :
        Cross = "YES" if I['OUT_TIME'] < VALID_TIME else "NO"
        dept_name = I['DEPARTMENT'] if 'UNIT' in I['DEPARTMENT'] else  f"{I['DEPARTMENT']} ({I['UNIT_NAME']})"
        employee_dict = {
            'NAME_DISPLAY' : f"{I['NAME']} - {I['PAYCODE']} - {I['EMP_TYPE']}",
            'DEPARTMENT_DISPLAY' : dept_name,
            'OUT_TIME' : I['OUT_TIME']- timedelta(hours=5 , minutes=30),
            'IS_CROSS_DATE' : Cross,
            'GATEPASS_NO' : I['GATEPASS_NO'],
            'EMP_TYPE' : I['EMP_TYPE']
        }
        employees_to_mark_in.append(employee_dict)
    return render(request, 'gatepass_app/mark_in_screen.html', {'employees' :employees_to_mark_in})


@login_required
def markout_cross(request, gatepass_no):
    return _cross_action(request, gatepass_no, 'mark_out_screen')

@login_required
def markin_cross (request, gatepass_no):
    return _cross_action(request, gatepass_no, 'mark_in_screen')

def _cross_action(request, gatepass_no, redirect_url_name):
    """
    Helper function to handle the common logic for 'cross' actions (markin_cross, markout_cross).
    Calls the APPS.GATEPASS_ADJUSTMENT procedure.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.callproc('APPS.GATEPASS_ADJUSTMENT', [gatepass_no])

            messages.success(request, f"Gatepass No: {gatepass_no} processed for cross-date successfully.")
        except Exception as e:
            logger.error(f"Error processing Gatepass No: {gatepass_no}: {e}", exc_info=True)
            messages.error(request, f"Error processing Gatepass No: {gatepass_no}. Please try again. Details: {e}")

        return redirect(redirect_url_name)

    messages.warning(request, "Invalid request method. Please submit the form.")
    return redirect(redirect_url_name)


@login_required
def process_mark_out(request, gatepass_no):
    if request.method == 'POST':
        try :
            data = get_object_or_404(GatePass, GATEPASS_NO = gatepass_no)
            data.OUT_TIME = timezone.now().replace(microsecond=0).replace(tzinfo=None) + timedelta(hours= 11)
            if data.EL_MIN :
                data.IN_TIME = timezone.now().replace(microsecond=0).replace(tzinfo=None) + timedelta(hours= 11 , minutes= data.EL_MIN)
                data.IN_BY = 'System'     
            data.INOUT_STATUS = 'O'
            data.OUT_BY = request.user.username
            data.save()
            messages.success(request,f"Employee : {data.NAME} Mark out Successfully!")
        except Exception as e:
            logger.error(f"Error :with Gatepass no :{gatepass_no} : {e}",exc_info=True)
            messages.error(request,f"Error : with  Gatepass no : {gatepass_no} : {e}")

        return redirect('mark_out_screen')
    messages.warning(request , "Invalid request method. Please submit the form.")
    return redirect('mark_out_screen')


@login_required
def process_mark_in(request, gatepass_no):
    if request.method == 'POST':
        try:
            data = get_object_or_404(GatePass,GATEPASS_NO = gatepass_no)
            data.IN_TIME = timezone.now().replace(microsecond=0).replace(tzinfo=None) + timedelta(hours= 11)
            data.IN_BY = request.user.username
            data.INOUT_STATUS = 'I'
            data.save()
            messages.success(request, f"Employee : {data.NAME} is Successfully MARKED IN!")
        except Exception as e:
            logger.error(f"Error :with Gatepass no :{gatepass_no} : {e}",exc_info=True)
            messages.error(request,f"Error : with  Gatepass no : {gatepass_no} : {e}")
        return redirect('mark_in_screen')
    messages.warning(request , "Invalid request method. Please submit the form.")
    return redirect('mark_in_screen')


@login_required
def create_manual_gatepass_entry(request):
    if request.method == 'POST':
        form = ManualGatePassForm(request.POST)
        if form.is_valid():
            paycode = form.cleaned_data['PAYCODE']
            gatepass_type = form.cleaned_data['GATEPASS_TYPE']

            try:
                # MARK_IN_TIME from hidden input (YYYY-MM-DDTHH:MM:SS from JS)
                mark_in_time_str = request.POST.get('MARK_IN_TIME')
                # MARK_OUT_TIME from hidden input (YYYY-MM-DDTHH:MM:SS from JS)
                mark_out_time_str = request.POST.get('MARK_OUT_TIME')

                # Use datetime.fromisoformat for both, as they now should consistently be 'YYYY-MM-DDTHH:MM:SS'
                mark_in_time_naive = datetime.fromisoformat(mark_in_time_str)
                mark_out_time_naive = datetime.fromisoformat(mark_out_time_str)

                # Make them timezone-aware using the DELHI_TIME (IST)
                mark_in_time_aware = DELHI_TIME.localize(mark_in_time_naive)
                mark_out_time_aware = DELHI_TIME.localize(mark_out_time_naive)

                # Convert to naive datetime objects for Oracle insertion if needed
                naive_mark_in_time_for_oracle = mark_in_time_aware.replace(tzinfo=None)
                naive_mark_out_time_for_oracle = mark_out_time_aware.replace(tzinfo=None)

            except (ValueError, TypeError) as e:
                messages.error(request, f"Error parsing time data: {e}. Please ensure correct time format.")
                form = ManualGatePassForm(request.POST)  # Pass POST data back to re-render form with errors
                return render(request, 'gatepass_app/create_manual_gatepass.html', {'form': form})

            current_date_aware = timezone.now().astimezone(DELHI_TIME)
            current_date_naive = current_date_aware.date()  # Get just the date part for GATEPASS_DATE

            with connection.cursor() as cursor:
                # Find the highest sequence number for today's manual entries
                cursor.execute(
                    f"SELECT FN_GATEPASS_NO FROM DUAL"
                )
                
                new_gatepass_no = cursor.fetchone()[0]

                # Fetch employee name and department from EMP_MST based on PAYCODE
                emp_name = None
                department = None
                try:
                    cursor.execute(
                        """
                        SELECT A.EMP_NAME, B.DEPARTMENTNAME ,A.EMP_TYPE,C.SHORT_NAME FROM EMP_MST@DB_APPS_TO_SVR A, TBLDEPARTMENT@DB_APPS_TO_SVR B,
                        UNIT_MST@DB_APPS_TO_SVR C WHERE LTRIM(RTRIM(A.PAYCODE)) = :P_PAYCODE AND A.DEPT_CODE = B.DEPARTMENTCODE
                        AND A.UNIT_CODE = C.UNIT_CODE
                        """,
                        {'p_paycode': paycode}
                    )
                    emp_details = cursor.fetchone()
                    if emp_details:
                        emp_name = emp_details[0]
                        department = emp_details[1]
                        emp_type = emp_details[2]
                        unit_name = emp_details[3]
                    else:
                        messages.warning(request, f"Employee with Pay Code {paycode} not found in master data. Proceeding without name/department.")
                        # Set default values if not found, so insertion doesn't fail
                        emp_name = "UNKNOWN"
                        department = "UNKNOWN"
                        emp_type = "UNKNOWN"
                        unit_name = "UNKNOWN"
                except Exception as e:
                    messages.warning(request, f"Could not fetch employee details for Pay Code {paycode}: {e}. Proceeding with default values.")
                    emp_name = "DB_ERROR"
                    department = "DB_ERROR"
                    emp_type = "DB_ERROR"
                    unit_name = "DB_ERROR"

                security_guard_identifier = request.user.username

                try:
                    cursor.execute(
                        """
                        INSERT INTO GATEPASS@DB_APPS_TO_SVR (
                            GATEPASS_NO, GATEPASS_DATE, PAYCODE, NAME, DEPARTMENT, GATEPASS_TYPE,
                            REMARKS, OUT_TIME, OUT_BY, IN_TIME, IN_BY, INOUT_STATUS, FINAL_STATUS,
                            REQUEST_TIME, AUTH, AUTH1_BY, AUTH1_STATUS, AUTH1_DATE, AUTH1_REMARKS,
                            EMP_TYPE,USER_ID,BYPASS_REASON,EL_MIN,UNIT_NAME
                        ) VALUES (
                            :gatepass_no, :gatepass_date, :paycode, :name, :department, :gatepass_type,
                            :remarks, :out_time, :out_by, :in_time, :in_by, :inout_status, :final_status,
                            :request_time, :auth, :auth1_by, :auth1_status, :auth1_date, :auth1_remarks,
                            :emp_type,:user_id,:bypass_reason,:el_min,:unit_name
                        )
                        """,
                        {
                            'gatepass_no': new_gatepass_no,
                            'gatepass_date': current_date_naive,  # Gatepass date is today
                            'paycode': paycode,
                            'name': emp_name,
                            'department': department,
                            'gatepass_type': gatepass_type,
                            'remarks': 'Without intimation leave taken - Manual Entry',  # Added more context
                            'out_time': naive_mark_out_time_for_oracle,  # Use parsed value from frontend
                            'out_by': security_guard_identifier,
                            'in_time': naive_mark_in_time_for_oracle,  # Use parsed value from frontend
                            'in_by': security_guard_identifier,
                            'inout_status': 'I',  # Marked as 'In' since both times are provided for a manual entry
                            'final_status': 'A',  # Assuming manually approved
                            'request_time': mark_in_time_aware.strftime('%I:%M:%S %p'),  # Use MARK_IN_TIME as REQUEST_TIME
                            'auth': '1',  # N = Not required for approval, or set to 'Y' if manual entry bypasses auth.
                            # Given AUTH1_STATUS is 'B', 'N' for AUTH makes sense (No approval needed).
                            'auth1_by': None,  # No specific approver for manual bypass
                            'auth1_status': 'B',  # B = By-passed
                            'auth1_date': None,  # No approval date for bypass
                            'auth1_remarks': None,  # Specific remark for bypass
                            'emp_type': emp_type,  
                            'user_id': paycode,  # User who created this entry
                            'bypass_reason': 'Marked by security - Manual',  # More specific reason
                            'el_min' : form.cleaned_data['mark_out_duration'],
                            'unit_name' : unit_name,
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
def create_manual_mark_out_entry(request):
    if request.method == 'POST':
        form = ManualMarkOutForm(request.POST)
        if form.is_valid():
            paycode = form.cleaned_data['PAYCODE']
            gatepass_type = form.cleaned_data['GATEPASS_TYPE']

            try:
                # MARK_OUT_TIME from hidden input (YYYY-MM-DDTHH:MM:SS from JS)
                mark_out_time_str = request.POST.get('MARK_OUT_TIME')
                mark_out_time_naive = datetime.fromisoformat(mark_out_time_str)
                mark_out_time_aware = DELHI_TIME.localize(mark_out_time_naive)
                naive_mark_out_time_for_oracle = mark_out_time_aware.replace(tzinfo=None)

            except (ValueError, TypeError) as e:
                messages.error(request, f"Error parsing time data: {e}. Please ensure correct time format.")
                form = ManualMarkOutForm(request.POST) # Pass POST data back to re-render form with errors
                return render(request, 'gatepass_app/create_manual_mark_out.html', {'form': form})

            current_date_aware = timezone.now().astimezone(DELHI_TIME)
            current_date_naive = current_date_aware.date() # Get just the date part for GATEPASS_DATE

            with connection.cursor() as cursor:
                # Find the highest sequence number for today's manual entries
                cursor.execute(
                    f"SELECT FN_GATEPASS_NO FROM DUAL"
                )
                
                new_gatepass_no = cursor.fetchone()[0]


                # Fetch employee name and department from EMP_MST based on PAYCODE
                emp_name = None
                department = None
                try:
                    cursor.execute(
                        """
                        SELECT A.EMP_NAME, B.DEPARTMENTNAME ,A.EMP_TYPE FROM EMP_MST@DB_APPS_TO_SVR A, TBLDEPARTMENT@DB_APPS_TO_SVR B
                        WHERE LTRIM(RTRIM(A.PAYCODE)) = :P_PAYCODE AND A.DEPT_CODE = B.DEPARTMENTCODE
                        """,
                        {'p_paycode': paycode}
                    )
                    emp_details = cursor.fetchone()
                    if emp_details:
                        emp_name = emp_details[0]
                        department = emp_details[1]
                        emp_type = emp_details[2]
                    else:
                        messages.warning(request, f"Employee with Pay Code {paycode} not found in master data. Proceeding without name/department.")
                        emp_name = "UNKNOWN"
                        department = "UNKNOWN"
                        emp_type = "UNKNOWN"
                except Exception as e:
                    messages.warning(request, f"Could not fetch employee details for Pay Code {paycode}: {e}. Proceeding with default values.")
                    emp_name = "DB_ERROR"
                    department = "DB_ERROR"
                    emp_type = "DB_ERROR"

                security_guard_identifier = request.user.username

                try:
                    cursor.execute(
                        """
                        INSERT INTO GATEPASS@DB_APPS_TO_SVR (
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
                            'gatepass_date': current_date_naive,
                            'paycode': paycode,
                            'name': emp_name,
                            'department': department,
                            'gatepass_type': gatepass_type,
                            'remarks': 'Manual Out Entry by Security',
                            'out_time': naive_mark_out_time_for_oracle, # This is the current time
                            'out_by': security_guard_identifier,
                            'in_time': None, # No IN_TIME for a fresh OUT entry
                            'in_by': None,
                            'inout_status': 'O', # 'O' for Out
                            'final_status': 'A',
                            'request_time': mark_out_time_aware.strftime('%I:%M:%S %p'), # Use MARK_OUT_TIME as REQUEST_TIME
                            'auth': '1',
                            'auth1_by': None,
                            'auth1_status': 'B', # B = By-passed
                            'auth1_date': None,
                            'auth1_remarks': None,
                            'emp_type': emp_type,
                            'user_id': paycode,
                            'bypass_reason': 'Marked by security - Manual Out',
                        }
                    )
                    messages.success(request, f"Manual Mark Out Gatepass {new_gatepass_no} created successfully.")
                    return redirect('mark_out_screen') # Redirect to the mark out screen
                except Exception as e:
                    messages.error(request, f"Error creating manual mark out gatepass: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ManualMarkOutForm()
    return render(request, 'gatepass_app/create_manual_mark_out.html', {'form': form})


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