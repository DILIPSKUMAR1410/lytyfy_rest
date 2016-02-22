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
from django.conf.urls import url
from django.contrib import admin
from lytyfy_rest import views
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/homepage/$', views.HomePageApi.as_view()),
    url(r'^api/transaction/formdata$', views.TransactionFormData.as_view()),
    url(r'^api/formcapture$', views.TransactionFormCapture.as_view()),
    url(r'^api/lenders/(?P<pk>[0-9]+)$', views.GetLenderDetail.as_view()),
    url(r'^api/lenders/(?P<pk>[0-9]+)/investment$', views.GetLenderInvestmentDetail.as_view()),
    url(r'^api/lenders/(?P<pk>[0-9]+)/update$', views.UpdateLenderDetails.as_view()),
    url(r'^api/lender/register$', views.Register.as_view()),
    url(r'^api/lender/token/new$', views.GetToken.as_view()),
    url(r'^api/lender/token/kill$', views.KillToken.as_view()),
    url(r'^api/lenders/(?P<pk>[0-9]+)/withdraw$', views.LenderWithdrawRequest.as_view()),
    url(r'^api/lender/token/verify$', views.VerifyToken.as_view()),
    # url(r'^api/lenders/(?P<pk>[0-9]+)/changepassword$', views.UserChangePassword.as_view()),
]
