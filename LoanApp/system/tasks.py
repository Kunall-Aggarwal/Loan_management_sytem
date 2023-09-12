from celery import shared_task
from .models import Registeration, TransactionData

@shared_task
def calculate_credit_score(aadhar):
    try:
        # Retrieve the user based on the provided user_id
        user = Registeration.objects.get(aadhar=aadhar)

        # Retrieve all transactions for the user
        user_transactions = TransactionData.objects.filter(aadhar=aadhar)

        # Calculate the total account balance
        total_balance = sum([transaction.amount if transaction.transaction_type == 'CREDIT' else -transaction.amount for transaction in user_transactions])

        # Define credit score calculation rules
        balance_range = 1000000  # Rs. 10,00,000
        credit_score_change_per_range = 10
        range_size = 15000  # Rs. 15,000

        # Calculate credit score based on account balance
        if total_balance >= balance_range:
            credit_score = 900
        elif total_balance <= 100000:
            credit_score = 300
        else:
            difference = total_balance - 100000
            credit_score = 300 + (difference // range_size) * credit_score_change_per_range

        user.credit_score = credit_score
        user.save()
    except Registeration.DoesNotExist:
        print(f"User with id {aadhar} does not exist.")
    except Exception as e:
        print(f"An error occurred while calculating credit score: {str(e)}")
