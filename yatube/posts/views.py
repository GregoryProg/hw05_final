from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentFrom, PostForm
from .models import Follow, Group, Post, User
from .utils import the_paginator


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group', 'author')
    context = {
        'page_obj': the_paginator(posts, request),
        'index': True
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    context = {
        'group': group,
        'page_obj': the_paginator(posts, request)
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group', 'author')
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author__username=username).exists()
    context = {
        'author': author,
        'page_obj': the_paginator(posts, request),
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related('group', 'author'),
                             pk=post_id)
    form = CommentFrom(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, template, {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'post': post,
        'form': form,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentFrom(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': the_paginator(posts, request),
        'follow': True
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    follow_user = get_object_or_404(User, username=username)
    if request.user != follow_user:
        Follow.objects.get_or_create(user=request.user, author=follow_user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    unfollow_user = get_object_or_404(User, username=username)
    get_object_or_404(
        Follow,
        user=request.user,
        author=unfollow_user
    ).delete()
    return redirect('posts:profile', username=username)
