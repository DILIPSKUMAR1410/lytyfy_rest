from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import IntegrityError
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from lytyfy_rest.utils import token_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from lytyfy_rest.models import LenderDeviabTransaction,Project,Lender,LenderCurrentStatus,LenderWallet,Token,LenderWithdrawalRequest,Invite
import hashlib
from random import randint
from rest_framework import serializers
from lytyfy_rest.serializers import LenderDeviabTransactionSerializer,LenderSerializer,LenderWithdrawalRequestSerializer
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.core.mail import send_mail


class HomePageApi(APIView):
	def get(self, request,format=None):
		count=LenderDeviabTransaction.objects.filter(project__id=1).values('lender').distinct().count()
		raised=Project.objects.get(pk=1).capitalAmount
		return Response({'backers':count,'quantum':raised},status=status.HTTP_200_OK)

class TransactionFormData(APIView):
	@csrf_exempt
	@token_required
	def get(self,request,format=None):
		if request.GET.get('amount',None) and request.GET.get('lenderId',None):
			try:
				params=request.GET
				data=Lender.objects.values('first_name','email','mobile_number').get(pk=params['lenderId'])
				if not data['first_name'] or not data['email']  and not data['mobile_number']:
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
			  	response['furl']= "http://54.254.195.114/api/formcapture"
			  	response['surl']= "http://54.254.195.114/api/formcapture"
			  	response['udf2']= 1
			  	response['udf1']= params['lenderId']
			  	response['amount']= params['amount']
			  	response['txnid']= txnid
				return Response(response,status=status.HTTP_200_OK)
			except:
				return Response({'error':"Lender not found"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"Invalid parameters"},status=status.HTTP_400_BAD_REQUEST)

class TransactionFormCapture(APIView):
	@csrf_exempt
	# @token_required
	def post(self,request,format=None):
		params=dict(request.data)
		if params and params['status'][0]=="success":
			trasaction={}
			trasaction['lender']=params['udf1'][0]
			trasaction['project']=params['udf2'][0]
			trasaction['amount']=float(params['amount'][0])
			trasaction['customer_email']=params['email'][0]
			trasaction['payment_id']=params['payuMoneyId'][0]
			trasaction['status']=params['status'][0]
			trasaction['payment_mode']=1
			trasaction['customer_phone']=params['phone'][0]
			trasaction['customer_name']=params['firstname'][0]
			trasaction['product_info']=params['productinfo'][0]
			serializer=LenderDeviabTransactionSerializer(data=trasaction)
			if serializer.is_valid():
				serializer.save()
				Project.objects.get(pk=trasaction['project']).creditCapitalAmount(trasaction['amount']).save()
				LenderCurrentStatus.objects.get(lender__id=trasaction['lender']).updateCurrentStatus(trasaction['amount']).save()
				return redirect("http://try.lytyfy.org/#/dashboard")
			else:
				return redirect("http://try.lytyfy.org/#/dashboard")
		else:
			return redirect("http://try.lytyfy.org/#/dashboard") 	


class GetLenderDetail(APIView):
	@csrf_exempt
	@token_required
	def get(self,request,pk,format=None):
		try:
			lenderDetails=Lender.objects.values('id','first_name','email','mobile_number').get(pk=pk)
			return Response(lenderDetails,status=status.HTTP_200_OK)
		except:
			return Response({'error':"Lender not found"},status=status.HTTP_400_BAD_REQUEST)

class GetLenderInvestmentDetail(APIView):
	@csrf_exempt
	@token_required
	def get(self,request,pk,format=None):
		
		investmentDetails=LenderCurrentStatus.objects.values('principal_repaid','interest_repaid','emr').get(lender__id=pk)
		investmentDetails['credits']=LenderWallet.objects.values_list('balance').get(lender__id=pk)[0]
		investmentDetails['transactions']=LenderDeviabTransaction.objects.filter(project__id=1,lender__id=pk).values('amount','payment_id','timestamp')
		totalInvestment=0
		for transaction in investmentDetails['transactions']:
			transaction['type']="debit"
			transaction['timestamp']=transaction['timestamp'].strftime("%d, %b %Y | %r")
			totalInvestment+=transaction['amount']
		investmentDetails['totalInvestment']=totalInvestment	
		totalAmountWithdraw=LenderWithdrawalRequest.objects.filter(status=1,lender__id=pk).values('amount')
		totalWithdrawal=0
		for withdraw in totalAmountWithdraw:
			totalWithdrawal+=withdraw['amount']
		investmentDetails['totalWithdrawal']=totalWithdrawal
		return Response(investmentDetails,status=status.HTTP_200_OK)
		


class UpdateLenderDetails(APIView):
	@csrf_exempt
	@token_required
	def post(self,request,pk,format=None):
		params=request.data
		if params:
			lender=Lender.objects.get(pk=pk)
			serializer=LenderSerializer(lender,data=params,partial=True)
			if serializer.is_valid():
				serializer.save()
				return Response({'message':"Profile Succesfully Updated"},status=status.HTTP_200_OK)
			else:
				return Response({'error':"Invalid parameters"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"No parameters found"},status=status.HTTP_400_BAD_REQUEST)		

