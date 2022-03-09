"""myproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from myproject.myapi import views
from myproject.myapi import multi_cards
from myproject.myapi import users
from myproject.myapi import models
from rest_framework import routers

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

# for nginx -> use below

urlpatterns = [
    path('', TemplateView.as_view(template_name="application.html"),name="app"),
    path('user/<user_id>/config/', views.get_configuration),
    path('user/<user_id>/tasks/', views.get_user_tasks),
    path('task/<task_id>/cards/', views.get_task_cards),
    path('user/<user_id>/cards/', views.get_user_cards),
    path('user/<user_id>/get/', views.get_user),
    path('admin/', admin.site.urls),
    #path('api/v1/users/', include('users.urls')),

    path('accounts/', include('django.contrib.auth.urls')), # new
    path('task/', views.run_script),
    path('task/create/', views.create_task),
    path('task/<task_id>/update/', views.update_task),
    path('task/<task_id>/delete/', views.delete_task),
    path('task/<task_id>/collaborators/', views.get_task_collaborators),
    path('card/create/', views.create_card),
    path('card/<card_id>/update/', views.update_card),
    path('card/<card_id>/update_card_taskid/', views.update_card_taskid),
    path('card/<card_id>/delete/', views.delete_card),
    path('card/<card_id>/read/', views.mark_card_as_read),

    # multiple card path
    path('cards/change_task/', multi_cards.select_task),
    path('cards/delete/', multi_cards.delete_cards),
    # summary path
    path('summarize/', views.summarize),

    #added
    path('user/create/', users.create_user),
    path('user/login/', users.login_user),
    path('user/update/username/', users.update_username),
    path('task/invite/', views.task_invite),
    path('task/invite/exist/', views.task_invite_exist),
    path('auth/cookies/', users.auth_cookies),
    path('wechat/login/', users.wechat_login),
    path('wechat/oa', users.wechat_oa),
    path('wechat/user/create/', users.wechat_user_create),
    path('wechat/mobile/signup/', users.wechat_mobile_signup),
    path('media/upload/task/', users.media_upload_task),
    path('media/upload/card/', users.media_upload_card),
    path('media/delete/task/', users.media_delete_task),
    path('media/delete/card/', users.media_delete_card),
    path('subscribe/<email>/', users.creating_subscription),
    path('survey/<email>/', users.submit_survey)
]



