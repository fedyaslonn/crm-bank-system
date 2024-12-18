from django.urls import path
from .views import *
from friendship.views import MyNewsListView


urlpatterns = [
    path('news_list/', NewsListView.as_view(), name='news_list'),
    path('news/add/', NewsCreateView.as_view(), name='add_news'),
    path('<int:pk>/<str:action>/', ReactToNewsView.as_view(), name='news_react'),
    path('news_detail/<int:news_id>/', NewsDetailView.as_view(), name='news_detail'),
    path('my_news_list/', MyNewsListView.as_view(), name='my_news_list'),
    path('<int:news_id>/add_comment/', AddCommentView.as_view(), name='add_comment'),
    path('news/<int:pk>/edit/', NewsUpdateView.as_view(), name='edit_news'),
    path('news/<int:pk>/delete/', NewsDeleteView.as_view(), name='delete_news'),
    path('news/<int:pk>/add_comment/', AddCommentView.as_view(), name='add_comment'),
]
