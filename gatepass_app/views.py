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

# DRF Imports
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import SecurityGuardSerializer, GatePassSerializer, EmployeeDetailsSerializer


# Existing HTML-rendering views (keep them as they are)
@login_required
def home_screen(request):
    security_guards = SecurityGuard.objects.all().order_by('username')
    return render(request, 'gatepass_app/home_screen.html', {'security_guards': security_guards})

@login_required
def mark_out_screen(request):
    employees_to_mark_out = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT GATEPASS_NO, NAME, DEPARTMENT, REMARKS, AUTH1_BY, AUTH1_DATE, REQUEST_TIME FROM GATEPASS WHERE FINAL_STATUS = 'A' AND OUT_TIME IS NULL AND EARLY_LATE <> 'L'")
        columns = [col[0] for col in cursor.description]
        raw_employees = cursor.fetchall()

    auth1_by_codes = list(set([str(row[4]).strip() for row in raw_employees if row[4] is not None and row[4]]))
    
    approved_by_names = {}
    if auth1_by_codes:
        param_names = [f"auth_code_{i}" for i in range(len(auth1_by_codes))]
        placeholders = ', '.join([f':{name}' for name in param_names])
        params = {param_names[i]: code for i, code in enumerate(auth1_by_codes)}

        try:
            with connection.cursor() as name_cursor:
                sql_query_for_names = f"SELECT ENTRY_NO, USER_NAME FROM USER_MST@dl10gto12c WHERE ENTRY_NO IN ({placeholders})"
                name_cursor.execute(sql_query_for_names, params)
                
                for entry_no, user_name in name_cursor.fetchall():
                    approved_by_names[str(entry_no).strip()] = user_name
        except Exception as e:
            print(f"Error fetching approved_by names from USER_MST: {e}")

    for row in raw_employees:
        employee_dict = dict(zip(columns, row))
        auth1_by_code_raw = employee_dict.get('AUTH1_BY')
        
        if auth1_by_code_raw is None:
            employee_dict['AUTH1_BY_NAME'] = "BY PASS HOD"
        else:
            auth1_by_code_stripped = str(auth1_by_code_raw).strip()
            employee_dict['AUTH1_BY_NAME'] = approved_by_names.get(auth1_by_code_stripped, auth1_by_code_stripped)
        
        employees_to_mark_out.append(employee_dict)

    return render(request, 'gatepass_app/mark_out_screen.html', {'employees': employees_to_mark_out})


@login_required
def process_mark_out(request, gatepass_no):
    if request.method == 'POST':
        current_time = timezone.now()
        security_guard_id = request.user.unique_code

        try:
            with connection.cursor() as cursor:
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
    return redirect('mark_out_screen')

@login_required
def mark_in_screen(request):
    employees_to_mark_in = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT GATEPASS_NO, NAME, DEPARTMENT, OUT_TIME, OUT_BY FROM GATEPASS WHERE INOUT_STATUS = 'O' AND EARLY_LATE <> 'E' ")
        columns = [col[0] for col in cursor.description]
        raw_employees = cursor.fetchall()

    out_by_codes = list(set([row[4] for row in raw_employees if row[4]]))
    
    security_guard_names = {}
    if out_by_codes:
        guards = SecurityGuard.objects.filter(unique_code__in=out_by_codes)
        for guard in guards:
            security_guard_names[guard.unique_code] = guard.username

    for row in raw_employees:
        employee_dict = dict(zip(columns, row))
        out_by_code = str(employee_dict.get('OUT_BY', '')).strip()
        employee_dict['OUT_BY_NAME'] = security_guard_names.get(out_by_code, out_by_code)
        
        employees_to_mark_in.append(employee_dict)

    return render(request, 'gatepass_app/mark_in_screen.html', {'employees': employees_to_mark_in})

@login_required
def process_mark_in(request, gatepass_no):
    if request.method == 'POST':
        current_time = timezone.now()
        security_guard_id = request.user.unique_code

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
    return redirect('mark_in_screen')

# This view will be replaced by a DRF APIView or ViewSet later for better consistency
@csrf_exempt
def get_employee_details(request, emp_code):
    if request.method == 'GET':
        employee_data = {}
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT EMP_NAME, GRADE, DESIG
                FROM emp_mst@dl10gto12c
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

class SecurityGuardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Security Guards to be viewed.
    """
    queryset = SecurityGuard.objects.all().order_by('username')
    serializer_class = SecurityGuardSerializer
    permission_classes = [IsAuthenticated] # Only authenticated users can access

class GatePassViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows GatePass records to be viewed or updated for IN/OUT.
    """
    queryset = GatePass.objects.all()
    serializer_class = GatePassSerializer
    permission_classes = [IsAuthenticated] # Only authenticated users can access

    # Override update methods for GatePass due to 'managed = False' and raw SQL updates
    def update(self, request, *args, **kwargs):
        # Handle full updates (PUT)
        partial = False
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        gatepass_no = instance.GATEPASS_NO
        current_time = timezone.now()
        security_guard_id = request.user.unique_code # Assuming unique_code for the logged-in guard

        # Extract only the fields that are allowed to be updated via the API
        out_time = serializer.validated_data.get('OUT_TIME', instance.OUT_TIME)
        out_by = serializer.validated_data.get('OUT_BY', instance.OUT_BY)
        in_time = serializer.validated_data.get('IN_TIME', instance.IN_TIME)
        in_by = serializer.validated_data.get('IN_BY', instance.IN_BY)
        inout_status = serializer.validated_data.get('INOUT_STATUS', instance.INOUT_STATUS)

        try:
            with connection.cursor() as cursor:
                # Construct the UPDATE query dynamically based on provided fields
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
                
                # Add current security guard if OUT_BY or IN_BY is being updated and not explicitly provided
                if 'OUT_BY' not in request.data and 'OUT_TIME' in request.data and out_time:
                    update_fields.append("OUT_BY = :out_by_auto")
                    params['out_by_auto'] = security_guard_id
                    inout_status = 'O' # Auto-set status if marking out
                    update_fields.append("INOUT_STATUS = 'O'")

                if 'IN_BY' not in request.data and 'IN_TIME' in request.data and in_time:
                    update_fields.append("IN_BY = :in_by_auto")
                    params['in_by_auto'] = security_guard_id
                    inout_status = 'I' # Auto-set status if marking in
                    update_fields.append("INOUT_STATUS = 'I'")

                if not update_fields:
                    return Response({"detail": "No updatable fields provided."}, status=status.HTTP_400_BAD_REQUEST)

                sql = f"UPDATE GATEPASS SET {', '.join(update_fields)} WHERE GATEPASS_NO = :gatepass_no"
                params['gatepass_no'] = gatepass_no

                cursor.execute(sql, params)
                # Refresh instance data after raw SQL update
                updated_instance = GatePass.objects.get(pk=gatepass_no)
                serializer = self.get_serializer(updated_instance)
                return Response(serializer.data)

        except Exception as e:
            return Response({"detail": f"Error updating GatePass: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        # Handle partial updates (PATCH) - reuse update logic
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

# Custom API View for Employee Details (replacing the old JsonResponse view)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_employee_details(request, emp_code):
    employee_data = {}
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT EMP_NAME, GRADE, DESIG
            FROM emp_mst@dl10gto12c
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
                serializer.is_valid(raise_exception=True) # Validate structure
                return Response(serializer.data)
            else:
                return Response({'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)