from django.db import models
from django.contrib.auth.models import User
import binascii
import os
from django.utils import timezone
from s3direct.fields import S3DirectField

class Lender(models.Model):

    GENDER_CHOICES=((0,'Male'),
                    (1,'Female'),
                    (2,'Other'))
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30,null=True)
    mobile_number = models.CharField(max_length=13,null=True)
    email = models.CharField(max_length=30,null=True)
    user=models.OneToOneField(User,related_name='lender')
    avatar=models.CharField(max_length=30,null=True)
    gender = models.IntegerField(choices=GENDER_CHOICES,null=True)
    dob = models.CharField(max_length=30,null=True)

class LenderWallet(models.Model):
    balance=models.FloatField(default=0.0)
    lender=models.OneToOneField(Lender,related_name="wallet")
    
    def credit(self,amount):
        self.balance += amount
        self.save()


class LenderWithdrawalRequest(models.Model):
    STATUS_CHOICES=((0,'Processing'),
                    (1,'Completed'),
                    (2,'Pending'))
    lender=models.ForeignKey(Lender)
    amount=models.FloatField(default=0.0)
    requested_at=models.DateTimeField(default=timezone.now())
    account_number=models.CharField(max_length=30)
    ifsc_code=models.CharField(max_length=30)
    account_name = models.CharField(max_length=30)
    bank_name = models.CharField(max_length=30)
    status = models.IntegerField(choices=STATUS_CHOICES,default=0)
    

class Project(models.Model):
    title=models.CharField(max_length=30)
    raisedAmount=models.FloatField(default=0.0)
    targetAmount=models.FloatField(default=0.0)
    place=models.CharField(max_length=30)
    description=models.TextField()
    enlistDate=models.DateTimeField(default=timezone.now())
    offlistDate=models.DateTimeField()
    
    def raiseAmount(self,amount=None):
        self.raisedAmount+=amount
        return self

    def __unicode__(self):
       return self.title


class LenderDeviabTransaction(models.Model):
    PAYMENT_CHOICES=((0,'CC'),
                    (1,'DC'),
                    (2,'NB'))
    lender=models.ForeignKey(Lender,related_name="lender_transactions")
    project= models.ForeignKey(Project,related_name="project_transactions")
    timestamp=models.DateTimeField(default=timezone.now())
    amount=models.FloatField(default=0.0)
    payment_id=models.IntegerField(default=0)
    status=models.CharField(max_length=30,null=True)
    payment_mode=models.IntegerField(choices=PAYMENT_CHOICES,null=True)
    customer_email=models.CharField(max_length=30,null=True)
    customer_phone=models.CharField(max_length=30,null=True)
    customer_name=models.CharField(max_length=30,null=True)
    product_info=models.CharField(max_length=30,null=True)
    additional_charges=models.FloatField(default=0.0,null=True)
    split_info=models.CharField(max_length=255,null=True)
    error_message=models.CharField(max_length=30,null=True)
    notification=models.CharField(max_length=30,null=True)
    transactions_type=models.CharField(max_length=30)

    def __unicode__(self):
       return str(self.payment_id)

class Token(models.Model):
    user = models.ForeignKey(User)
    token = models.CharField(max_length=40, primary_key=True)
    created = models.DateTimeField(default=timezone.now())
    social_token = models.TextField(null=True) 

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
    uid = models.CharField(max_length=32,null=True)
    is_verified = models.BooleanField(default=False)
    def __unicode__(self):
       return self.email

class LenderCurrentStatus(models.Model):
    lender=models.ForeignKey(Lender,related_name="projects") 
    principal_repaid=models.FloatField(default=0.0)
    interest_repaid=models.FloatField(default=0.0)
    principal_left=models.FloatField(default=0.0)
    interest_left=models.FloatField(default=0.0)
    emr=models.FloatField(default=0.0)
    tenure_left=models.IntegerField(default=8)
    project=models.ForeignKey(Project,related_name="lenders")

    def updateCurrentStatus(self,amount):
        self.principal_left+=amount
        il= amount *.6 / 100
        self.interest_left+=il
        self.emr=self.principal_left / self.tenure_left + self.interest_left

        #remove after floating issue resolved
        self.interest_left = round(self.interest_left,2)
        self.emr = round(self.emr,2)
        self.principal_left = round(self.principal_left,2)
        
        self.save()
        return self

    def FMI_paid(self,amount):
        if amount < self.interest_left:
            self.interest_left -= amount 
            self.interest_left +=  self.principal_left *.6 / 100  
            self.interest_repaid += amount
            self.tenure_left -= 1
            self.emr = self.principal_left / self.tenure_left + self.interest_left

            #remove after floating issue resolved
            self.interest_left = round(self.interest_left,2)
            self.interest_repaid = round(self.interest_repaid,2)
            self.emr = round(self.emr,2)

            self.save()
        else:
            self.principal_left -= (amount - self.interest_left)
            self.interest_repaid += self.interest_left
            self.principal_repaid += (amount - self.interest_left)
            self.interest_left = self.principal_left *.6 / 100  
            self.tenure_left -= 1
            self.emr = self.principal_left / self.tenure_left + self.interest_left

            #remove after floating issue resolved
            self.interest_left = round(self.interest_left,2)
            self.interest_repaid = round(self.interest_repaid,2)
            self.emr = round(self.emr,2)
            self.principal_left = round(self.principal_left,2)
            self.principal_repaid = round(self.principal_repaid,2)
            
            self.save()


class Borrower(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30,null=True)
    mobile_number = models.CharField(max_length=13,null=True,blank=True)
    avatar= S3DirectField(dest='borrower_img',max_length=64,null=True,blank=True)
    project=models.ForeignKey(Project,related_name="borrowers",null=True,)

    def __unicode__(self):
       return self.first_name + " " +self.last_name