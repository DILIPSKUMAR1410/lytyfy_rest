"""lytyfy_rest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from lytyfy_rest import views
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^s3direct/', include('s3direct.urls')),
    url(r'^api/homepage/$', views.HomePageApi.as_view()),
    url(r'^api/transaction/formdata$', views.TransactionFormData.as_view()),
    url(r'^api/formcapture$', views.TransactionFormCapture.as_view()),
    url(r'^api/lender$', views.GetLenderDetail.as_view()),
    url(r'^api/lender/profile$', views.GetLenderProfile.as_view()),
    url(r'^api/lender/update$', views.UpdateLenderDetails.as_view()),
    url(r'^api/lender/register$', views.Register.as_view()),
    url(r'^api/lender/portfolio$', views.LenderPortfolio.as_view()),
    url(r'^api/lender/token/new$', views.GetToken.as_view()),
    url(r'^api/lender/token/kill$', views.KillToken.as_view()),
    url(r'^api/lender/withdraw$', views.LenderWithdrawRequest.as_view()),
    url(r'^api/lender/token/verify$', views.VerifyToken.as_view()),
    url(r'^api/requestinvite$', views.RequestInvite.as_view()),
    url(r'^api/lender/changepassword$', views.ChangePassword.as_view()),
    url(r'^api/projects/$', views.ListProject.as_view()),
    url(r'^api/resetpassword/$', views.ResetPassword.as_view()),
    url(r'^api/repayment/$', views.RepaymentToInvestors.as_view()),
    url(r'^api/FBToken/$', views.FBToken.as_view()),
    url(r'^api/lender/verify/$', views.VerifyInvestor.as_view()),
    url(r'^api/lender/dashboard$', views.DashBoardApi.as_view()),
    url(r'^api/lender/wallet/transactions$',
        views.WalletTransactions.as_view()),
    url(r'^api/projects/(?P<project_id>\d+)$',
        views.GetProject.as_view()),

]
