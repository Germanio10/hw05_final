from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Follow, Post, Group, Comment
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model()
TEST_OF_POST = 13


class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Name')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description')

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded)
        cls.comment = Comment.objects.create(
            text='test text',
            author=cls.user,
            post=cls.post
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_pages_names = {
            'posts/index.html': reverse('posts:main_page'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': 'test-slug'}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': 'Name'}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={'post_id': (self.
                                                      post.pk)}),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:main_page'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = self.user
        post_group_0 = self.group
        post_image_0 = self.uploaded
        self.assertEqual(post_text_0, 'test text')
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_image_0, self.uploaded)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-slug'}))
        first_object = response.context['group']
        post_title = first_object.title
        post_slug = first_object.slug
        post_description = first_object.description
        post_image = self.uploaded
        self.assertEqual(post_title, 'test title')
        self.assertEqual(post_slug, 'test-slug')
        self.assertEqual(post_description, 'test description')
        self.assertEqual(post_image, self.uploaded)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'Name'}))
        first_object = response.context['author']
        post_username = first_object.username
        post_image = self.uploaded
        self.assertEqual(post_username, 'Name')
        self.assertEqual(post_image, self.uploaded)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id': (self.
                                                      post.pk)}))
        first_object = response.context['post']
        post_text = first_object.text
        post_author = self.user
        post_group = self.group
        post_image = self.uploaded
        self.assertEqual(post_text, 'test text')
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_image, self.uploaded)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон create_post по id  сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': (self.
                                                      post.pk)}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group(self):
        """Пост с группой появится на страницах"""
        response_index = self.authorized_client.get(
            reverse('posts:main_page'))
        response_group = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}))
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'Name'}))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(self.post, index)
        self.assertIn(self.post, group)
        self.assertIn(self.post, profile)

    def test_post_not_in_another_group(self):
        """Пост не находится в чужой группе"""
        self.group_2 = Group.objects.create(
            title='test title2',
            slug='test-slugg',
            description='test description2'
        )
        response_group = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slugg'}))
        group = response_group.context['page_obj']
        self.assertNotIn(self.post, group)

    def test_post_with_comment(self):
        """Comment с постом появится на страницах"""
        response_detail = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        detail = response_detail.context['comments']

        self.assertIn(self.comment, detail)


class PaginatorTestViews(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test-slug')
        bilk_post = []
        for i in range(TEST_OF_POST):
            bilk_post.append(Post(text=f'Тестовый текст{i}',
                                  group=self.group,
                                  author=self.user))
        Post.objects.bulk_create(bilk_post)

    def test_first_page_concatins_ten_records(self):
        """На первой странице находится 10 записей"""
        reverse_list = [
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'Name'})
        ]
        for reverse_name in reverse_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_concatins_ten_records(self):
        """На первой странице находится 10 записей"""
        reverse_list = [
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'})
        ]
        for reverse_name in reverse_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowTest(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='test text'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        """Корректная работа подписки"""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)
     

    def test_unfollow(self):
        """Корректная работа отписки"""
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_post_in_follow_page(self):
        """Посты появляются на странице follow"""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_follower.get('/follow/')
        post_text = response.context['page_obj'][0].text
        self.assertEqual(post_text, 'test text')
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response, 'test text')
