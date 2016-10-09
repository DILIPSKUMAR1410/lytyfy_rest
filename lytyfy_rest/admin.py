from django.contrib import admin
from lytyfy_rest.models import LenderDeviabTransaction, Project, Lender,\
    LenderCurrentStatus, LenderWallet, Token, LenderWithdrawalRequest, \
    Invite, Borrower, Product, FieldPartner, ProjectGallery

admin.site.register(Project)
admin.site.register(Invite)
admin.site.register(Borrower)
admin.site.register(LenderDeviabTransaction)
admin.site.register(Product)
admin.site.register(FieldPartner)
admin.site.register(ProjectGallery)
