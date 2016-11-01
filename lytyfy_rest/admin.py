from django.contrib import admin
from lytyfy_rest.models import LenderDeviabTransaction, Project, Lender,\
    LenderCurrentStatus, LenderWallet, Token, LenderWithdrawalRequest, \
    Invite, Borrower, Product, FieldPartner, ProjectGallery, FieldRep, BorrowerLoanDetails, \
    FRBorrowerMap, LoanTerm, LoanStatus

admin.site.register(Project)
admin.site.register(Invite)
admin.site.register(Borrower)
admin.site.register(LenderDeviabTransaction)
admin.site.register(Product)
admin.site.register(FieldPartner)
admin.site.register(ProjectGallery)
admin.site.register(LenderWithdrawalRequest)
admin.site.register(FieldRep)
admin.site.register(BorrowerLoanDetails)
admin.site.register(FRBorrowerMap)
admin.site.register(LoanTerm)
admin.site.register(LoanStatus)
admin.site.register(LenderCurrentStatus)
