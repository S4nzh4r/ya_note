from http import HTTPStatus

from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Ronaldo')
        cls.aut_client = Client()
        cls.aut_client.force_login(cls.user)

        cls.note_url = reverse('notes:add')
        cls.form_data = {
            'title': 'Title', 'text': 'Text',
            'slug': 'test-slug', 'author': cls.user
        }

    def test_user_can_create_notes(self):
        response = self.aut_client.post(self.note_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.user)

    def test_anonymous_user_cant_create_notes(self):
        response = self.client.post(self.note_url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.note_url}'
        self.assertRedirects(response, expected_url)

        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_not_unique_slug(self):
        note = Note.objects.create(**self.form_data)
        self.form_data['slug'] = note.slug
        response = self.aut_client.post(self.note_url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(note.slug + WARNING)
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        self.form_data.pop('slug')
        response = self.aut_client.post(self.note_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        self.assertEqual(Note.objects.count(), 1)

        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNotesEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author')
        cls.client_auth = Client()
        cls.client_auth.force_login(cls.author)

        cls.reader = User.objects.create(username='Reader')
        cls.client_reader = Client()
        cls.client_reader.force_login(cls.reader)

        cls.note = Note.objects.create(
            title='Title',
            text='TEXT',
            author=cls.author,
            slug='slug'
        )

        cls.note_detail = reverse('notes:detail', args=(cls.note.slug,))
        cls.note_edit = reverse('notes:edit', args=(cls.note.slug,))
        cls.note_delete = reverse('notes:delete', args=(cls.note.slug,))
        cls.succes_url = reverse('notes:success')

        cls.form_data = {'title': 'New_Title',
                         'text': 'NEW_TEXT',
                         'slug': 'new-slug'}

    def test_user_can_edit_note(self):
        response = self.client_auth.post(self.note_edit, data=self.form_data)
        self.assertRedirects(response, self.succes_url)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        response = self.client_reader.post(self.note_edit, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_user_can_delete_note(self):
        response = self.client_auth.delete(self.note_delete)
        self.assertRedirects(response, self.succes_url)

        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_other_user_cant_delete_note(self):
        response = self.client_reader.delete(self.note_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
