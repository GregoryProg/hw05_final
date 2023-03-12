from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Самый тестовый пост и всех постов',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий на 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        check_str = (
            (str(self.post), self.post.text[:15]),
            (str(self.group), self.group.title),
            (str(self.comment), self.comment.text[:15]),
        )
        for value1, value2 in check_str:
            with self.subTest(value1=value1):
                self.assertEqual(value1, value2)

    def test_comment_verbose_name(self):
        comment = self.comment
        field_verboses = {
            'post': 'Пост комментария',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)
