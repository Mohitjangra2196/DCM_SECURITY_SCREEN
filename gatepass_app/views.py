# gatepass_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection # For raw SQL queries
from django.utils import timezone
from .models import GatePass, SecurityGuard
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # Use carefully, for simple APIs
from django.db import connection

@login_required
def home_screen(request):
    security_guards = SecurityGuard.objects.all().order_by('username')
    return render(request, 'gatepass_app/home_screen.html', {'security_guards': security_guards})

@login_required
def mark_out_screen(request):
    employees_to_mark_out = []
    with connection.cursor() as cursor:
        # Initial query to get gate pass entries awaiting mark out
        cursor.execute("SELECT GATEPASS_NO, NAME, DEPARTMENT, REMARKS, AUTH1_BY, AUTH1_DATE, REQUEST_TIME FROM GATEPASS WHERE FINAL_STATUS = 'A' AND OUT_TIME IS NULL AND EARLY_LATE <> 'L'")
        columns = [col[0] for col in cursor.description]
        raw_employees = cursor.fetchall()

    # Store unique AUTH1_BY codes to avoid redundant lookups
    # Crucially, strip whitespace from the code here, as Oracle CHAR/VARCHAR2 can have padding
    # Only include non-NULL codes for lookup
    auth1_by_codes = list(set([str(row[4]).strip() for row in raw_employees if row[4] is not None and row[4]])) # Index 4 is AUTH1_BY
    
    # Dictionary to store emp_code -> emp_name mapping
    approved_by_names = {}
    if auth1_by_codes:
        # Build a list of named parameters for the IN clause
        param_names = [f"auth_code_{i}" for i in range(len(auth1_by_codes))]
        placeholders = ', '.join([f':{name}' for name in param_names])
        params = {param_names[i]: code for i, code in enumerate(auth1_by_codes)}

        try:
            with connection.cursor() as name_cursor:
                # *** UPDATED QUERY FOR HOD NAMES USING USER_MST ***
                sql_query_for_names = f"SELECT ENTRY_NO, USER_NAME FROM USER_MST@dl10gto12c WHERE ENTRY_NO IN ({placeholders})"
                name_cursor.execute(sql_query_for_names, params)
                
                for entry_no, user_name in name_cursor.fetchall():
                    # Strip spaces from entry_no coming from DB to match stripped input codes
                    approved_by_names[str(entry_no).strip()] = user_name
        except Exception as e:
            print(f"Error fetching approved_by names from USER_MST: {e}")
            # Log this error for debugging
            # messages.error(request, f"Could not fetch some approved by names: {e}")

    for row in raw_employees:
        employee_dict = dict(zip(columns, row))
        
        # Get the AUTH1_BY code from the current row
        auth1_by_code_raw = employee_dict.get('AUTH1_BY')
        
        # Determine what to display for 'Approved By'
        if auth1_by_code_raw is None: # Check if the raw value is NULL
            employee_dict['AUTH1_BY_NAME'] = "BY PASS HOD"
        else:
            auth1_by_code_stripped = str(auth1_by_code_raw).strip()
            # Use the stripped code to look up the name in the approved_by_names dictionary
            # Fallback to the code itself if the name isn't found
            employee_dict['AUTH1_BY_NAME'] = approved_by_names.get(auth1_by_code_stripped, auth1_by_code_stripped)
        
        employees_to_mark_out.append(employee_dict)

    return render(request, 'gatepass_app/mark_out_screen.html', {'employees': employees_to_mark_out})


