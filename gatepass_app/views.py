# gatepass_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection # For raw SQL queries
from django.utils import timezone
from .models import GatePass
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt 
from django.contrib.auth import get_user_model 

# DRF Imports
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import GatePassSerializer, EmployeeDetailsSerializer 

# Import for timezone handling
from pytz import timezone as pytz_timezone 

# Define the Oracle server's actual timezone (IST)
ORACLE_SERVER_TIMEZONE = pytz_timezone('Asia/Kolkata')

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
    employees_to_mark_in = []
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

    for row in raw_employees:
        employee_dict = dict(zip(columns, row))
        out_by_identifier = str(employee_dict.get('OUT_BY', '')).strip()
        employee_dict['OUT_BY_NAME'] = security_guard_names.get(out_by_identifier, out_by_identifier)

        raw_out_time_from_db = employee_dict.get('OUT_TIME')
        if raw_out_time_from_db:
            if timezone.is_naive(raw_out_time_from_db):
                aware_time_in_oracle_tz = ORACLE_SERVER_TIMEZONE.localize(raw_out_time_from_db)
                employee_dict['OUT_TIME'] = aware_time_in_oracle_tz
        
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

@csrf_exempt
def get_employee_details(request, emp_code):
    if request.method == 'GET':
        employee_data = {}
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT EMP_NAME, GRADE, DESIG
                FROM emp_mst
                WHERE EMP_CODE = :emp_code
                """
                cursor.execute(sql, {'emp_code': emp_code})
                row = cursor.fetchone()

                if row:
                    full_name = row[0] if row[0] else ''
                    name_parts = full_name.split(' ', 1)
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
            print(f"Error fetching employee details for {emp_code}: {e}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


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
        current_time = timezone.now()
        security_guard_identifier = request.user.username 

        update_fields = []
        params = {}

        if 'OUT_TIME' in request.data:
            update_fields.append("OUT_TIME = :out_time")
            params['out_time'] = out_time
        if 'OUT_BY' in request.data:
            update_fields.append("OUT_BY = :out_by")
            params['out_by'] = out_by
        if 'IN_TIME' in request.data:
            update_fields.append("IN_TIME = :in_time")
            params['in_time'] = in_time
        if 'IN_BY' in request.data:
            update_fields.append("IN_BY = :in_by")
            params['in_by'] = in_by
        if 'INOUT_STATUS' in request.data:
            update_fields.append("INOUT_STATUS = :inout_status")
            params['inout_status'] = inout_status
        
        if 'OUT_BY' not in request.data and 'OUT_TIME' in request.data and out_time:
            update_fields.append("OUT_BY = :out_by_auto")
            params['out_by_auto'] = security_guard_identifier
            inout_status = 'O'
            update_fields.append("INOUT_STATUS = 'O'")

        if 'IN_BY' not in request.data and 'IN_TIME' in request.data and in_time:
            update_fields.append("IN_BY = :in_by_auto")
            params['in_by_auto'] = security_guard_identifier
            inout_status = 'I'
            update_fields.append("INOUT_STATUS = 'I'")

        if not update_fields:
            return Response({"detail": "No updatable fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        sql = f"UPDATE GATEPASS SET {', '.join(update_fields)} WHERE GATEPASS_NO = :gatepass_no"
        params['gatepass_no'] = gatepass_no

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                updated_instance = GatePass.objects.get(pk=gatepass_no)
                serializer = self.get_serializer(updated_instance)
                return Response(serializer.data)
        except Exception as e:
            return Response({"detail": f"Error updating GatePass: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_employee_details(request, emp_code):
    employee_data = {}
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT EMP_NAME, GRADE, DESIG
            FROM emp_mst
            WHERE EMP_CODE = :emp_code
            """
            cursor.execute(sql, {'emp_code': emp_code})
            row = cursor.fetchone()

            if row:
                full_name = row[0] if row[0] else ''
                name_parts = full_name.split(' ', 1)
                first_name = name_parts[0] if name_parts else ''
                last_name = name_parts[1] if len(name_parts) > 1 else ''

                data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'grade': row[1],
                    'desig': row[2],
                }
                serializer = EmployeeDetailsSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                return Response(serializer.data)
            else:
                return Response({'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)