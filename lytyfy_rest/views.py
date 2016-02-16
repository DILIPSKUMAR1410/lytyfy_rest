from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import IntegrityError
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from lytyfy_rest.utils import token_required
from django.contrib.auth.models import User
from lytyfy_rest.models import LenderDeviabTransaction,Project,Lender,LenderCurrentStatus,LenderWallet,Token
import hashlib
from random import randint
from rest_framework import serializers
from lytyfy_rest.serializers import LenderDeviabTransactionSerializer,LenderSerializer

class HomePageApi(APIView):
	def get(self, request,format=None):
		count=LenderDeviabTransactions.objects.filter(project__id=1).values('lender').distinct().count()
		raised=Project.objects.get(pk=1).capitalAmount
		return Response({'total_investors':count,'raised':raised},status=status.HTTP_200_OK)

class TransactionFormData(APIView):
	def get(self,request,format=None):
		if request.GET.get('amount',None) and request.GET.get('lenderId',None):
			try:
				params=request.GET
				data=Lender.objects.values('first_name','email','mobile_number').get(pk=params['lenderId'])
				if not data['first_name'] or not data['email']  or not data['mobile_number']:
					return Response({'error':"Please provide your profile details "},status=status.HTTP_400_BAD_REQUEST) 
				txnid=str(randint(100000, 999999))
				hashing= "vz70Zb" + "|" + txnid + "|" + params['amount'] + "|" + "DhamdhaPilot" + "|" + data['first_name'] + "|" + data['email'] + "|" + params['lenderId'] + "|" + "1" + "|||||||||" + "k1wOOh0b"
				response={}
				response['firstname']=data['first_name']
				response['email']=data['email']
				response['phone']=data['mobile_number']
				response['key']="vz70Zb"
			  	response['productinfo']= "DhamdhaPilot"
			  	response['service_provider']="payu_paisa"
			  	response['hash']=  hashlib.sha512(hashing).hexdigest()
			  	response['curl']= "http://try.lytyfy.org/#/dashboard"
			  	response['furl']= "http://try.lytyfy.org/api/v1/projects/webhook/success"
			  	response['surl']= "http://try.lytyfy.org/api/v1/projects/webhook/success"
			  	response['udf2']= 1
			  	response['udf1']= params['lenderId']
			  	response['amount']= params['amount']
			  	response['txnid']= txnid
				return Response({'data':response},status=status.HTTP_200_OK)
			except:
				return Response({'error':"Lender not found"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"Invalid parameters"},status=status.HTTP_400_BAD_REQUEST)

class TransactionFormCapture(APIView):
	def post(self,request,format=None):
		params=request.data
		if params:
			serializer=LenderDeviabTransactionSerializer(data=params)
			if serializer.is_valid():
				serializer.save()
				return Response({'data':response},status=status.HTTP_200_OK)
			else:
				return Response({'error':"Invalid parameters"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"No parameters found"},status=status.HTTP_400_BAD_REQUEST)		


class GetLenderDetail(APIView):
	def get(self,request,pk,format=None):
		try:
			lenderDetails=Lender.objects.values('first_name','email','mobile_number').get(pk=pk)
			return Response({'lenderDetails':lenderDetails},status=status.HTTP_200_OK)
		except:
			return Response({'error':"Lender not found"},status=status.HTTP_400_BAD_REQUEST)

class GetLenderInvestmentDetail(APIView):
	def get(self,request,pk,format=None):
		try:
			investmentDetails=LenderCurrentStatus.objects.values('principal_repaid','interest_repaid','emr').get(lender__id=pk)
			investmentDetails['credits']=LenderWallet.objects.values_list('balance').get(lender__id=pk)[0]
			investmentDetails['transactions']=LenderDeviabTransaction.objects.filter(project__id=1,lender__id=pk).values('amount','payment_id','timestamp')
			totalInvestment=0
			for transaction in investmentDetails['transactions']:
				totalInvestment+=transaction['amount']
			investmentDetails['totalInvestment']=totalInvestment	
			totalAmountWithdraw=LenderDeviabTransaction.objects.filter(status=1,lender__id=pk).values('amount')
			totalWithdrawal=0
			for withdraw in totalAmountWithdraw:
				totalWithdrawal+=withdraw['amount']
			investmentDetails['totalWithdrawal']=totalWithdrawal
			return Response(investmentDetails,status=status.HTTP_200_OK)
		except:
			return Response({'error':"Lender not found"},status=status.HTTP_400_BAD_REQUEST)


class UpdateLenderDetails(APIView):
	def post(self,request,pk,format=None):
		params=request.data
		if params:
			lender=Lender.objects.get(pk=pk)
			serializer=LenderSerializer(lender,data=params)
			if serializer.is_valid():
				serializer.save()
				return Response({'message':"Profile Succesfully Updated"},status=status.HTTP_200_OK)
			else:
				return Response({'error':"Invalid parameters"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"No parameters found"},status=status.HTTP_400_BAD_REQUEST)		

class Register(APIView):
	@csrf_exempt
	def post(self,request,format=None):
		params=request.data
		if params['username'] is not None and params['password'] is not None:
			try:
				user = User.objects.create_user(params['username'], None, params['password'])
			except IntegrityError:
				return Response({'error': 'User already exists'},status=status.HTTP_400_BAD_REQUEST)
			token = Token.objects.create(user=user)
			return Response({'token': token.token,'username': user.username},status=status.HTTP_200_OK)
		return Response({'error': 'Invalid Data'},status=status.HTTP_400_BAD_REQUEST)

class GetToken(APIView):
	@csrf_exempt
	def post(self,request,format=None):
		username = request.POST.get('username', None)
		password = request.POST.get('password', None)

		if username is not None and password is not None:
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					token, created = Token.objects.get_or_create(user=user)
					return Response({'token': token.token,'username': user.username},status=status.HTTP_200_OK)
				else:
					return Response({'error': 'Invalid User'},status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response({'error': 'Invalid Username/Password'},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error': 'Invalid Data'},status=status.HTTP_400_BAD_REQUEST)

class KillToken(APIView):
	@csrf_exempt
	@token_required
	def post(self,request):
		request.token.delete()
		return Response({'success':"Succesfully token killed"},status=status.HTTP_200_OK)
