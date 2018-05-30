
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from .forms import NewTopicForm
from .models import Board, Post


# Create your views here.
def home(request):
    boards = Board.objects.all()
    return render(request, 'home.html', {'boards': boards})


def board_topics(request, pk):
    board = get_object_or_404(Board, pk=pk)
    return render(request, 'topics.html', {'board': board})


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
            return redirect('board_topics', pk=board.pk)
    else:
        form = NewTopicForm()

    return render(request, 'new_topic.html', {'board': board, 'form': form})
