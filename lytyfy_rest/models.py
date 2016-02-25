from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import binascii
import os

class Lender(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    mobile_number = models.CharField(max_length=13,null=True)
    email = models.CharField(max_length=30,null=True)
    user=models.OneToOneField(User,related_name='lender')
    
class LenderCurrentStatus(models.Model):
    lender=models.OneToOneField(Lender) 
    principal_repaid=models.FloatField(default=0)
    interest_repaid=models.FloatField(default=0)
    principal_left=models.FloatField(default=0)
    interest_left=models.FloatField(default=0)
    tenure_left=models.FloatField(default=0)
    emr=models.FloatField(default=0)

class LenderWallet(models.Model):
    lender=models.OneToOneField(Lender)
    balance=models.FloatField(default=0)

class LenderWithdrawalRequest(models.Model):
    STATUS_CHOICES=((0,'Processing'),
                    (1,'Completed'),
                    (2,'Pending'))
    lender=models.ForeignKey(Lender)
    amount=models.FloatField(default=0)
    requested_at=models.DateTimeField(auto_now=True)
    account_number=models.CharField(max_length=30)
    ifsc_code=models.CharField(max_length=30)
    account_name = models.CharField(max_length=30)
    bank_name = models.CharField(max_length=30)
    status = models.IntegerField(choices=STATUS_CHOICES,default=0)
    

class Project(models.Model):
    capitalAmount=models.FloatField(default=0)
    def creditCapitalAmount(self,amount=None):
        self.capitalAmount+=amount
        return self.capitalAmount


class LenderDeviabTransaction(models.Model):
    PAYMENT_CHOICES=((0,'CC'),
                    (1,'DC'),
                    (2,'NB'))
    lender=models.ForeignKey(Lender)
    project= models.ForeignKey(Project)
    timestamp=models.DateTimeField(auto_now=True)
    amount=models.FloatField(default=0)
    payment_id=models.FloatField(default=0)
    status=models.CharField(max_length=30)
    payment_mode=models.IntegerField(choices=PAYMENT_CHOICES)
    customer_email=models.CharField(max_length=30)
    customer_phone=models.CharField(max_length=30)
    customer_name=models.CharField(max_length=30)
    product_info=models.CharField(max_length=30,null=True)
    additional_charges=models.FloatField(default=0,null=True)
    split_info=models.CharField(max_length=255,null=True)
    error_message=models.CharField(max_length=30,null=True)
    notification=models.CharField(max_length=30,null=True)


class Token(models.Model):
    user = models.ForeignKey(User)
    token = models.CharField(max_length=40, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        return super(Token, self).save(*args, **kwargs)

    def generate_token(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __unicode__(self):
        return self.token


class Invite(models.Model):
    email = models.CharField(max_length=30)