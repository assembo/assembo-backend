from django.urls import include, path
from myproject.myapi import new_functions
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('login/username/', new_functions.login_username),
    path('login/wechat/', new_functions.login_wechat), 
    path('signup/username/', new_functions.signup_username),
    path('signup/wechat/', new_functions.signup_wechat),
    path('invite/accept/', new_functions.invite_accept),
    path('media/update/', new_functions.media_update),
    path('wechat/oa', new_functions.wechat_oa),
    path('user/update/name/', new_functions.user_update_name)
]



