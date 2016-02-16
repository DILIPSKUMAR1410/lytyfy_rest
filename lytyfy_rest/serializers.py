from rest_framework import serializers
from lytyfy_rest.models import LenderDeviabTransaction,Lender


class LenderDeviabTransactionSerializer(serializers.ModelSerializer):
     class Meta:
        model = LenderDeviabTransaction
        fields = '__all__'

class LenderSerializer(serializers.ModelSerializer):
     class Meta:
        model = Lender
        fields = ['first_name','mobile_number','email']
