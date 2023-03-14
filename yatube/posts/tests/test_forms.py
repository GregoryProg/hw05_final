import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.test_post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_valid_form_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_valid_form_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        test_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменяем текст',
            'group': test_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.test_post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.test_post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(pk=self.test_post.id)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], test_group.id)

    def test_add_comment_for_authorized_client(self):
        """Проверка комментариев для авторизованного пользователя"""
        Comment.objects.all().delete()
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.test_post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.test_post.id}
            )
        )
        self.assertEqual(Post.objects.count(), comments_count + 1)
        comment = Comment.objects.first()
        self.assertEqual(form_data['text'], comment.text)

    def test_add_comment_for_authorized_client(self):
        """Проверка комментариев для неавторизованного пользователя"""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.test_post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/posts/{self.test_post.id}/comment/')
        )
