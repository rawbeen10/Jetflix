from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken.')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('Username may only contain letters, digits and @/./+/-/_ characters.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        # Proper format check
        import re
        pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError('Enter a valid email address (e.g. name@example.com).')
        local, domain = email.split('@', 1)
        if '..' in email:
            raise ValidationError('Email address cannot contain consecutive dots.')
        if local.startswith('.') or local.endswith('.'):
            raise ValidationError('Email local part cannot start or end with a dot.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        username = self.cleaned_data.get('username', '')
        email    = self.cleaned_data.get('email', '').split('@')[0]

        if not password:
            return password

        # Minimum length
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        # Must have uppercase
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')

        # Must have lowercase
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')

        # Must have digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number.')

        # Must have special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-\+\=\[\]\/\\]', password):
            raise ValidationError('Password must contain at least one special character (!@#$%^&* etc).')

        # Too common
        common = ['password', '12345678', 'qwerty', 'abc123', 'letmein', 'welcome', 'monkey', 'dragon']
        if password.lower() in common:
            raise ValidationError('This password is too common. Please choose a stronger one.')

        # Similar to username
        if username and username.lower() in password.lower():
            raise ValidationError('Password is too similar to your username.')

        # Similar to email prefix
        if email and len(email) >= 4 and email.lower() in password.lower():
            raise ValidationError('Password is too similar to your email address.')

        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        return cleaned_data
