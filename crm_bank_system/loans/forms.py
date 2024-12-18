from django import forms

class LoanForm(forms.Form):
    amount = forms.DecimalField(
        label='Сумма кредита',
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите сумму кредита'})
    )
    interest_rate = forms.DecimalField(
        label='Процентная ставка',
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите процентную ставку'})
    )
    term = forms.IntegerField(
        label='Срок кредита (в месяцах)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите срок кредита'})
    )