from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import IntegrityError
from django.db import transaction
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from lytyfy_rest.utils import token_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from lytyfy_rest.models import LenderDeviabTransaction,Project,Lender,LenderCurrentStatus,LenderWallet,Token,LenderWithdrawalRequest,Invite,Borrower
import hashlib
import sendgrid
from random import randint
from rest_framework import serializers
from lytyfy_rest.serializers import LenderDeviabTransactionSerializer,LenderSerializer,LenderWithdrawalRequestSerializer
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Sum
from django.conf import settings

class HomePageApi(APIView):
	def get(self, request,format=None):
		investors=LenderDeviabTransaction.objects.all().values('lender').distinct().count()
		raised=int(sum(Project.objects.all().values_list('raisedAmount',flat=True)))
		borrowers=Borrower.objects.all().count()
		return Response({'backers':investors,'quantum':raised,'borrowers':borrowers},status=status.HTTP_200_OK)

class TransactionFormData(APIView):
	@token_required
	def get(self,request,format=None):
		if request.GET.get('amount',None) and request.GET.get('lenderId',None) and request.GET.get('projectId',None):
			try:
				params=request.GET
				data=Lender.objects.values('first_name','email','mobile_number').get(pk=params['lenderId'])
				if not data['first_name'] or not data['email']  and not data['mobile_number']:
					return Response({'error':"Please provide your profile details "},status=status.HTTP_400_BAD_REQUEST) 
				project = Project.objects.values('title').get(pk=params['projectId'])
				if not project:
					return Response({'error':"Project not found"},status=status.HTTP_400_BAD_REQUEST) 
				txnid=str(randint(1000000, 9999999))
				hashing= "vz70Zb" + "|" + txnid + "|" + params['amount'] + "|" + project['title'] + "|" + data['first_name'] + "|" + data['email'] + "|" + params['lenderId'] + "|" + params['projectId'] + "|||||||||" + "k1wOOh0b"
				response={}
				response['firstname']=data['first_name']
				response['email']=data['email']
				response['phone']=data['mobile_number']
				response['key']="vz70Zb"
			  	response['productinfo']= project['title']
			  	response['service_provider']="payu_paisa"
			  	response['hash']=  hashlib.sha512(hashing).hexdigest()
			  	response['furl']= "http://"+settings.HOST_DOMAIN+"/api/formcapture"
			  	response['surl']= "http://"+settings.HOST_DOMAIN+"/api/formcapture"
			  	response['udf2']= params['projectId']
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
				Project.objects.get(pk=trasaction['project']).raiseAmount(trasaction['amount']).save()
				got, created = LenderCurrentStatus.objects.get_or_create(lender_id=trasaction['lender'],project_id=trasaction['project'])
				got.updateCurrentStatus(trasaction['amount'])
				return redirect("http://"+settings.CLIENT_DOMAIN+"/#/dashboard")
			else:
				return redirect("http://"+settings.CLIENT_DOMAIN+"/#/dashboard")
		else:
			return redirect("http://"+settings.CLIENT_DOMAIN+"/#/dashboard") 	


class GetLenderDetail(APIView):
	@token_required
	def get(self,request,pk,format=None):
		try:
			lenderDetails=Lender.objects.values('id','first_name','email','mobile_number').get(pk=pk)
			return Response(lenderDetails,status=status.HTTP_200_OK)
		except:
			return Response({'error':"Lender not found"},status=status.HTTP_400_BAD_REQUEST)

class GetLenderInvestmentDetail(APIView):
	@token_required
	def get(self,request,pk,format=None):
		data={}
		ldt=LenderDeviabTransaction.objects.filter(lender_id=pk)
		data['transactions']=ldt.values('amount','payment_id','timestamp','project__title','transactions_type').order_by('-timestamp')
		map_data=ldt.filter(transactions_type="debit").values('project__title').annotate(investment = Sum('amount'))
		totalInvestment=0
		for transaction in data['transactions']:
			transaction['timestamp']=transaction['timestamp'].strftime("%d, %b %Y | %r")
			if transaction['transactions_type'] == "debit":
				totalInvestment+=transaction['amount']
		data['totalInvestment']=totalInvestment	
		data['investmentDetails']=LenderCurrentStatus.objects.filter(lender_id=pk).values('principal_repaid','interest_repaid','emr','project__title')
		totalPrincipalRepaid=totalInterestRepaid=totalEmr=0
		for investmentDetail in data['investmentDetails']:
			totalPrincipalRepaid+=investmentDetail['principal_repaid']
			totalInterestRepaid+=investmentDetail['interest_repaid']
			totalEmr+=investmentDetail['emr']			
			investmentDetail['investment']=[item['investment'] for item in map_data if item["project__title"] == investmentDetail["project__title"]][0]		
		data['totalPrincipalRepaid']=totalPrincipalRepaid
		data['totalInterestRepaid']=totalInterestRepaid
		data['totalEmr']=totalEmr
		data['credits']=LenderWallet.objects.values_list('balance').get(lender_id=pk)[0]
		totalAmountWithdraw=LenderWithdrawalRequest.objects.filter(status=1,lender_id=pk).values('amount')
		totalWithdrawal=0
		for withdraw in totalAmountWithdraw:
			totalWithdrawal+=withdraw['amount']
		data['totalWithdrawal']=totalWithdrawal
		return Response(data,status=status.HTTP_200_OK)
		


