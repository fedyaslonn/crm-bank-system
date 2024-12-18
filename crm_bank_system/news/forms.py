from django import forms
from .models import News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'news_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите текст новости',
                'rows': 5,
            }),
            'news_image': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите URL изображения',
            }),
        }
