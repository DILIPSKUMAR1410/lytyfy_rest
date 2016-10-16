from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import IntegrityError
from django.db import transaction
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from lytyfy_rest.utils import token_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from lytyfy_rest.models import LenderDeviabTransaction, Project, Lender, LenderCurrentStatus, LenderWallet, Token, LenderWithdrawalRequest, Invite, Borrower
import hashlib
import sendgrid
from random import randint
from rest_framework import serializers
from lytyfy_rest.serializers import LenderDeviabTransactionSerializer, LenderSerializer, LenderWithdrawalRequestSerializer
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Sum
from django.conf import settings
from open_facebook.api import OpenFacebook, FacebookAuthorization


class HomePageApi(APIView):

    def get(self, request, format=None):
        investors = LenderDeviabTransaction.objects.all().values('lender').distinct().count()
        raised = int(
            sum(Project.objects.all().values_list('raisedAmount', flat=True)))
        borrowers = Borrower.objects.all().count()
        return Response({'backers': investors + 18, 'quantum': raised, 'borrowers': borrowers}, status=status.HTTP_200_OK)


class DashBoardApi(APIView):

    @token_required
    def get(self, request, format=None):
        lender = request.token.user.lender
        data = {}
        lcs = LenderCurrentStatus.objects.filter(lender=lender).values(
            'principal_repaid', 'principal_left', 'emr')
        totalInvestment = totalEmr = 0
        for current_status in lcs:
            totalInvestment += current_status['principal_repaid'] + \
                current_status['principal_left']
            totalEmr += current_status['emr']
        data['totalInvestment'] = totalInvestment
        data['totalEmr'] = totalEmr
        data['credits'] = LenderWallet.objects.get(lender=lender).balance
        return Response(data, status=status.HTTP_200_OK)


class WalletTransactions(APIView):

    @token_required
    def get(self, request, format=None):
        lender = request.token.user.lender
        ldt = LenderDeviabTransaction.objects.select_related(
            'project').filter(lender=lender)
        data = ldt.values('amount', 'wallet_money', 'payment_id', 'timestamp',
                          'project__title', 'transactions_type').order_by('-timestamp')
        for datum in data:
            datum['timestamp'] = datum['timestamp'].strftime("%d, %b %Y | %r")
            if datum['wallet_money']:
                datum['amount'] += datum['wallet_money']
        return Response(data, status=status.HTTP_200_OK)


class LenderPortfolio(APIView):

    @token_required
    def get(self, request, format=None):
        lender = request.token.user.lender
        data = LenderCurrentStatus.objects.select_related('project').filter(lender=lender).values('principal_repaid', 'emr', 'tenure_left', 'principal_left',
                                                                                                  'interest_repaid', 'interest_left', 'project__title', 'project__targetAmount', 'project__raisedAmount', 'project__offlistDate')
        return Response(data, status=status.HTTP_200_OK)


