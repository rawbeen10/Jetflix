from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from .forms import MovieForm

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')

    return render(request, 'adminpanel/login.html')

@staff_member_required
def admin_dashboard(request):
    total_users = User.objects.count()

    context = {
        'total_users': total_users,
    }

    return render(request, 'adminpanel/dashboard.html', context)

def add_movie(request):
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = MovieForm()

    return render(request, 'adminpanel/add_movie.html', {'form': form})