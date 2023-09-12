from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Registeration(models.Model):

    # unique_uer_id = models.CharField(primary_key = True, default = uuid.uuid4, editable = False, null = False)
    aadhar = models.CharField(max_length=100, null = False)
    name = models.CharField(max_length=50, null= False)
    email = models.EmailField(max_length=150, null=False)
    annual_income = models.DecimalField(max_digits=15, decimal_places=2,null=False)
    credit_score = models.PositiveIntegerField(default=0, null=False)




class LoanApplied(models.Model):
    LOAN_TYPE =[
        ('Car', 'Car'),
        ('Home', 'Home'),
        ('Edcation', 'Education'),
        ('Personal', 'Personal'),
    ]
    aadhar = models.ForeignKey(Registeration, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=10, choices=LOAN_TYPE)
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=15, decimal_places=2)
    term_period = models.PositiveIntegerField()
    disbursal_date = models.DateField()
    is_closed = models.BooleanField(default=False)




class TransactionData(models.Model):
    TYPE = [
        ("C","Credit"),
        ("D","Debit"),
        ("L","Loan")
    ]
    # aadhar = models.UUIDField(default = uuid.uuid4)
    # unique_user_id = models.ForeignKey(Registeration, on_delete=models.CASCADE)
    aadhar = models.ForeignKey(Registeration, null = False, on_delete=models.CASCADE)
    loan_id = models.ForeignKey(LoanApplied, null = True, on_delete=models.CASCADE)
    event_date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TYPE)
    amount = models.DecimalField(max_digits=15,decimal_places=2, null=False)




class EMI(models.Model):
    loan_id = models.ForeignKey(LoanApplied, on_delete=models.CASCADE)
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    is_paid = models.BooleanField(default=False)



