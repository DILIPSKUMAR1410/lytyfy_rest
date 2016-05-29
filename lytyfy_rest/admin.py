from django.contrib import admin
from lytyfy_rest.models import LenderDeviabTransaction,Project,Lender,LenderCurrentStatus,LenderWallet,Token,LenderWithdrawalRequest,Invite,Borrower

admin.site.register(Project)
admin.site.register(Invite)
admin.site.register(Borrower)
