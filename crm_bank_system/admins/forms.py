from django import forms
from users.models import CustomUser

class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'is_active']


class RespondToReportForm(forms.Form):
    admin_response = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Ответ администратора",
        help_text="Введите ваш ответ на жалобу."
    )