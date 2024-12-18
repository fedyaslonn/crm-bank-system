from django import forms
from .models import Report

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['description', 'screenshot']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Введите описание проблемы'}),
            'screenshot': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Введите URL скриншота'}),
        }
