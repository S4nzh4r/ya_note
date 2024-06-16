from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    # Вынесем ссылку список страниц в атрибуты класса.
    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатетль')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title='Заголовок',
            author=cls.author,
            text='Текст',
            slug='test'
        )

    def test_notes_in_list_for_different_users(self):
        user_notes = (
            (self.author_client, True),
            (self.reader_client, False)
        )

        for user, note_in_list in user_notes:
            with self.subTest(user=user):
                response = user.get(self.LIST_URL)
                object_list = response.context['object_list']
                self.assertEqual((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        notes_form = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in notes_form:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
