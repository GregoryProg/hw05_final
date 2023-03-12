from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post, User


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='User')
        cls.follower = User.objects.create(username='Follower')
        cls.no_follower = User.objects.create(username='NoFollower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(PostPagesTest.follower)
        self.authorized_client_no_follower = Client()
        self.authorized_client_no_follower.force_login(
            PostPagesTest.no_follower
        )

    def check_post(self, response, is_page):
        if is_page:
            page_obj = response.context.get('page_obj')
            self.assertIsInstance(page_obj, Page)
            post = page_obj[0]
        else:
            post = response.context.get('post')
        self.assertIsInstance(post, Post)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.group.id, self.group.id)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_post(response, is_page=True)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:group_posts',
                    kwargs={'slug': self.group.slug}
                )
            )
        )
        self.assertEqual(response.context.get('group'), self.group)
        self.check_post(response, is_page=True)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.post.author}
                )
            )
        )
        self.assertEqual(response.context.get('author'), self.post.author)
        self.check_post(response, is_page=True)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.check_post(response, is_page=False)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        self.check_post(response, is_page=False)
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание поста на страницах с выбранной группой"""
        test_group = Group.objects.create(
            title='Вторая тестовая группа',
            slug='test-slug-2',
            description='Второе тестовое описание',
        )
        test_post = Post.objects.create(
            text='Проверка создания поста на страницах с выбранной группой',
            author=self.user,
            group=test_group,
        )

        response = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertNotIn(test_post, response.context['page_obj'])

    def test_comment_in_post_detail(self):
        """Проверяем отображение комментария на странице поста"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIn('comments', response.context)

    def test_cache(self):
        """Тестирование кэша"""
        post = Post.objects.create(
            text='Пост для тестирования кеша',
            author=self.user,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        temp = response.content
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, temp)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, temp)

    def test_following_authorized_client(self):
        """Авторизованный пользователь может подписаться"""
        self.authorized_client_follower.post(reverse(
            'posts:profile_follow', kwargs={'username': self.user}))
        self.assertTrue(Follow.objects.filter(
            user=self.follower,
            author=self.user).exists())

    def test_unfollowing_authorized_client(self):
        """Авторизованный пользователь может отписаться"""
        self.authorized_client_follower.post(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user}))
        Follow.objects.filter(
            user=self.follower,
            author=self.user).delete()
        self.assertFalse(Follow.objects.filter(
            user=self.follower,
            author=self.user).exists())

    def test_new_post_se_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user,
        )
        follow = Follow.objects.create(
            user=self.follower,
            author=self.user
        )
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        post = response.context.get('page_obj')[0]
        self.assertEqual(post, posts)
        follow.delete()
        response_2 = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_2.context.get('page_obj')), 0)

    def test_new_post_not_in_following_page(self):
        """Пост не появляется в ленте у тех, кто не подписан."""
        response = self.authorized_client_no_follower.get(
            reverse('posts:follow_index')
        )
        post_count = len(response.context.get('page_obj').object_list)
        Post.objects.create(
            text='Тестовый текст для нового поста',
            author=self.user,
            group=self.group,
        )
        response = self.authorized_client_no_follower.get(
            reverse('posts:follow_index')
        )
        post_count1 = len(response.context.get('page_obj').object_list)
        self.assertEqual(post_count, post_count1)


class PaginatorTest(TestCase):
    MORE_POSTS = 6

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_client = Client()
        cls.user = User.objects.create(username='leo')
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug'
        )
        for i in range(settings.NUMBER_POSTS + PaginatorTest.MORE_POSTS):
            cls.post_2 = Post.objects.create(
                text=f'Тестовый текст {i+1}',
                author=cls.user,
                group=cls.group,
            )

    def test_correct_paginator(self):
        """Paginator работает корректно."""
        pag_address = {
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post_2.author}),
        }

        for paginator in pag_address:
            with self.subTest(paginator=paginator):
                response = self.client.get(paginator)
                self.assertEqual(len(
                    response.context['page_obj']
                ), settings.NUMBER_POSTS)
                response = self.client.get(paginator + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), PaginatorTest.MORE_POSTS
                )
