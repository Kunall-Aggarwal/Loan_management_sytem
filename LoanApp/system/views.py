from datetime import date
from decimal import Decimal
import json
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from .serializer import RegisterationSerializer, TransactionSerializer, LoanSerializer, EMISerializer
from .models import Registeration, LoanApplied, TransactionData, EMI
import uuid
from django.db.models import Sum

# Create your views here.

class RegisterUser(APIView):
    
    def post(self, request):
        data = request.data
        serializer = RegisterationSerializer(data=data)
        if not serializer.is_valid():
            return HttpResponse('Entries do not match')

        #   celery_task
        account_balance = 0
        credit_score = 0

        if account_balance >= 1000000:
            credit_score = 900
        elif account_balance <= 100000:
            credit_score = 300
        else:
            difference = account_balance - 100000
            credit_score = 300 + (difference // 15000) * 10

        user = Registeration.objects.create(aadhar = data['aadhar'],
                                            name = data['name'],
                                            email = data['email'],
                                            annual_income = data['annual_income'],
                                            credit_score = credit_score)

        user.save()
        
        
        return



class ApplyLoan(APIView):

    def post(self, request):
        data = request.data
        serializer = LoanSerializer(data=request.data)
        if not serializer.is_valid():
            return HttpResponse(serializer.errors, status=400)
        
        unique_user_id = data['user_id']
        loan_type = data['loan_type']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        term_period = data['term_period']
        disbursement_date = data['disbursement_date']

        try:
            user_detail = Registeration.objects.get(aadhar = unique_user_id)
        except:
            return HttpResponse('No USER Found', status=400)

        if user_detail.credit_score < 450:
            return HttpResponse('Credit score not sufficient')
        
        if user_detail.annual_income < Decimal(150000):
            return HttpResponse('Annual income should be greater than or equal to 1,50,000')
        
        mapping = {
            "Car": 750000,
            "Home": 8500000,
            "Education": 5000000,
            "Personal": 1000000,
        }

        if loan_amount > mapping.get(loan_type, 0):
            return HttpResponse('Loan Amount exceeds the maximum limit.')
    
        if data.get('interest_rate') < 14:
            return HttpResponse('Interest rate should greater than or equal to 14')
        
        emi = ApplyLoan.calculate_emi(loan_amount, interest_rate, term_period)
        
        if not ApplyLoan.check_total_interest(emi, loan_amount, term_period):            
            return HttpResponse('Total interest in less than 100000')
        
        if not ApplyLoan.check_emi_criteria(emi, user_detail.annual_income/12):            
            return HttpResponse('Monthly income does not meet the requirement')
        


            
        loan = LoanApplied.objects.create(unique_user_id = data['unique_user_id'],
                                          loan_type = data['loan_type'],
                                          loam_amount = data['loan_amount'],
                                          interest_rate = data['interest_rate'],
                                          time_period = data['time_period'],
                                          disbursement_date = data['disbursement_date'])
        loan.save()
        

        emi_records = []
        for month in range(1, term_period + 1):
            emi_due_date = disbursement_date.replace(day=1)  # EMI due on the 1st of each month
            emi_due_date = emi_due_date.replace(month=emi_due_date.month + month - 1)
            emi_records.append(EMI(loan=loan, due_date=emi_due_date, amount_due=emi))

        emi_data = EMI.objects.bulk_create(emi_records)
        emi_data.save()

        return HttpResponse({'Loan_id': loan.id, 'Due_dates': emi_records}, status=200)

    def calculate_emi(principal, annual_rate, tenure_months):
        # Calculate monthly interest rate
        monthly_rate = (annual_rate / 12) / 100
        
        # Calculate EMI using the formula
        emi = principal * monthly_rate * (pow(1 + monthly_rate, tenure_months)) / (pow(1 + monthly_rate, tenure_months) - 1)
        
        return round(emi,2)

    def check_emi_criteria(emi, monthly_income):
        if emi <= 0.6 * monthly_income:
            return True
        else:
            return False

    def check_total_interest(emi, principal, tenure_months):
        # Calculate total interest paid over the tenure
        total_interest = (emi * tenure_months) - principal
        
        if total_interest > 10000:
            return True
        else:
            return False
    



class MakePayment(APIView):

    def post(self, request):
        data = request.data
        serializer = TransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return HttpResponse(serializer.errors, status=400)
            
        try:
            loan_details = LoanApplied.objects.get(id=data['loan_id'])
        except LoanApplied.DoesNotExist:
            return HttpResponse({'error': 'Loan not found.'}, status=400)
        

        # Get the next unpaid EMI for this loan
        try:
            next_emi = EMI.objects.filter(loan=data['loan_id'], is_paid=False).earliest('due_date')
        except EMI.DoesNotExist:
            return HttpResponse({'error': 'No pending EMIs for this loan.'}, status=400)


        existing_payment = TransactionData.objects.filter(loan=data['loan_id'], date=date.today()).first()
        if existing_payment:
            return HttpResponse({'error': 'Payment for the same date already exists.'}, status=400)


        # Check if the payment amount is less than the EMI amount
        if data['amount'] == next_emi.amount_due:
            next_emi.amount_due -= data['amount']
            next_emi.is_paid = True
            next_emi.save()

        # elif data['amount'] < next_emi.amount_due:
        #     next_emi.amount_due -= data['amount']
        #     next_emi.save()

        else:
            total_paid = TransactionData.objects.filter(loan=data['loan_id']).aggregate(total=Sum('amount'))['total'] or 0
            
            remaining_balance = loan_details.loan_amount - total_paid - data['amount']
            remaining_term = (next_emi.due_date.year - date.today().year) * 12 + (next_emi.due_date.month - date.today().month)
            
            if remaining_term > 0:
                new_emi = ApplyLoan.calculate_emi(remaining_balance, loan_details.interest_rate, remaining_term)
                next_emi.amount_due = new_emi
                next_emi.is_paid = True
                next_emi.save()

                revise_data = EMI.objects.filter(loan_id = loan_details.id, is_paid = False).update(amount_due = new_emi)
                revise_data.save()
            else:
                return HttpResponse({'error': 'Invalid payment date.'}, status=400)

        add_transaction = TransactionData.objects.create(aadhar = loan_details.aadhar,
                                       loan_id = loan_details.id,
                                       event_date = date.today(),
                                       transaction_type = "L",
                                       amount = data['amount'])

        add_transaction.save()
        # Return a response indicating successful payment registration
        return HttpResponse({'message': 'Payment registered successfully.'}, status=200)
        





class GetStatement(APIView):

    def get(self, request, loan_id):
        try:
            loan = LoanApplied.objects.get(id=loan_id)
        except LoanApplied.DoesNotExist:
            return HttpResponse({'error': 'Loan not found.'}, status=400)

        # Check if the loan is closed
        if loan.is_closed:
            return HttpResponse({'error': 'Loan is closed.'}, status=400)

        # Retrieve past transactions for the loan
        past_transactions = TransactionData.objects.filter(loan=loan, date__lte=date.now())

        # Retrieve future EMIs for the loan
        future_emis = EMI.objects.filter(loan=loan, due_date__gt=date.now(), is_paid=False)

        # Calculate the total amount paid towards the loan so far
        total_paid = past_transactions.aggregate(total=Sum('amount'))['total'] or 0

        # Calculate the total amount due for future EMIs
        total_due = future_emis.aggregate(total=Sum('amount_due'))['total'] or 0

        # Create a statement with details of past transactions and upcoming EMIs
        statement = {
            'Past_transactions': TransactionSerializer(past_transactions, many=True).data,
            'Upcoming_transactions': EMISerializer(future_emis, many=True).data,
            'Total_paid': total_paid,
            'Total_due': total_due,
            'Remaining_balance': loan.loan_amount - total_paid,
        }

        return HttpResponse(statement, status=200)