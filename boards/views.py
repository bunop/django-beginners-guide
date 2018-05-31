
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import UpdateView, ListView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import NewTopicForm, PostForm
from .models import Board, Post, Topic


# Create your views here.
class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'home.html'


def board_topics(request, pk):
    board = get_object_or_404(Board, pk=pk)

    # Annotate: generate a new “column” on the fly. This new column will be
    # translated into a property,
    queryset = board.topics.order_by(
        '-last_updated').annotate(
            replies=Count('posts') - 1)

    page = request.GET.get('page', 1)

    paginator = Paginator(queryset, 20)

    try:
        topics = paginator.page(page)

    except PageNotAnInteger:
        # fallback to the first page
        topics = paginator.page(1)

    except EmptyPage:
        # probably the user tried to add a page number
        # in the url, so we fallback to the last page
        topics = paginator.page(paginator.num_pages)

    return render(
        request,
        'topics.html',
        {'board': board, 'topics': topics})


@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)

    if request.method == 'POST':
        form = NewTopicForm(request.POST)

        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            # using authenticated user as topic starter
            topic.starter = request.user
            topic.save()
            Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                # using authenticated user as topic starter
                created_by=request.user
            )
            # TODO: redirect to the created topic page
            return redirect('topic_posts', pk=pk, topic_pk=topic.pk)
    else:
        form = NewTopicForm()

    return render(request, 'new_topic.html', {'board': board, 'form': form})


def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    topic.views += 1
    topic.save()
    return render(request, 'topic_posts.html', {'topic': topic})


@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
    else:
        form = PostForm()

    return render(request, 'reply_topic.html', {'topic': topic, 'form': form})


# dispatch is an internal method Django use (defined inside the View class)
@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    #  will be used to identify the name of the keyword argument used to
    # retrieve the Post object
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        # we are reusing the get_queryset method from the parent class
        queryset = super().get_queryset()
        # we are adding an extra filter to the queryset,
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect(
            'topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)
