from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View, ListView
from dulwich.porcelain import status
from urllib3 import request

from .models import Friendship
from users.models import CustomUser

import logging

from news.models import News
from news.models import UserReaction

logger = logging.getLogger(__name__)


# Create your views here.

class FriendsListView(LoginRequiredMixin, View):
    template_name = "customer/friends_list.html"

    def get(self, request, *args, **kwargs):
        search_query = request.GET.get("search", "").strip()

        user = request.user

        friends = Friendship.objects.filter(
            Q(user_from=user) | Q(user_to=user),
            status="ACCEPTED"
        ).select_related("user_from", "user_to")

        if search_query:
            friends = friends.filter(
                Q(user_from__username__icontains=search_query) |
                Q(user_to__username__icontains=search_query)
            )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return render(request, "friends_list.html", {"friends": friends})

        # Обычная загрузка страницы
        return render(request, self.template_name, {"friends": friends})

def search_friends(request):
    query = request.GET.get('query', '')
    users = CustomUser.objects.filter(Q(username__icontains=query) | Q(email__icontains=query)).exclude(id=request.user.id)

    sent_requests = Friendship.objects.filter(
        user_from=request.user,
        status='PENDING'
    ).values_list('user_to_id', flat=True)

    # Если обычный запрос, возвращаем HTML-шаблон
    return render(request, 'customer/search_friends.html',
                  {'users': users,
                   'sent_requests': set(sent_requests)})

def send_friend_request(request):
    if request.method == 'POST':
        user_to_id = request.POST.get('user_to_id')
        if not user_to_id:
            return JsonResponse({'status': 'error', 'message': 'User ID not provided'})

        try:
            user_to = CustomUser.objects.get(id=user_to_id)
            with transaction.atomic():
                Friendship.objects.create(
                    user_from=request.user,
                    user_to=user_to,
                    status='PENDING'
                )
            return redirect('search_friends')
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def my_friends(request):
    search_query = request.GET.get('search', '')

    friendships = Friendship.objects.filter(
        (Q(user_from=request.user) | Q(user_to=request.user)),
        status="ACCEPTED"
    )

    friends = []

    for friendship in friendships:
        if friendship.user_from == request.user:
            friends.append(friendship.user_to)
        else:
            friends.append(friendship.user_from)

    if search_query:
        friends = [friend for friend in friends if search_query.lower() in friend.username.lower() or search_query.lower() in friend.email.lower()]

    return render(request, 'customer/my_friends.html', {'friends': friends, 'search_query': search_query})


def my_friendship_requests(request):
    friendships = Friendship.objects.filter(
        user_from=request.user,
        status="PENDING"
    )

    return render(request, 'customer/my_friends_requests.html', {'friendships': friendships})

def incoming_friend_requests(request):
    friendships = Friendship.objects.filter(
        user_to=request.user,
        status="PENDING"
    )

    return render(request, 'customer/incoming_friends_requests.html', {'friendships': friendships})

def accept_friend_request(request, friendship_id):
    if request.method == 'POST':
        try:
            friendship = Friendship.objects.get(id=friendship_id)
            if friendship.user_to == request.user and friendship.status == 'PENDING':
                friendship.status = 'ACCEPTED'
                friendship.save()
                return redirect('incoming_friend_requests')
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid friendship request'})
        except Friendship.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Friendship request not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def reject_friend_request(request, friendship_id):
    if request.method == 'POST':
        try:
            friendship = Friendship.objects.get(id=friendship_id)
            if friendship.user_to == request.user and friendship.status == 'PENDING':
                friendship.status = 'REJECTED'
                friendship.save()
                return redirect('incoming_friend_requests')
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid friendship request'})
        except Friendship.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Friendship request not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def remove_friend(request, friend_id):
    if request.method == 'POST':
        try:
            friendship = Friendship.objects.get(
                (Q(user_from=request.user, user_to_id=friend_id) | Q(user_to=request.user, user_from_id=friend_id)),
                status='ACCEPTED'
            )
            friendship.status = 'PENDING'
            friendship.save()
            return redirect('my_friends')
        except Friendship.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Friendship not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


class FriendsNewsListView(LoginRequiredMixin, View):
    def get(self, request):
        friends_ids = Friendship.objects.filter(
            Q(user_from=request.user) | Q(user_to=request.user),
            status='ACCEPTED'
        ).values_list('user_to_id', flat=True)

        news_queryset = (News.objects.filter(
            authors_id__in=friends_ids).
                select_related('authors')
                .prefetch_related(
            Prefetch(
                'reactions',
                queryset=UserReaction.objects.filter(user=request.user),
                to_attr='user_reactions'
            )
        ).exclude(authors_id=request.user.id).order_by("-created_at"))

        search_query = request.GET.get('search', '')
        if search_query:
            news = news_queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        sort_order = request.GET.get('sort', '')
        if sort_order == 'asc':
            news_queryset = news_queryset.order_by('title')
        elif sort_order == 'desc':
            news_queryset = news_queryset.order_by('-title')

        for news in news_queryset:
            reaction = news.user_reactions[0] if news.user_reactions else None
            news.is_liked = reaction.is_like if reaction else False
            news.is_disliked = not reaction.is_like if reaction else False

        context = {
            'news_list': news_queryset,
            'active_tab': 'friends',
            'request': request,
        }

        return render(request, 'customer/news_list.html', context)


class MyNewsListView(LoginRequiredMixin, View):
    def get(self, request):
        news_queryset = News.objects.filter(
            authors_id=request.user.id
        ).select_related('authors').prefetch_related(
            Prefetch(
                'reactions',
                queryset=UserReaction.objects.filter(user=request.user),
                to_attr='user_reactions'
            )
        )

        search_query = request.GET.get('search', '')
        if search_query:
            news_queryset = news_queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        sort_order = request.GET.get('sort', '')
        if sort_order == 'asc':
            news_queryset = news_queryset.order_by('title')
        elif sort_order == 'desc':
            news_queryset = news_queryset.order_by('-title')

        for news in news_queryset:
            reaction = news.user_reactions[0] if news.user_reactions else None
            news.is_liked = reaction.is_like if reaction else False
            news.is_disliked = not reaction.is_like if reaction else False

        context = {
            'news_list': news_queryset,
            'request': request
        }

        return render(request, 'customer/news_list.html', context)
