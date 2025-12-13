from django import forms
from movies.models import Movie


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = [
            'title', 'description', 'year', 'genre', 
            'cast', 'movie_length', 'review_stars', 
            'is_published', 'thumbnail', 'video'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter movie title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Enter movie description',
                'rows': 5
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. 2024'
            }),
            'genre': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cast': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Actor One, Actor Two'
            }),
            'movie_length': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. 2h 30m'
            }),
            'review_stars': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.1',
                'min': '0',
                'max': '5'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'video/*'
            }),
        }
        labels = {
            'title': 'Movie Title',
            'description': 'Description',
            'year': 'Release Year',
            'genre': 'Genre',
            'cast': 'Cast',
            'movie_length': 'Duration',
            'review_stars': 'Rating',
            'is_published': 'Publish Status',
            'thumbnail': 'Thumbnail Image',
            'video': 'Video File',
        }