@login_required
def process_mark_out(request, gatepass_no):
    if request.method == 'POST':
        current_time = timezone.now()
        security_guard_id = request.user.unique_code # Assuming unique_code is used for OUT_BY

        # Update the OUT_TIME, OUT_BY, and INOUT_STATUS in the Oracle database view
        # Using raw SQL is often necessary when dealing with views that don't allow direct ORM updates
        # or for specific column updates on views.
        try:
            with connection.cursor() as cursor:
                # Check if the view is directly updatable for these columns.
                # If not, you might need an updateable view or a stored procedure.
                cursor.execute(
                    """
                    UPDATE GATEPASS
                    SET OUT_TIME = :out_time, OUT_BY = :out_by, INOUT_STATUS = 'O'
                    WHERE GATEPASS_NO = :gatepass_no
                    """,
                    {'out_time': current_time, 'out_by': security_guard_id, 'gatepass_no': gatepass_no}
                )
            messages.success(request, f"Employee {gatepass_no} marked out successfully.")
        except Exception as e:
            messages.error(request, f"Error marking out employee {gatepass_no}: {e}")
        return redirect('mark_out_screen')
    return redirect('mark_out_screen') # Redirect if not a POST request

@login_required
def mark_in_screen(request):
    employees_to_mark_in = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT GATEPASS_NO, NAME, DEPARTMENT, OUT_TIME, OUT_BY FROM GATEPASS WHERE INOUT_STATUS = 'O' AND EARLY_LATE <> 'E' ")
        columns = [col[0] for col in cursor.description]
        raw_employees = cursor.fetchall()

    # Fetch security guard names for OUT_BY codes
    out_by_codes = list(set([row[4] for row in raw_employees if row[4]])) # Index 4 is OUT_BY
    
    # Dictionary to store unique_code -> username mapping from SecurityGuard model
    security_guard_names = {}
    if out_by_codes:
        # Use Django ORM for SecurityGuard as it's a Django model
        guards = SecurityGuard.objects.filter(unique_code__in=out_by_codes)
        for guard in guards:
            security_guard_names[guard.unique_code] = guard.username

    for row in raw_employees:
        employee_dict = dict(zip(columns, row))
        
        # Replace OUT_BY code with name, or use code if name not found
        out_by_code = str(employee_dict.get('OUT_BY', '')).strip()
        employee_dict['OUT_BY_NAME'] = security_guard_names.get(out_by_code, out_by_code)
        
        employees_to_mark_in.append(employee_dict)

    return render(request, 'gatepass_app/mark_in_screen.html', {'employees': employees_to_mark_in})

@login_required
def process_mark_in(request, gatepass_no):
    if request.method == 'POST':
        current_time = timezone.now()
        security_guard_id = request.user.unique_code # Assuming unique_code is used for IN_BY

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE GATEPASS
                    SET IN_TIME = :in_time, IN_BY = :in_by, INOUT_STATUS = 'I'
                    WHERE GATEPASS_NO = :gatepass_no
                    """,
                    {'in_time': current_time, 'in_by': security_guard_id, 'gatepass_no': gatepass_no}
                )
            messages.success(request, f"Employee {gatepass_no} marked in successfully.")
        except Exception as e:
            messages.error(request, f"Error marking in employee {gatepass_no}: {e}")
        return redirect('mark_in_screen')
    return redirect('mark_in_screen') # Redirect if not a POST request

@csrf_exempt
def get_employee_details(request, emp_code):
    if request.method == 'GET':
        employee_data = {}
        try:
            with connection.cursor() as cursor:
                # Select only EMP_NAME, GRADE, DESIG
                sql = """
                SELECT EMP_NAME, GRADE, DESIG
                FROM emp_mst@dl10gto12c
                WHERE EMP_CODE = :emp_code
                """
                cursor.execute(sql, {'emp_code': emp_code})
                row = cursor.fetchone()

                if row:
                    full_name = row[0] if row[0] else ''
                    name_parts = full_name.split(' ', 1) # Split at first space
                    first_name = name_parts[0] if name_parts else ''
                    last_name = name_parts[1] if len(name_parts) > 1 else ''

                    employee_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'grade': row[1],
                        'desig': row[2],
                    }
                    return JsonResponse({'success': True, 'data': employee_data})
                else:
                    return JsonResponse({'success': False, 'message': 'Employee not found'}, status=404)
        except Exception as e:
            # Log the error for debugging
            print(f"Error fetching employee details for {emp_code}: {e}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)