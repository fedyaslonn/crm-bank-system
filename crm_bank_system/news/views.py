from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, View, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from .models import News, UserReaction, Comment
from .forms import NewsForm

from django.contrib import messages

from django.db.models import Q, Count


class NewsListView(ListView):
    model = News
    template_name = 'customer/news_list.html'
    context_object_name = 'news_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        sort_order = self.request.GET.get('sort', '')

        if search_query:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))

        if sort_order == 'asc':
            queryset = queryset.order_by('title')
        elif sort_order == 'desc':
            queryset = queryset.order_by('-title')
        elif sort_order == 'likes_desc':
            queryset = queryset.annotate(annotated_likes_count=Count('reactions', filter=Q(reactions__is_like=True))).order_by('-annotated_likes_count')
        elif sort_order == 'likes_asc':
            queryset = queryset.annotate(annotated_likes_count=Count('reactions', filter=Q(reactions__is_like=True))).order_by('annotated_likes_count')
        elif sort_order == 'dislikes_desc':
            queryset = queryset.annotate(annotated_dislikes_count=Count('reactions', filter=Q(reactions__is_like=False))).order_by('-annotated_dislikes_count')
        elif sort_order == 'dislike_asc':
            queryset = queryset.annotate(annotated_dislikes_count=Count('reactions', filter=Q(reactions__is_like=False))).order_by('annotated_dislikes_count')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        for news in context['news_list']:
            if user.is_authenticated:
                reaction = news.reactions.filter(user=user).first()
                news.is_liked = reaction.is_like if reaction else False
                news.is_disliked = not reaction.is_like if reaction else False
            else:
                news.is_liked = False
                news.is_disliked = False

        return context


class ReactToNewsView(View):
    def post(self, request, pk, action):
        news = get_object_or_404(News, pk=pk)
        is_like = action == 'like'
        user = request.user

        with transaction.atomic():
            reaction, created = UserReaction.objects.get_or_create(user=user, news=news)

            # Удаление реакции, если она такая же, как текущая
            if not created and reaction.is_like == is_like:
                reaction.delete()
            else:
                reaction.is_like = is_like
                reaction.save()

            # Обновляем лайки/дизлайки в базе данных
            news.likes_count = news.reactions.filter(is_like=True).count()
            news.dislikes_count = news.reactions.filter(is_like=False).count()
            news.save()  # Сохраняем изменения

            return JsonResponse({
                'likes_count': news.likes_count,
                'dislikes_count': news.dislikes_count,
                'is_liked': is_like,
                'is_disliked': not is_like if not created else False,
            })


@method_decorator(login_required, name='dispatch')
class NewsCreateView(CreateView):
    model = News
    form_class = NewsForm
    template_name = 'customer/add_news.html'
    success_url = reverse_lazy('news_list')

    def form_valid(self, form):
        form.instance.authors = self.request.user
        return super().form_valid(form)

class NewsDetailView(View, LoginRequiredMixin):
    def get(self, request, news_id):
        news = get_object_or_404(News, pk=news_id)
        user = request.user

        reaction = UserReaction.objects.filter(user=user, news=news).first()
        is_liked = reaction.is_like if reaction else False
        is_disliked = not reaction.is_like if reaction else False

        context = {
            'news': news,
            'is_liked': is_liked,
            'is_disliked': is_disliked,
        }
        return render(request, 'customer/news_detail.html', context)


class AddCommentView(View):
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        content = request.POST.get('content')

        if content:
            Comment.objects.create(
                news=news,
                user=request.user,
                content=content,
            )
            messages.success(request, "Комментарий добавлен!")
        else:
            messages.error(request, "Комментарий не может быть пустым.")

        return redirect('news_detail', news_id=news.id)


class NewsUpdateView(UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'customer/news_form.html'
    success_url = reverse_lazy('news_list')

    def dispatch(self, request, *args, **kwargs):
        """Проверка доступа: только автор или администратор может редактировать новость."""
        news = self.get_object()  # Получаем объект новости
        if request.user != news.authors and not request.user.is_superuser:
            return HttpResponseForbidden("У вас нет прав для редактирования этой новости.")
        return super().dispatch(request, *args, **kwargs)


class NewsDeleteView(View, LoginRequiredMixin):
    def get(self, request, pk):
        object = News.objects.get(pk=pk)
        return render(request, "customer/news_confirm_delete.html", {"object": object})

    def post(self, request, pk):
        news = News.objects.filter(id=pk)
        news.delete()
        return HttpResponseRedirect(reverse_lazy("news_list"))