class UpdateLenderDetails(APIView):
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
	def post(self,request,format=None):
		params=request.data
		password = "XYZ"
		uid = params['uid']
		if params['email'] and password and uid:
			invite = Invite.objects.filter(email=params['email'],uid=uid,is_verified=False).first()
			if invite:
				invite.is_verified = True
				invite.save()
				try:
					user = User.objects.create_user(params['email'], None, password)
					user.is_active = False
					user.save()
					lender=Lender(user=user,email=user.username,gender=params.get('gender',None),dob=params.get('dob',None),first_name=params.get('name',None))
					lender.save()
					LenderWallet(lender=lender).save()
					sg = sendgrid.SendGridAPIClient(apikey="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")
					data = {  
							   "personalizations":[  
							      {  
							         "to":[  
							            {  
							               "email":"jsmith503@gmail.com"
							            }
							         ],
							         "substitutions":{  
							            "-email-":lender.email
							         }
							      }
							   ],
							   "from":{  
							      "email":"support@lytyfy.org"
							   },
							   "content":[  
							      {  
							         "type":"text/html",
							         "value":"Hello, Email!"
							      }
							   ],
							   "template_id": "e9eed821-b227-480d-bbe3-a932294a4f22"  
							}
					response = sg.client.mail.send.post(request_body=data)
					return Response({'message':"Sent for verification"},status=status.HTTP_200_OK)
				except:
					return Response({'error': 'User already exists'},status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response({'error': 'CANT ACCESS WITHOUT INVITATION OR ALREADY REGISTERED '},status=status.HTTP_401_UNAUTHORIZED)
		return Response({'error': 'Invalid Data'},status=status.HTTP_400_BAD_REQUEST)

class GetToken(APIView):
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
	@token_required
	def get(self,request,pk=None):
		request.token.delete()
		return Response({'success':"Succesfully token killed"},status=status.HTTP_200_OK)

class LenderWithdrawRequest(APIView):
	@token_required
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
			if serializer.is_valid():
				serializer.save()
				return Response({'message':"Request Send"},status=status.HTTP_200_OK)
			else:
				return Response({'error':"Invalid Request"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"No parameters found"},status=status.HTTP_400_BAD_REQUEST)

class VerifyToken(APIView):
	@token_required
	def get(self,request,format=None):
		pk=request.token.user.lender.id
		lenderDetails=Lender.objects.values('id','email','first_name').get(pk=pk)
		return Response(lenderDetails,status=status.HTTP_200_OK)
		

class RequestInvite(APIView):
	def post(self,request,format=None):
		email =request.data.get('email',None)
		if email:
			invite,created=Invite.objects.get_or_create(email=email)
			if created:
				import uuid
				uid = uuid.uuid4().hex
				invite.uid = uid
				invite.save()
				subject = """New Register"""
				html_message = "http://"+settings.CLIENT_DOMAIN+"/#/register?uid="+uid
				send_mail(subject,None, "support@lytyfy.org",[email], fail_silently=True,html_message=html_message)
				return Response({'msg':"Check your email for registration link"},status=status.HTTP_200_OK)
			return Response({'msg':"Email already exists"},status=status.HTTP_200_OK)
		return Response({'error':"Invalid request"},status=status.HTTP_400_BAD_REQUEST)


class ChangePassword(APIView):
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



class ListProject(APIView):
	def get(self, request,format=None):
		projects=Project.objects.all()
		data=[]
		for project in projects:
			project_detail={}
			project_detail['project_id']=project.id
			project_detail['borrowers']=project.borrowers.values('first_name','last_name','avatar')
			project_detail['lenders']=project.lenders.values('lender_id','lender__first_name','lender__avatar')
			project_detail['title']=project.title
			project_detail['loan_raised']=project.raisedAmount
			project_detail['loan_amount']=project.targetAmount
			project_detail['place']=project.place
			project_detail['description']=project.description
			project_detail['offlistDate']=project.offlistDate
			project_detail['repayment_term']=8
			project_detail['repayment_schedule']="Monthly"
			project_detail['status']= "running" if project.offlistDate > timezone.now() else "completed"
			project_detail['amount_to_invest']=""
			if request.GET.get('lenderId',None):
				project_detail['current_user']={}
				project_detail['current_user']['invested']=any(int(lender['lender_id']) == int(request.GET.get('lenderId')) for lender in project_detail['lenders'])
				if project_detail['current_user']['invested']:
					project_detail['current_user'].update(project.project_transactions.filter(lender_id=request.GET.get('lenderId',None)).aggregate(Sum('amount')))
			data.append(project_detail)
		return Response(data,status=status.HTTP_200_OK)


class ResetPassword(APIView):
	def post(self,request,format=None):
		params =request.data
		if params:
			user = User.objects.filter(username=params['email']).first()
			if user:
				password = User.objects.make_random_password()
				user.set_password(password)
				user.save()
				try:
					subject = """New Credentials"""
					html_message = """
					Dear Investor,<br><br>
					Username: """+params['email']+"""<br>
					Password: """+password+"""<br><br>
					Regards,<br>
					Team Lytyfy """
					send_mail(subject,None, "support@lytyfy.org",[params['email']], fail_silently=True,html_message=html_message)
					return Response({'msg':"New creds sent to your registered email"},status=status.HTTP_200_OK)
				except:
					return Response({'error': 'Something went wrong , kindly write us at support@lytyfy.org'},status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response({'error':"User not found"},status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error':"Invalid request"},status=status.HTTP_400_BAD_REQUEST)

class RepaymentToInvestors(APIView):
	@transaction.atomic
	def get(self, request,format=None):
		if request.GET.get('amount',None) and request.GET.get('project_id',None):
			amount = float(request.GET.get('amount',None))
			project_id = request.GET.get('project_id',None)
			lenders=LenderCurrentStatus.objects.filter(project=project_id)
			tmr = lenders.aggregate(Sum('emr'))
			for lender in lenders:
				share = round(amount * lender.emr/tmr['emr__sum'],2)
				trasaction={}
				trasaction['lender']=lender.lender.id
				trasaction['project']=lender.project.id
				trasaction['amount']=share
				trasaction['payment_id']=randint(11111111, 99999999)
				trasaction['transactions_type']="credit"
				serializer=LenderDeviabTransactionSerializer(data=trasaction)
				if serializer.is_valid():
					serializer.save()
					lender.FMI_paid(share)
					lender.lender.wallet.credit(share)
				else:
					return Response({'error':"Invalid request"},status=status.HTTP_400_BAD_REQUEST)
			return Response({'msg':"Succesfully wallet credited"},status=status.HTTP_200_OK)	

			
class FBToken(APIView):
	def post(self, request,format=None):
		if request.data.get('access_token'):
			from open_facebook.api import OpenFacebook
			facebook = OpenFacebook(request.data.get('access_token'))
			resp = facebook.get('me', fields='id,email')
			
			if resp['email']:
				user = User.objects.filter(username=resp['email']).first()
				if user:
					token_exist = Token.objects.filter(user=user)
					if token_exist:
						token=token_exist.first().token
						return Response({'token': token,'username': user.username},status=status.HTTP_200_OK)
					else:
						Token(user=user).save()
						new_token = Token.objects.filter(user=user).first().token
						return Response({'token': new_token,'username': user.username},status=status.HTTP_200_OK)
				else:
					invite,created=Invite.objects.get_or_create(email=resp['email'])
					if created:
						import uuid
						uid = uuid.uuid4().hex
						invite.uid = uid
						invite.save()
						subject = """New Register"""
						html_message = "http://"+settings.CLIENT_DOMAIN+"/#/register?uid="+uid
						send_mail(subject,None, "support@lytyfy.org",[resp['email']], fail_silently=True,html_message=html_message)
						return Response({'msg':"Check your email for registration link"},status=status.HTTP_200_OK)
					return Response({'msg':"Email already exists"},status=status.HTTP_200_OK)	
			else:
				return Response({'msg':"Email not available"},status=status.HTTP_200_OK)	
		return Response({'msg':"token not found"},status=status.HTTP_400_BAD_REQUEST)	

