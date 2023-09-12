from django.contrib import admin
from django.urls import path, include
from .views import RegisterUser, ApplyLoan, MakePayment, GetStatement

urlpatterns = [
    path('register-user', RegisterUser.as_view()),
    path('apply-loan', ApplyLoan.as_view()),
    path('make-payment', MakePayment.as_view()),
    path('get-statement', GetStatement.as_view()),

]
