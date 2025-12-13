from django import forms
from movies.models import Movie

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = [
            'title',
            'year',
            'description',
            'thumbnail',
            'video',
            'genre',
            'cast',
            'movie_length',
            'review_stars',
            'views',
            'is_published',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'cast': forms.TextInput(attrs={'placeholder': 'Actor1, Actor2, Actor3'}),
            'movie_length': forms.TextInput(attrs={'placeholder': '2h 30m'}),
            'review_stars': forms.NumberInput(attrs={'min': 0, 'max': 5, 'step': 0.1}),
            'views': forms.NumberInput(attrs={'min': 0}),
        }
