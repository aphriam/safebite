from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import UserAllergy


class AllergyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success_and_duplicate(self):
        response = self.client.post(
            '/api/auth/register/',
            {'username': 'alice', 'password': 'pass12345', 'email': 'alice@example.com'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='alice').exists())

        duplicate = self.client.post(
            '/api/auth/register/',
            {'username': 'alice', 'password': 'pass12345'},
            format='json',
        )
        self.assertEqual(duplicate.status_code, 400)

    def test_login_invalid_credentials(self):
        User.objects.create_user(username='bob', password='secret123')

        response = self.client.post(
            '/api/auth/login/',
            {'username': 'bob', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    def test_profile_requires_auth(self):
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, 403)

    def test_add_get_delete_allergy_flow(self):
        user = User.objects.create_user(username='carol', password='secret123')
        self.client.force_authenticate(user=user)

        add = self.client.post(
            '/api/profile/add-allergy/',
            {'allergy_name': 'peanut'},
            format='json',
        )
        self.assertEqual(add.status_code, 201)
        allergy_id = add.json()['id']

        profile = self.client.get('/api/profile/')
        self.assertEqual(profile.status_code, 200)
        allergies = profile.json()['allergies']
        self.assertEqual(len(allergies), 1)
        self.assertEqual(allergies[0]['allergy_name'], 'peanut')

        delete = self.client.delete(f'/api/profile/delete-allergy/{allergy_id}/')
        self.assertEqual(delete.status_code, 200)
        self.assertFalse(UserAllergy.objects.filter(id=allergy_id).exists())

    @patch('allergy.views.predict_risk', return_value=('high', 91))
    def test_predict_history_and_clear(self, _mock_predict):
        user = User.objects.create_user(username='dave', password='secret123')
        UserAllergy.objects.create(user=user, allergy_name='milk')
        self.client.force_authenticate(user=user)

        predict = self.client.post(
            '/api/predict/',
            {'ingredients': 'milk, sugar'},
            format='json',
        )
        self.assertEqual(predict.status_code, 200)
        payload = predict.json()
        self.assertEqual(payload['predicted_risk'], 'high')
        self.assertEqual(payload['confidence_percent'], '91%')
        self.assertEqual(payload['user_allergies_detected'], ['milk'])

        history = self.client.get('/api/history/')
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()['history']), 1)

        cleared = self.client.delete('/api/history/clear/')
        self.assertEqual(cleared.status_code, 200)

        history_after = self.client.get('/api/history/')
        self.assertEqual(history_after.status_code, 200)
        self.assertEqual(history_after.json()['history'], [])
