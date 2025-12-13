from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm


# Home / Register
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. You can now log in.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'home/register.html', {'form': form})

# Login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'movies/landing.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('home')

def search_view(request):
    return render(request, 'home/search.html')

def watchlist_view(request):
    return render(request, 'home/watchlist.html')   

def watch_history_view(request):    
    return render(request, 'home/watch_history.html')

def edit_profile_view(request):
    return render(request, 'home/edit_profile.html')    

def movies_view(request):
    return render(request, 'home/movies.html')      
