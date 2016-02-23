from rest_framework import serializers
from lytyfy_rest.models import LenderDeviabTransaction,Lender,LenderWithdrawalRequest,Invite


class LenderDeviabTransactionSerializer(serializers.ModelSerializer):
     class Meta:
        model = LenderDeviabTransaction
        fields = '__all__'

class LenderSerializer(serializers.ModelSerializer):
     class Meta:
        model = Lender
        fields = ['first_name','mobile_number','email']

class LenderWithdrawalRequestSerializer(serializers.ModelSerializer):
	class Meta:
		model=LenderWithdrawalRequest

class RequestInviteSerializer(serializers.ModelSerializer):
	class Meta:
		model=Invite