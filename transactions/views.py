from django.db.models import Sum
from django.shortcuts import render
from django.views.generic import CreateView,ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from . models import Transaction
from . forms import DepositForm, WithdrawalForm, LoanRequestForm
from . constants import DEPOSIT,WITHDRAWAL, LOAN, LOAN_PAID
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.urls import reverse_lazy
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
# Create your views here.

def send_transaction_email(user, amount, subject, template):
        mail_subject = subject
        message = render_to_string(template, {
            'user' : user,
            'amount' : amount,
        })
        to_email = user.email
        send_email = EmailMultiAlternatives(mail_subject, '', to=[to_email])
        send_email.attach_alternative(message, "text/html")
        send_email.send()
     

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name =  'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account' : self.request.user.account,
        })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title' : self.title
        })
        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type' : DEPOSIT}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount') # user je tk ta deposit krtece seta nelam
        account = self.request.user.account
        account.balance += amount
        account.save(
            update_fields = ['balance']
        ) 
        messages.success(self.request, f'{amount}$ was deposited to your account successfully ')

        # email send krteci jei user tk deposit krce
        send_transaction_email(self.request.user, amount, "deposit message", 'transactions/deposit_email.html')

        # mail_subject = "deposit message"
        # message = render_to_string('transactions/deposit_email.html',{
        #     'user' : self.request.user,
        #     'amount' : amount,
        # })
        # to_email = self.request.user.email
        # send_email = EmailMultiAlternatives(mail_subject, '', to=[to_email])
        # send_email.attach_alternative(message, "text/html")
        # send_email.send()

        # Finished here


        return super().form_valid(form)
    

class withdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawalForm
    title = 'withdraw'

    def get_initial(self):
        initial = {'transaction_type' : WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance -= amount
        account.save(
            update_fields = ['balance']
        )
        messages.success(self.request, f'{amount}$ was withdrawal from your account successfully ')

        send_transaction_email(self.request.user, amount, "Withdrawal message", 'transactions/withdraw_email.html')
        return super().form_valid(form)
    
    
class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type' : LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(account = self.request.user.account, transaction_type = LOAN, loan_approve = True).count()   # user theke koita loan already exixt kore seta count krteci

        if current_loan_count >= 3:
            return HttpResponse('You have crossed your loan limits')
        
        messages.success(self.request, f'Loan request for {amount}$ has been successfull')
        
        send_transaction_email(self.request.user, amount, "Loan Request message", 'transactions/loan_email.html')
        return super().form_valid(form)
    

class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0
    context_object_name = 'report_list'

    def get_queryset(self):
        queryset = super().get_queryset().filter(   # user er sokol data ekhane store krlam
            account = self.request.user.account
        )

        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            # start_date_str and end_date_str ei duitake datetime input ee convert korlam
            # datetime.strptime(' ' ,"%Y-%m-%d").date()  eti akti built in funtion
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            queryset = queryset.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date)

            self.balance =  Transaction.objects.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
        
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account' : self.request.user.account
        })
        return context
    

class PayLoanView(LoginRequiredMixin, View):
    
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id = loan_id)

        if loan.loan_approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transactions = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(self.request, f'Your loan is more greather than your current balance')
                return redirect('loan_list')
            

class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account = user_account, transaction_type =  LOAN)
        return queryset

