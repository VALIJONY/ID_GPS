from django.urls import path
from .views import Loginview,Home,LogoutView, MultiMonthBugalteriyaCreateView, MultiMonthBugalteriyaUpdateView, RasxodAddView, RasxodDeleteView, RasxodUpdateView,SkladView,SkladAddView,sklad_list,SotishListView,SotishAddView,SotishUpdateView,SotishDeleteView,RasxodListView,MijozlarView,BugalteriyaTableView

urlpatterns = [
   path('',Loginview.as_view(),name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
   path('home/',Home.as_view(),name='home'),
   path('sklad/',SkladView.as_view(),name='sklad-list'),
   path('sklad/add/',SkladAddView.as_view(),name="skladadd"),
   path('sklad-filter/',sklad_list,name='filter-sklad'),
   path('sotuv/',SotishListView.as_view(),name='sotish_list'),
   path('sotish/add/',SotishAddView.as_view(),name='sotish_add'),
    path('sotish/update/<int:pk>/', SotishUpdateView.as_view(), name='sotish_update'),
    path('sotish/delete/<int:pk>/', SotishDeleteView.as_view(), name='sotish_delete'),
    path('rasxod/', RasxodListView.as_view(), name='rasxod_list'),
    path('rasxod/add/', RasxodAddView.as_view(), name='rasxod_add'),
    path('rasxod/update/<int:pk>/', RasxodUpdateView.as_view(), name='rasxod_update'),
    path('rasxod/delete/<int:pk>/', RasxodDeleteView.as_view(), name='rasxod_delete'),
    path('mijozlar/',MijozlarView.as_view(),name='mijozlar'),
    path('bugalteriya/',BugalteriyaTableView.as_view(),name='bugalteriya'),
    path('bugalteriya/create/', MultiMonthBugalteriyaCreateView.as_view(), name='bugalteriyacreate'),
    path('bugalteriya/update/',MultiMonthBugalteriyaUpdateView.as_view(),name='bagalteriya_update')
]