class Register(APIView):
	@csrf_exempt
	def get(self,request,format=None):
		params=request.GET
		if params['username'] is not None:
			try:
				user = User.objects.create_user(params['username'], None, "deviab@123")
				lender=Lender(user=user,email=user.username)
				lender.save()
				LenderCurrentStatus(lender=lender).save()
				LenderWallet(lender=lender).save()
			except IntegrityError:
				return Response({'error': 'User already exists'},status=status.HTTP_400_BAD_REQUEST)
			token = Token.objects.create(user=user)
			return Response({'token': token.token,'username': user.username},status=status.HTTP_200_OK)
		return Response({'error': 'Invalid Data'},status=status.HTTP_400_BAD_REQUEST)

class GetToken(APIView):
	@csrf_exempt
	def post(self,request,format=None):
		username = request.data.get('username', None)
		password = request.data.get('password', None)
		if username is not None and password is not None:
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					token_exist = Token.objects.filter(user=user)
					if token_exist:
						token=token_exist.first().token
						return Response({'token': token,'username': user.username},status=status.HTTP_200_OK)	
					else:
						Token(user=user).save()
						new_token = Token.objects.filter(user=user).first().token
						return Response({'token': new_token,'username': user.username},status=status.HTTP_200_OK)
				else:
					return Response({'error': 'Invalid User'},status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response({'error': 'Invalid Username/Password'},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error': 'No Credentials found'},status=status.HTTP_400_BAD_REQUEST)

class KillToken(APIView):
	@csrf_exempt
	@token_required
	def get(self,request,pk=None):
		request.token.delete()
		return Response({'success':"Succesfully token killed"},status=status.HTTP_200_OK)

class LenderWithdrawRequest(APIView):
	def post(self,request,pk,format=None):
		balance=LenderWallet.objects.get(lender__id=pk).balance
		if balance < 1001:
			return Response({'message':"your balance is less than 1000"},status=status.HTTP_200_OK)
		pending_request=LenderWithdrawalRequest.objects.filter(lender__id=pk,status=0).values('status')
		if pending_request:
			return Response({'message':"you still have a pending request"},status=status.HTTP_200_OK)
		params=request.data
		if params:
			params['amount']=balance
			params['lender']=pk
			serializer=LenderWithdrawalRequestSerializer(data=params)
			serializer.is_valid()
			print serializer.errors
			if serializer.is_valid():
				serializer.save()
				return Response({'message':"Request Send"},status=status.HTTP_200_OK)
			else:
				return Response({'error':"Invalid Request"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"No parameters found"},status=status.HTTP_400_BAD_REQUEST)

class VerifyToken(APIView):
	@csrf_exempt
	@token_required
	def get(self,request,format=None):
		pk=request.token.user.lender.id
		lenderDetails=Lender.objects.values('id','email','first_name').get(pk=pk)
		return Response(lenderDetails,status=status.HTTP_200_OK)
		

class RequestInvite(APIView):
	def post(self,request,format=None):
		params =request.data
		if params:
			invite,created= Invite.objects.get_or_create(email=params['email'])
			if created:
				try:
					subject = """New request for invitation by """+params['email']
					approve_link = "http://54.254.195.114/api/lender/register?username="+params['email']
					html_message = 'Hi Deepak, We got a new request for invitation. Click YES to approve else ignore this mail<br> <a href='+approve_link+'>YES</a>'
					send_mail(subject,None, "support@lytyfy.org",['connect2sdeepak@gmail.com'], fail_silently=True,html_message=html_message)
					return Response({'message':" Invite will be sent to your Email"},status=status.HTTP_200_OK)
				except:
					return Response({'message':" Invite will be sent to your Email"},status=status.HTTP_200_OK)
			else:
				return Response({'message':"Email is already registered"},status=status.HTTP_200_OK)
		else:
			return Response({'error':"No parameters found"},status=status.HTTP_400_BAD_REQUEST)


class ChangePassword(APIView):
	@csrf_exempt
	@token_required
	def post(self,request,pk,format=None):
		params=request.data
		if params:
			try:
				hash_password=Lender.objects.values('user__password').get(pk=pk)
				flag=check_password(params['old_password'],hash_password['user__password'])
				if flag:
					user=Lender.objects.get(pk=pk).user
					user.set_password(params['new_password'])
					user.save()
					return Response({'message':"Password sucessfully changed"},status=status.HTTP_200_OK)
				else:
					return Response({'error':"Wrong old password"},status=status.HTTP_400_BAD_REQUEST)
			except:
				return Response({'error':"lender not found"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"Invalid request"},status=status.HTTP_400_BAD_REQUEST)
			


