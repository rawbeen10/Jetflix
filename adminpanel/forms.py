from django import forms
from movies.models import Movie, Genre, Language

class MovieForm(forms.ModelForm):
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text='Select one or more genres'
    )
    
    language = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        required=False,
        empty_label="Select Language",
        help_text='Select the movie language'
    )
    
    class Meta:
        model = Movie
        fields = ['title', 'year', 'description', 'thumbnail', 'video', 
                  'genres', 'language', 'cast', 'movie_length', 'review_stars', 
                  'views', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter movie title'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter release year'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter movie description'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'cast': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Tom Hanks, Morgan Freeman'
            }),
            'movie_length': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2h 30m'
            }),
            'review_stars': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '5'
            }),
            'views': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }