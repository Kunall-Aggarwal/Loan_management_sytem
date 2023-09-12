from rest_framework import serializers
from .models import Registeration, TransactionData, LoanApplied, EMI

class RegisterationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registeration
        fields = ['aadhar', 'ansual_income', 'credit_score'] 



class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionData
        fields = ['aadhar', 'event_date', 'amount', 'transaction_type']  



class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplied
        fields = ['id', 'aadhar', 'loan_type', 'loan_amount', 'interest_rate', 'term_period', 'disbursal_date']  



class EMISerializer(serializers.ModelSerializer):
    class Meta:
        model = EMI
        fields = ['id', 'loan', 'due_date', 'amount_due', 'is_paid']  
