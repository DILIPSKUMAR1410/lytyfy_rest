from rest_framework.response import Response
from rest_framework import status
from lytyfy_rest.models import Token
from django.conf import settings

def token_required(func):
    def inner(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)
        if auth_header is not None:
            tokens = auth_header.split(' ')
            if len(tokens) == 2 and tokens[0] == 'Token':
                token = tokens[1]
                try:
                    request.token = Token.objects.get(token=token)
                    return func(self, request)
                except Token.DoesNotExist:
                    return Response({'error': 'Token not found'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'error': 'Invalid Header'}, status=status.HTTP_401_UNAUTHORIZED)
    return inner


def getFormDataForPayU(lender,project,payu_amount,wallet_money):
    data = {'first_name': lender.first_name,
            'email': lender.email, 'mobile_number': lender.mobile_number}
    if not data['first_name'] or not data['email'] and not data['mobile_number']:
        return False
    txnid = str(randint(1000000, 9999999))
    hashing = "vz70Zb" + "|" + txnid + "|" + payu_amount + "|" + project.title + "|" + data[
        'first_name'] + "|" + data['email'] + "|" + str(lender.id) + "|" + project.id + "|" + wallet_money + "||||||||" + "k1wOOh0b"
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
    response['udf2'] = project.id
    response['udf1'] = lender.id
    response['udf3'] = wallet_money
    response['amount'] = payu_amount
    response['txnid'] = txnid
    return response