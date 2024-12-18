from django.urls import path
from .views import *

urlpatterns = [
    path("", FriendsListView.as_view(), name="friends_list"),
    path('search/', search_friends, name='search_friends'),
    path('send_friend_request/', send_friend_request, name='send_friend_request'),
    path('my_friends/', my_friends, name='my_friends'),
    path('my_friends_requests/', my_friendship_requests, name='my_friends_requests'),
    path('incoming_friend_requests/', incoming_friend_requests, name='incoming_friend_requests'),
    path('accept_friend_request/<int:friendship_id>/', accept_friend_request, name='accept_friend_request'),
    path('reject_friend_request/<int:friendship_id>/', reject_friend_request, name='reject_friend_request'),
    path('remove_friend/<int:friend_id>/', remove_friend, name='remove_friend'),
    path('friends_news/', FriendsNewsListView.as_view(), name='friends_news')
]
