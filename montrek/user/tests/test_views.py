from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.test import TestCase
from django.urls import reverse

class SignUpViewTests(TestCase):
    def test_signup_view(self):
        url = reverse('signup')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/signup.html')

    def test_signup_form_submission(self):
        url = reverse('signup')
        data = {
            'username': 'testuser',
            'password1': 'testpassword',
            'password2': 'testpassword',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_signup_form_invalid_submission(self):
        url = reverse('signup')
        data = {
            'username': 'invalid-username!',
            'password1': 'testpassword',
            'password2': 'testpassword',
        }

        response = self.client.post(url, data)
        messages = list(response.context['messages'])

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/signup.html')
        self.assertContains(response, 'Enter a valid username.')
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            '<ul class="errorlist">'
            '<li>username'
            '<ul class="errorlist">'
            '<li>Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.</li>'
            '</ul>'
            '</li>'
            '</ul>'
        )


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
        )

    def test_login_view(self):
        url = reverse('login')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/login.html')

    def test_login_form_submission(self):
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpassword',
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_login_form_invalid_submission(self):
        url = reverse('login')
        data = {
            'username': 'nonexistent-user',
            'password': 'testpassword',
        }

        response = self.client.post(url, data)
        messages = list(response.context['messages'])

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/login.html')
        self.assertContains(response, 'Please enter a correct username and password.')
        self.assertEqual(
            str(messages[0]),
            '<ul class="errorlist">'
            '<li>__all__'
            '<ul class="errorlist nonfield">'
            '<li>Please enter a correct username and password. Note that both fields may be case-sensitive.'
            '</li>'
            '</ul>'
            '</li>'
            '</ul>'
        )
