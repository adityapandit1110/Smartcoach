from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.urls import reverse_lazy,reverse
from django.db.models import Count, Q
from django.db import IntegrityError
from django.conf import settings
from .models import Train, Coach, Defect, PassengerProfile
from .forms import PassengerRegisterForm

# ----------------------------
# Home redirects to login
# ----------------------------
def home(request):
    return redirect('login')


# ----------------------------
# Custom Login View with role-based redirect
# ----------------------------
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def form_invalid(self, form):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(self.request, "Username does not exist.")
            return redirect(reverse('login'))

        # If username exists, check password
        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(self.request, "Incorrect password.")
        else:
            messages.error(self.request, "Invalid login credentials.")  # fallback, usually won't hit

        return redirect(reverse('login'))

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse_lazy('admin_dashboard')
        elif user.groups.filter(name="Passenger").exists():
            return reverse_lazy('dashboard')
        elif user.groups.filter(name="Maintenance Staff").exists():
            return reverse_lazy('staff_dashboard')
        return reverse_lazy('login')


# ----------------------------
# Dashboard Routing
# ----------------------------
@login_required
def dashboard(request):
    user = request.user
    if user.groups.filter(name="Passenger").exists():
        return render(request, 'core/passenger_dashboard.html')
    elif user.groups.filter(name="Maintenance Staff").exists():
        return redirect('staff_dashboard')
    elif user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return render(request, 'core/no_access.html')


# ----------------------------
# Passenger Dashboard
# ----------------------------
@login_required
def passenger_dashboard(request):
    return render(request, 'core/passenger_dashboard.html')


# ----------------------------
# Report Defect View
# ----------------------------
@login_required
def report_defect(request):
    trains = Train.objects.all()
    coaches = []
    selected_train_id = request.POST.get("train")

    if selected_train_id:
        coaches = Coach.objects.filter(train_id=selected_train_id)

    if request.method == "POST" and 'selected_coaches' in request.POST:
        selected_coach_ids = request.POST.getlist('selected_coaches')
        defect_summaries = []

        for coach_id in selected_coach_ids:
            try:
                coach = Coach.objects.get(id=coach_id)
            except Coach.DoesNotExist:
                continue

            defects = request.POST.getlist(f'defects_{coach_id}')
            custom_defect = request.POST.get(f'custom_{coach_id}')
            image = request.FILES.get(f'image_{coach_id}')

            for defect_type in defects:
                custom_text = custom_defect if defect_type == 'Other' else ''
                defect = Defect.objects.create(
                    coach=coach,
                    defect_type=defect_type,
                    custom_defect_text=custom_text,
                    image=image,
                    reported_by=request.user
                )
                defect_summaries.append(f"""
🚆 Coach: {coach}
🔧 Defect: {defect_type if defect_type != 'Other' else 'Other - ' + custom_text}
📸 Photo: {'Yes' if image else 'No'}
📌 Status: {defect.status}
--------------------------""")

        if defect_summaries:
            subject = "SmartCoach | Defect Report Summary ✅"
            message = f"""
Dear {request.user.first_name or 'Passenger'},

Thank you for reporting the issue(s) through SmartCoach.

🛠️ Report Summary:
{''.join(defect_summaries)}

We’ll notify you of any updates.

Regards,
SmartCoach Team
"""
            send_mail(subject, message, settings.EMAIL_HOST_USER, [request.user.email], fail_silently=True)

        messages.success(request, "Defect(s) reported successfully!")
        return redirect('dashboard')

    return render(request, 'core/report_defect.html', {
        'trains': trains,
        'coaches': coaches,
        'selected_train_id': selected_train_id
    })


# ----------------------------
# View Coaches for Train (AJAX)
# ----------------------------
def get_coaches(request, train_id):
    coaches = Coach.objects.filter(train_id=train_id)
    data = {
        'coaches': [{'id': c.id, 'coach_number': c.coach_number} for c in coaches]
    }
    return JsonResponse(data)


# ----------------------------
# Staff Dashboard
# ----------------------------
def is_staff(user):
    return user.groups.filter(name='Maintenance Staff').exists() or user.is_superuser

@user_passes_test(is_staff)
def staff_dashboard(request):
    defects = Defect.objects.select_related('coach__train', 'reported_by').order_by('-date_reported')

    if request.method == 'POST':
        defect_id = request.POST.get('defect_id')
        new_status = request.POST.get('status')

        try:
            defect = Defect.objects.get(id=defect_id)
            previous_status = defect.status
            defect.status = new_status
            defect.save()

            messages.success(request, f"Defect ID {defect.id} updated to '{new_status}'")

            subject = "SmartCoach | Defect Status Updated 🔄"
            message = f"""
Dear {defect.reported_by.first_name or defect.reported_by.username},

Your defect report has been updated.

🆔 Defect ID: {defect.id}
🚆 Train: {defect.coach.train.name} ({defect.coach.train.number})
🚃 Coach: {defect.coach.coach_number}
🔧 Defect Type: {defect.defect_type}

🟡 Previous Status: {previous_status}
🟢 Updated Status: {new_status}

Regards,
SmartCoach Team
"""
            send_mail(subject, message, settings.EMAIL_HOST_USER, [defect.reported_by.email], fail_silently=True)

        except Defect.DoesNotExist:
            messages.error(request, "Defect not found.")

    return render(request, 'core/staff_dashboard.html', {'defects': defects})


