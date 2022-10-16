from django.contrib.auth import get_user_model
from django.test import TestCase, Client


from ..models import Group, Post, Follow, Comment

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_user = User.objects.create_user(username='Name')
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.user_user
        )
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
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='test comment'
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
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html'
        }
        for name in url_names:
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.assertEqual(response.status_code, 200)

    def test_url_with_user_at_desired_location(self):
        """Страницы доступны авторизованному или автору"""
        url_names = {
            '/profile/HasNoName/': 'posts/profile.html',
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
            # '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_profile_unfollow(self):
        """Код 200 и редирект"""
        response = self.authorized_client.get(
            f'/profile/{self.user}/unfollow/',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        response = self.guest_client.get(
            f'/profile/{self.user}/unfollow/',
            follow=True
        )
        self.assertRedirects(response,
        f'/auth/login/?next=/profile/{self.user}/unfollow/'
             )

    def test_profile_follow(self):
        """Код 200 и редирект"""
        response = self.authorized_client.get(
            f'/profile/{self.user}/follow/',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        response = self.guest_client.get(
            f'/profile/{self.user}/follow/',
            follow=True
        )
        url = f'/auth/login/?next=/profile/{self.user}/follow/'
        self.assertRedirects(response, url)
           
    def test_comment(self):
        url = f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        url2 = f'/posts/{self.post.pk}/'
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/comment/'
        )
        self.assertRedirects(response, url)
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/comment/'
        )
        self.assertRedirects(response, url2)
