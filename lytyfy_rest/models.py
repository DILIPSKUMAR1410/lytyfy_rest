from django.db import models
from django.contrib.auth.models import User
import binascii
import os
from django.utils import timezone

class Lender(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30,null=True)
    mobile_number = models.CharField(max_length=13,null=True)
    email = models.CharField(max_length=30,null=True)
    user=models.OneToOneField(User,related_name='lender')
    avatar=models.CharField(max_length=30,null=True)

class LenderWallet(models.Model):
    lender=models.OneToOneField(Lender)
    balance=models.FloatField(default=0)

class LenderWithdrawalRequest(models.Model):
    STATUS_CHOICES=((0,'Processing'),
                    (1,'Completed'),
                    (2,'Pending'))
    lender=models.ForeignKey(Lender)
    amount=models.FloatField(default=0)
    requested_at=models.DateTimeField(default=timezone.now())
    account_number=models.CharField(max_length=30)
    ifsc_code=models.CharField(max_length=30)
    account_name = models.CharField(max_length=30)
    bank_name = models.CharField(max_length=30)
    status = models.IntegerField(choices=STATUS_CHOICES,default=0)
    

class Project(models.Model):
    title=models.CharField(max_length=30)
    raisedAmount=models.FloatField(default=0)
    targetAmount=models.FloatField(default=0)
    place=models.CharField(max_length=30)
    description=models.TextField()
    enlistDate=models.DateTimeField(default=timezone.now())
    offlistDate=models.DateTimeField()
    
    def raiseAmount(self,amount=None):
        self.raisedAmount+=amount
        return self


class LenderDeviabTransaction(models.Model):
    PAYMENT_CHOICES=((0,'CC'),
                    (1,'DC'),
                    (2,'NB'))
    lender=models.ForeignKey(Lender)
    project= models.ForeignKey(Project)
    timestamp=models.DateTimeField(default=timezone.now())
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
    created = models.DateTimeField(default=timezone.now())

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


class LenderCurrentStatus(models.Model):
    lender=models.ForeignKey(Lender) 
    principal_repaid=models.FloatField(default=0)
    interest_repaid=models.FloatField(default=0)
    principal_left=models.FloatField(default=0)
    interest_left=models.FloatField(default=0)
    tenure_left=models.FloatField(default=8)
    emr=models.FloatField(default=0)
    project=models.ForeignKey(Project,related_name="lenders")

    def updateCurrentStatus(self,amount):
        self.principal_left+=amount
        il= amount *.6 / 100
        self.interest_left+=il
        self.emr=self.principal_left / self.tenure_left + self.interest_left;
        return self

class Borrower(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30,null=True)
    mobile_number = models.CharField(max_length=13,null=True)
    avatar=models.CharField(max_length=30,null=True)
    project=models.ForeignKey(Project,related_name="borrowers",null=True)