from rest_framework import serializers
from lytyfy_rest.models import LenderDeviabTransaction,Lender,LenderWithdrawalRequest,Invite


class LenderDeviabTransactionSerializer(serializers.ModelSerializer):
     class Meta:
        model = LenderDeviabTransaction
        fields=['lender','project','amount','payment_id','status','payment_mode','customer_email','customer_phone','customer_name','product_info','transactions_type']

class LenderSerializer(serializers.ModelSerializer):
     class Meta:
        model = Lender
        fields = ['first_name','mobile_number','email','last_name','dob','gender']

class LenderWithdrawalRequestSerializer(serializers.ModelSerializer):
	class Meta:
		model=LenderWithdrawalRequest
		fields = ['account_number','ifsc_code','account_name','bank_name','amount','lender']