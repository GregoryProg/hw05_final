from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='User')
        cls.author = User.objects.create(username='not_author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.authorized_client_not_auth = Client()
        self.authorized_client_not_auth.force_login(PostURLTests.author)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_posts_post_id_edit_url_exists_at_author(self):
        """Страница /posts/post_id/edit/ доступна автору."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /posts/post_id/edit/ перенаправит
        неавторизованного пользователя пользователя
        на страницу логина.
        """
        response = self.guest_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/posts/{self.post.pk}/edit/')
        )

    def test_post_edit_url_redirect_anonymous_on_post_id(self):
        """Страница по адресу /posts/post_id/edit/ перенаправит
        авторизованного пользователя на страницу поста.
        """
        response = self.authorized_client_not_auth.get(
            f'/posts/{self.post.id}/edit/',
            follow=True)
        self.assertRedirects(
            response,
            (f'/posts/{self.post.id}/')
        )

    def test_unexisting_page_at_desired_places(self):
        """Страница /unexisting_page/ должна выдать ошибку."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_follow_url(self):
        """Тест подписки на автора"""

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_in_their_places(self):
        self.templates = [
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.user}/",
            f"/posts/{self.post.id}/",
        ]
        for adress in self.templates:
            with self.subTest(adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
