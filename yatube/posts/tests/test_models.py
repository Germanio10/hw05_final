from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post


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
            text='Текстовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__"""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_name_group = group.title
        expected_object_name_post = post.text
        self.assertEqual(expected_object_name_post, str(post))
        self.assertEqual(expected_object_name_group, str(group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым"""
        post = PostModelTest.post
        field_verbose = {
            'text': 'Текст',
            'group': 'Группа'
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым"""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста'
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