# ----------------------------
# Passenger's Defects
# ----------------------------
@login_required
def my_defects(request):
    defects = Defect.objects.filter(reported_by=request.user).order_by('-date_reported')
    return render(request, 'core/my_defects.html', {'defects': defects})


# ----------------------------
# Admin Dashboard with Stats
# ----------------------------
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    status_counts = Defect.objects.values('status').annotate(count=Count('id'))

    electrical_q = Q(defect_type__icontains='light') | Q(defect_type__icontains='fan') | Q(defect_type__icontains='charging') | Q(defect_type__icontains='ac')
    mechanical_q = Q(defect_type__icontains='seat') | Q(defect_type__icontains='door') | Q(defect_type__icontains='chain') | Q(defect_type__icontains='handrest')
    civil_q = Q(defect_type__icontains='toilet') | Q(defect_type__icontains='mirror') | Q(defect_type__icontains='smell') | Q(defect_type__icontains='leak') | Q(defect_type__icontains='coach') | Q(defect_type__icontains='window')

    electrical_count = Defect.objects.filter(electrical_q).count()
    mechanical_count = Defect.objects.filter(mechanical_q).count()
    civil_count = Defect.objects.filter(civil_q).count()
    total_defects = Defect.objects.count()
    others_count = total_defects - (electrical_count + mechanical_count + civil_count)

    defect_type_counts = [
        {'defect_type': 'Electrical', 'count': electrical_count},
        {'defect_type': 'Mechanical', 'count': mechanical_count},
        {'defect_type': 'Civil', 'count': civil_count},
        {'defect_type': 'Others', 'count': others_count},
    ]

    pending_count = Defect.objects.filter(status='Pending').count()
    trains = Train.objects.all()

    return render(request, 'core/admin_dashboard.html', {
        'defect_type_counts': defect_type_counts,
        'status_counts': list(status_counts),
        'pending_count': pending_count,
        'trains': trains,
    })


# ----------------------------
# Register Passenger
# ----------------------------
def register_passenger(request):
    if request.method == 'POST':
        form = PassengerRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                raw_password = form.cleaned_data['password']
                user.set_password(raw_password)
                user.save()

                passenger_group = Group.objects.get(name='Passenger')
                user.groups.add(passenger_group)

                gender = form.cleaned_data['gender']
                PassengerProfile.objects.create(user=user, gender=gender)

                subject = 'Welcome to SmartCoach! 🚆'
                message = f'''
Dear {user.first_name},

Thank you for registering on SmartCoach Railway Defect Reporting.

👤 Username: {user.username}
🔑 Password: {raw_password}

You can now login and start reporting issues.

Regards,
SmartCoach Team 🚆
'''
                send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)

                messages.success(request, "Registration successful! Login credentials sent to your email.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Something went wrong: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PassengerRegisterForm()

    return render(request, 'core/register.html', {'form': form})


# ----------------------------
# Add Maintenance Staff
# ----------------------------
def add_maintenance_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.create_user(username=username, password=password)
            group = Group.objects.get(name='Maintenance Staff')
            user.groups.add(group)
            messages.success(request, "Maintenance Staff added successfully.")
        except IntegrityError:
            messages.error(request, "Username already exists.")
    return redirect('admin_dashboard')


# ----------------------------
# Add/Delete Train
# ----------------------------
@require_POST
def add_train(request):
    number = request.POST.get('train_number', '').strip()
    name = request.POST.get('train_name', '').strip()

    if not number or not name:
        messages.error(request, "Train number and name are required.")
        return redirect('admin_dashboard')

    if Train.objects.filter(number__iexact=number).exists():
        messages.error(request, "Train with this number already exists.")
        return redirect('admin_dashboard')

    try:
        Train.objects.create(number=number, name=name)
        messages.success(request, "Train added successfully.")
    except IntegrityError:
        messages.error(request, "Error while adding the train.")

    return redirect('admin_dashboard')

@require_POST
def delete_train(request, train_id):
    Train.objects.filter(id=train_id).delete()
    messages.success(request, "Train deleted successfully.")
    return redirect('admin_dashboard')


# ----------------------------
# Add/Delete Coach
# ----------------------------
@require_POST
def add_coach(request, train_id):
    coach_number = request.POST.get('coach_number')
    coach_type = request.POST.get('coach_type')

    if coach_number and coach_type:
        train = Train.objects.get(id=train_id)
        Coach.objects.create(train=train, coach_number=coach_number, coach_type=coach_type)
        messages.success(request, f"Coach {coach_number} added to {train.name}.")

    return redirect('admin_dashboard')

def delete_coach(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)
    coach_number = coach.coach_number
    train_name = coach.train.name
    coach.delete()
    messages.success(request, f"Coach {coach_number} removed from {train_name}.")
    return redirect('admin_dashboard')
