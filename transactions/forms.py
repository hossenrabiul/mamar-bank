from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']


    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True   # ei field disable thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput()  # user er theke hide thakbe
    
    def save(self, commit = True):
        self.instance.account = self.account
        self.instance.balance_after_transactions = self.account.balance
        return super().save()
    

class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposit_amount = 500
        amount = self.cleaned_data.get('amount')
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You have to deposit at least {min_deposit_amount}$'
            )
        return amount
    

class WithdrawalForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} in your account$'
            )
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You have to withdrwa at least {min_withdraw_amount}$'
            )
        if amount > max_withdraw_amount:
            raise f'You can withdraw at most {max_withdraw_amount}$'
        
        return amount
    

class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return amount