class TransactionFormData(APIView):

    @transaction.atomic
    @token_required
    def get(self, request, format=None):
        params = request.GET
        lender = request.token.user.lender
        balance = lender.wallet.balance
        try:
            if params.get('amount', None) and params.get('projectId', None):
                project = Project.objects.filter(
                    pk=params['projectId']).first()
                if not project:
                    return Response({'error': "Project not found"}, status=status.HTTP_400_BAD_REQUEST)
                target_balance = project.targetAmount - project.raisedAmount
                if target_balance < float(params['amount']):
                    return Response({'error': "Cant invest more than expected"}, status=status.HTTP_400_BAD_REQUEST)
                if request.GET.get('walletCheck', False) == "true":
                    # Internal transaction
                    if float(params['amount']) <= balance:
                        trasaction = {}
                        trasaction['lender'] = lender.id
                        trasaction['project'] = params['projectId']
                        trasaction['amount'] = 0
                        trasaction['wallet_money'] = float(params['amount'])
                        trasaction['customer_email'] = lender.email
                        trasaction['payment_id'] = str(
                            randint(1000000, 9999999))
                        trasaction['status'] = "success"
                        trasaction['payment_mode'] = 3
                        trasaction['customer_phone'] = lender.mobile_number
                        trasaction['customer_name'] = lender.first_name
                        trasaction['product_info'] = Project.objects.get(
                            pk=params['projectId']).title
                        trasaction['transactions_type'] = "debit"
                        serializer = LenderDeviabTransactionSerializer(
                            data=trasaction)
                        if serializer.is_valid():
                            lender.wallet.debit(trasaction['wallet_money'])
                            serializer.save()
                            project.raiseAmount(
                                trasaction['wallet_money']).save()
                            got, created = LenderCurrentStatus.objects.get_or_create(
                                lender_id=trasaction['lender'], project_id=trasaction['project'])
                            got.updateCurrentStatus(trasaction['wallet_money'])
                            return Response({'msg': "Succesfully Invested"}, status=status.HTTP_200_OK)
                        else:
                            return Response({'error': "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)

                    else:
                        payU_amount = float(params['amount']) - balance
                        data = {'first_name': lender.first_name,
                                'email': lender.email, 'mobile_number': lender.mobile_number}
                        if not data['first_name'] or not data['email'] and not data['mobile_number']:
                            return Response({'error': "Please provide your profile details "}, status=status.HTTP_400_BAD_REQUEST)

                        txnid = str(randint(1000000, 9999999))
                        hashing = "vz70Zb" + "|" + txnid + "|" + str(payU_amount) + "|" + project.title + "|" + data[
                            'first_name'] + "|" + data['email'] + "|" + str(lender.id) + "|" + params['projectId'] + "|" + str(balance) + "||||||||" + "k1wOOh0b"
                        response = {}
                        response['firstname'] = data['first_name']
                        response['email'] = data['email']
                        response['phone'] = data['mobile_number']
                        response['key'] = "vz70Zb"
                        response['productinfo'] = project.title
                        response['service_provider'] = "payu_paisa"
                        response['hash'] = hashlib.sha512(
                            hashing).hexdigest()
                        response['furl'] = "https://" + \
                            settings.HOST_DOMAIN + "/api/formcapture"
                        response['surl'] = "https://" + \
                            settings.HOST_DOMAIN + "/api/formcapture"
                        response['udf2'] = params['projectId']
                        response['udf1'] = str(lender.id)
                        response['udf3'] = str(balance)
                        response['amount'] = str(payU_amount)
                        response['txnid'] = txnid
                        return Response(response, status=status.HTTP_200_OK)
                else:
                    data = {'first_name': lender.first_name,
                            'email': lender.email, 'mobile_number': lender.mobile_number}
                    if not data['first_name'] or not data['email'] and not data['mobile_number']:
                        return Response({'error': "Please provide your profile details "}, status=status.HTTP_400_BAD_REQUEST)
                    txnid = str(randint(1000000, 9999999))
                    hashing = "vz70Zb" + "|" + txnid + "|" + params['amount'] + "|" + project.title + "|" + data[
                        'first_name'] + "|" + data['email'] + "|" + str(lender.id) + "|" + params['projectId'] + "|" + str(0) + "||||||||" + "k1wOOh0b"
                    response = {}
                    response['firstname'] = data['first_name']
                    response['email'] = data['email']
                    response['phone'] = data['mobile_number']
                    response['key'] = "vz70Zb"
                    response['productinfo'] = project.title
                    response['service_provider'] = "payu_paisa"
                    response['hash'] = hashlib.sha512(hashing).hexdigest()
                    response['furl'] = "https://" + \
                        settings.HOST_DOMAIN + "/api/formcapture"
                    response['surl'] = "https://" + \
                        settings.HOST_DOMAIN + "/api/formcapture"
                    response['udf2'] = params['projectId']
                    response['udf1'] = lender.id
                    response['udf3'] = 0
                    response['amount'] = params['amount']
                    response['txnid'] = txnid
                    return Response(response, status=status.HTTP_200_OK)
        except:
            return Response({'error': "Invalid Transaction"}, status=status.HTTP_400_BAD_REQUEST)


class TransactionFormCapture(APIView):

    @csrf_exempt
    @transaction.atomic
    def post(self, request, format=None):
        params = dict(request.data)
        if params and params['status'][0] == "success":
            trasaction = {}
            trasaction['lender'] = params['udf1'][0]
            trasaction['project'] = params['udf2'][0]
            trasaction['wallet_money'] = float(params['udf3'][0])
            trasaction['amount'] = float(params['amount'][0])
            trasaction['customer_email'] = params['email'][0]
            trasaction['payment_id'] = params['payuMoneyId'][0]
            trasaction['status'] = params['status'][0]
            trasaction['payment_mode'] = 1
            trasaction['customer_phone'] = params['phone'][0]
            trasaction['customer_name'] = params['firstname'][0]
            trasaction['product_info'] = params['productinfo'][0]
            trasaction['transactions_type'] = "debit"
            serializer = LenderDeviabTransactionSerializer(data=trasaction)
            if serializer.is_valid():
                if trasaction['wallet_money']:
                    Lender.objects.get(id=trasaction['lender']).wallet.debit(
                        trasaction['wallet_money'])
                serializer.save()
                combined_amount = trasaction[
                    'wallet_money'] + trasaction['amount']
                Project.objects.get(pk=trasaction['project']).raiseAmount(
                    combined_amount).save()
                got, created = LenderCurrentStatus.objects.get_or_create(
                    lender_id=trasaction['lender'], project_id=trasaction['project'])
                got.updateCurrentStatus(combined_amount)
                return redirect("https://" + settings.CLIENT_DOMAIN + "/#/web/account/latest_transaction")
            else:
                return redirect("https://" + settings.CLIENT_DOMAIN + "/#/web/account/latest_transaction")
        else:
            return redirect("https://" + settings.CLIENT_DOMAIN + "/#/web/account/latest_transaction")


class GetLenderDetail(APIView):

    @token_required
    def get(self, request, format=None):
        try:
            lender = request.token.user.lender
            lenderDetails = {'first_name': lender.first_name, 'last_name': lender.last_name, 'email': lender.email,
                             'mobile_number': lender.mobile_number, 'dob': lender.dob, 'gender': lender.gender}
            return Response(lenderDetails, status=status.HTTP_200_OK)
        except:
            return Response({'error': "Lender not found"}, status=status.HTTP_400_BAD_REQUEST)


class GetLenderProfile(APIView):

    @token_required
    def get(self, request, format=None):
        try:
            lender = request.token.user.lender
            lenderDetails = {'first_name': lender.first_name,
                             'last_name': lender.last_name, 'email': lender.email}
            if request.token.social_token:
                social_type = request.token.social_token.split("social_type=")
                access_token = social_type[0]
                social_type = social_type[1]
                if social_type == "F":
                    facebook = OpenFacebook(access_token)
                    lenderDetails['img_url'] = facebook.my_image_url(
                        size='large')
                elif social_type == "G":
                    from oauth2client.client import AccessTokenCredentials
                    import httplib2
                    from googleapiclient.discovery import build
                    credentials = AccessTokenCredentials(
                        access_token, 'my-user-agent/1.0')
                    http = credentials.authorize(httplib2.Http())
                    service = build("plus", "v1", http=http)
                    people = service.people().get(userId="me").execute()
                    lenderDetails['img_url'] = people['image']['url']
            return Response(lenderDetails, status=status.HTTP_200_OK)
        except:
            return Response({'error': "Lender not found"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateLenderDetails(APIView):

    @token_required
    @transaction.atomic
    def post(self, request, format=None):
        params = request.data
        if params:
            lender = request.token.user.lender
            serializer = LenderSerializer(lender, data=params, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg': "Profile Succesfully Updated"}, status=status.HTTP_200_OK)
            else:
                return Response({'error': "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': "No parameters found"}, status=status.HTTP_400_BAD_REQUEST)


class Register(APIView):

    @transaction.atomic
    def post(self, request, format=None):
        params = request.data
        password = "XYZ"
        uid = params['uid']
        if params['email'] and password and uid:
            invite = Invite.objects.filter(
                email=params['email'], uid=uid, is_verified=False).first()
            if invite:
                invite.is_verified = True
                invite.save()
                user = User.objects.create_user(
                    params['email'], None, password)
                user.is_active = False
                user.save()
                lender = Lender(user=user, email=user.username, gender=params.get('gender', None), dob=params.get('dob', None),
                                first_name=params.get('first_name', None), last_name=params.get('last_name', None), mobile_number=params.get('mobile_number', None))
                lender.save()
                LenderWallet(lender=lender).save()
                sg = sendgrid.SendGridAPIClient(
                    apikey="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")
                data = {
                    "personalizations": [
                        {
                            "to": [
                                {
                                    "email": settings.VERIFIER_EMAIL
                                }
                            ],
                            "substitutions": {
                                "-email-": lender.email,
                                "-link-": "http://" + settings.HOST_DOMAIN + "/api/lender/verify/?lender_id=" + str(lender.id)
                            }
                        }
                    ],
                    "from": {
                        "email": "support@lytyfy.org"
                    },
                    "template_id": "e9eed821-b227-480d-bbe3-a932294a4f22"
                }
                response = sg.client.mail.send.post(request_body=data)
                return Response({'msg': "Sent for verification"}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'CANT ACCESS WITHOUT INVITATION OR ALREADY REGISTERED '}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'error': 'Invalid Data'}, status=status.HTTP_400_BAD_REQUEST)


class GetToken(APIView):

    def post(self, request, format=None):
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        if username is not None and password is not None:
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    token_exist = Token.objects.filter(user=user)
                    if token_exist:
                        token = token_exist.first().token
                        return Response({'token': token}, status=status.HTTP_200_OK)
                    else:
                        Token(user=user).save()
                        new_token = Token.objects.filter(
                            user=user).first().token
                        return Response({'token': new_token}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid User'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Invalid Username/Password'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No Credentials found'}, status=status.HTTP_400_BAD_REQUEST)


class KillToken(APIView):

    @token_required
    def get(self, request):
        request.token.delete()
        return Response({'success': "Succesfully token killed"}, status=status.HTTP_200_OK)


class LenderWithdrawRequest(APIView):

    @token_required
    @transaction.atomic
    def post(self, request, format=None):
        lender = request.token.user.lender
        balance = lender.wallet.balance
        if balance < 1001:
            return Response({'msg': "your balance is less than 1000"}, status=status.HTTP_200_OK)
        pending_request = LenderWithdrawalRequest.objects.filter(
            lender=lender, status=0).values('status')
        if pending_request:
            return Response({'msg': "you still have a pending request"}, status=status.HTTP_200_OK)
        params = request.data
        if params:
            params['amount'] = balance
            params['lender'] = lender.id
            serializer = LenderWithdrawalRequestSerializer(data=params)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg': "Request Send"}, status=status.HTTP_200_OK)
            else:
                return Response({'error': "Invalid Request"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': "No parameters found"}, status=status.HTTP_400_BAD_REQUEST)


class VerifyToken(APIView):

    @token_required
    def get(self, request, format=None):
        lender = request.token.user.lender
        lenderDetails = {'first_name': lender.first_name,
                         'id': lender.id, 'email': lender.email}
        return Response(lenderDetails, status=status.HTTP_200_OK)


class RequestInvite(APIView):

    @transaction.atomic
    def post(self, request, format=None):
        email = request.data.get('email', None)
        if email:
            invite, created = Invite.objects.get_or_create(email=email)
            if created:
                import uuid
                uid = uuid.uuid4().hex
                invite.uid = uid
                invite.save()
                sg = sendgrid.SendGridAPIClient(
                    apikey="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")
                data = {
                    "personalizations": [
                        {
                            "to": [
                                {
                                    "email": email
                                }
                            ],
                            "substitutions": {
                                "-link-": "http://" + settings.CLIENT_DOMAIN + "/#/register?uid=" + uid
                            }
                        }
                    ],
                    "from": {
                        "email": "support@lytyfy.org"
                    },
                    "template_id": "8dfdcd2d-fd68-4b67-9237-2095184817aa"
                }
                response = sg.client.mail.send.post(request_body=data)
                return Response({'msg': "Check your email for registration link"}, status=status.HTTP_200_OK)
            return Response({'msg': "Email already exists"}, status=status.HTTP_200_OK)
        return Response({'error': "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


class ChangePassword(APIView):

    @token_required
    @transaction.atomic
    def post(self, request, format=None):
        lender = request.token.user.lender
        params = request.data
        if params:
            try:
                hash_password = lender.user.password
                flag = check_password(params['old_password'], hash_password)
                if flag:
                    user = lender.user
                    user.set_password(params['new_password'])
                    user.save()
                    return Response({'msg': "Password sucessfully changed"}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': "Wrong old password"}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({'error': "lender not found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


class ListProject(APIView):

    def get(self, request, format=None):
        projects = Project.objects.prefetch_related(
            'lenders').select_related('field_partner').all().order_by('-offlistDate')
        data = []
        for project in projects:
            project_detail = {}
            project_detail['project_id'] = project.id
            project_detail['borrowers'] = project.borrowers.values(
                'first_name', 'last_name', 'avatar')
            project_detail['lenders'] = project.lenders.values(
                'lender_id', 'lender__first_name', 'lender__avatar')
            project_detail['title'] = project.title
            project_detail['loan_raised'] = project.raisedAmount
            project_detail['loan_amount'] = project.targetAmount
            project_detail['place'] = project.place
            project_detail['description'] = project.description
            project_detail['offlistDate'] = project.offlistDate
            project_detail['repayment_term'] = 8
            project_detail['repayment_schedule'] = "Monthly"
            project_detail['field_partner'] = project.field_partner.name
            project_detail[
                'status'] = "running" if project.offlistDate > timezone.now() else "completed"
            data.append(project_detail)
        return Response(data, status=status.HTTP_200_OK)


class ResetPassword(APIView):

    def post(self, request, format=None):
        params = request.data
        if params:
            user = User.objects.filter(username=params['email']).first()
            if user:
                password = User.objects.make_random_password()
                user.set_password(password)
                user.save()
                try:
                    sg = sendgrid.SendGridAPIClient(
                        apikey="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")
                    data = {
                        "personalizations": [
                            {
                                "to": [
                                    {
                                        "email": params['email']
                                    }
                                ],
                                "substitutions":{
                                    "-username-": params['email'],
                                    "-password-":password,
                                    "-first_name-":user.lender.first_name
                                }
                            }
                        ],
                        "from": {
                            "email": "support@lytyfy.org"
                        },
                        "template_id": "e1e8ef81-1ba7-4a11-b266-9e634bba2b1f"
                    }
                    response = sg.client.mail.send.post(request_body=data)
                    return Response({'msg': "New creds sent to your registered email"}, status=status.HTTP_200_OK)
                except:
                    return Response({'error': 'Something went wrong , kindly write us at support@lytyfy.org'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


class RepaymentToInvestors(APIView):

    @transaction.atomic
    def get(self, request, format=None):
        if request.GET.get('amount', None) and request.GET.get('project_id', None):
            amount = float(request.GET.get('amount', None))
            project_id = request.GET.get('project_id', None)
            lenders = LenderCurrentStatus.objects.filter(project=project_id)
            tmr = lenders.aggregate(Sum('emr'))
            for lender in lenders:
                share = round(amount * lender.emr / tmr['emr__sum'], 2)
                trasaction = {}
                trasaction['lender'] = lender.lender.id
                trasaction['project'] = lender.project.id
                trasaction['amount'] = share
                trasaction['payment_id'] = randint(11111111, 99999999)
                trasaction['transactions_type'] = "credit"
                serializer = LenderDeviabTransactionSerializer(data=trasaction)
                if serializer.is_valid():
                    serializer.save()
                    lender.FMI_paid(share)
                    lender.lender.wallet.credit(share)
                else:
                    return Response({'error': "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'msg': "Succesfully wallet credited"}, status=status.HTTP_200_OK)
        return Response({'error': "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


class FBToken(APIView):

    @transaction.atomic
    def post(self, request, format=None):
        access_token = request.data.get('access_token')
        social_type = request.data.get('social_type')
        if access_token and social_type:
            if social_type == "G":
                from oauth2client.client import AccessTokenCredentials
                import httplib2
                from googleapiclient.discovery import build
                credentials = AccessTokenCredentials(
                    access_token, 'my-user-agent/1.0')
                http = credentials.authorize(httplib2.Http())
                service = build("plus", "v1", http=http)
                people = service.people().get(userId="me").execute()
                email = people['emails'][0]['value']
                access_token = access_token + "social_type=G"
            elif social_type == "F":
                access_token = FacebookAuthorization.extend_access_token(
                    access_token).get('access_token')
                facebook = OpenFacebook(access_token)
                resp = facebook.get('me', fields='id,email')
                email = resp['email']
                access_token = access_token + "social_type=F"
            if email:
                user = User.objects.filter(
                    username=email, is_active=True).first()
                if user:
                    token_exist = Token.objects.filter(user=user)
                    if token_exist:
                        first_one = token_exist.first()
                        token = first_one.token
                        first_one.social_token = access_token
                        first_one.save()
                        return Response({'token': token}, status=status.HTTP_200_OK)
                    else:
                        Token(user=user).save()
                        first_one = Token.objects.filter(user=user).first()
                        new_token = first_one.token
                        first_one.social_token = access_token
                        first_one.save()
                        return Response({'token': new_token}, status=status.HTTP_200_OK)
                else:
                    invite, created = Invite.objects.get_or_create(email=email)
                    if created:
                        import uuid
                        uid = uuid.uuid4().hex
                        invite.uid = uid
                        invite.save()
                        sg = sendgrid.SendGridAPIClient(
                            apikey="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")
                        data = {
                            "personalizations": [
                                {
                                    "to": [
                                        {
                                            "email": email
                                        }
                                    ],
                                    "substitutions": {
                                        "-link-": "https://" + settings.CLIENT_DOMAIN + "/#/register?uid=" + uid
                                    }
                                }
                            ],
                            "from": {
                                "email": "support@lytyfy.org"
                            },
                            "template_id": "8dfdcd2d-fd68-4b67-9237-2095184817aa"
                        }
                        response = sg.client.mail.send.post(request_body=data)
                    elif invite.is_verified:
                        return Response({'msg': "Your application is under verification"}, status=status.HTTP_201_CREATED)
                    return Response({'msg': "Check your email for registration link"}, status=status.HTTP_201_CREATED)
            else:
                return Response({'msg': "Update your email in facebook"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'msg': "token not found"}, status=status.HTTP_400_BAD_REQUEST)


class VerifyInvestor(APIView):

    @transaction.atomic
    def get(self, request, format=None):
        lender_id = request.GET.get('lender_id', None)
        if lender_id:
            lender = Lender.objects.filter(id=lender_id).first()
            if lender:
                auth_user = lender.user
                auth_user.is_active = True
                auth_user.save()
                hash_password = auth_user.password
                flag = check_password("XYZ", hash_password)
                if flag:
                    password = User.objects.make_random_password()
                    auth_user.set_password(password)
                    auth_user.save()
                    sg = sendgrid.SendGridAPIClient(
                        apikey="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")
                    data = {
                        "personalizations": [
                            {
                                "to": [
                                    {
                                        "email": lender.email
                                    }
                                ],
                                "substitutions": {
                                    "-user_name-": lender.email,
                                    "-password-": password,
                                    "-first_name-": lender.first_name
                                }
                            }
                        ],
                        "from": {
                            "email": "support@lytyfy.org"
                        },
                        "template_id": "23fc3054-9d34-462f-91a3-830e7d340ace"
                    }
                    response = sg.client.mail.send.post(request_body=data)
                    return Response({'msg': "Investor account sucessfully created"}, status=status.HTTP_200_OK)
            else:
                return Response({'msg': "lender not found"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'msg': "Invalid Request"}, status=status.HTTP_400_BAD_REQUEST)


class GetProject(APIView):

    def get(self, request, project_id, format=None):
        project = Project.objects.select_related(
            'product', 'field_partner').prefetch_related('gallery').get(id=project_id)
        project_detail = {}
        project_detail['project_id'] = project.id
        project_detail['field_partner__name'] = project.field_partner.name
        project_detail[
            'field_partner__description'] = project.field_partner.description
        project_detail['field_partner__avatar'] = project.field_partner.avatar
        project_detail['gallery__image_url'] = project.gallery.values_list(
            'image_url', flat=True)
        project_detail['image_url'] = project.image_url
        project_detail['customer_img'] = project.customer_img
        project_detail['customer_story'] = project.customer_story
        project_detail['borrowers'] = project.borrowers.values(
            'first_name', 'last_name', 'avatar')
        project_detail['lenders'] = project.lenders.values(
            'lender_id', 'lender__first_name', 'lender__avatar')
        project_detail['title'] = project.title
        project_detail['loan_raised'] = project.raisedAmount
        project_detail['loan_amount'] = project.targetAmount
        project_detail['place'] = project.place
        project_detail['description'] = project.description
        project_detail['offlistDate'] = project.offlistDate
        project_detail['repayment_term'] = 8
        project_detail['repayment_schedule'] = "Monthly"
        project_detail[
            'status'] = "running" if project.offlistDate > timezone.now() else "completed"
        return Response(project_detail, status=status.HTTP_200_OK)
