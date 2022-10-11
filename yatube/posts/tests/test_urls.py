
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description',
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_redirect_authorized_not_author(self):
        """Редирект авториз.юзера не автора с post_edit"""
        self.user2 = User.objects.create(username='NoName')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        url1 = f'/posts/{self.post.id}/'
        pages = {f'/posts/{self.post.id}/edit/': url1}
        for page, value in pages.items():
            response = self.authorized_client2.get(page)
            self.assertRedirects(response, value)

    def test_redirect_guest_client(self):
        """Редирект неавторизованного пользователя"""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{self.post.id}/edit/': url2}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю"""
        url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': '/group/test-slug/',
            '/profile/HasNoName/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html'
        }
        for name in url_names:
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.assertEqual(response.status_code, 200)

    def test_url_with_user_at_desired_location(self):
        """Страницы доступны авторизованному или автору"""
        url_names = {
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }
        for name in url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """"URL-адрес использует соответсвующий шаблон."""
        templates_url_names = {
            'fsdfsdf': 'core/404.html',
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
