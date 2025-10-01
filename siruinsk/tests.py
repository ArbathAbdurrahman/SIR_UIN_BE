from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json


class RegistrationViewTest(APITestCase):
    """Test RegistrationView"""
    
    def setUp(self):
        self.client = APIClient()
        self.registration_url = '/api/auth/register/'  # Sesuaikan dengan URL Anda
    
    def test_successful_registration(self):
        """Test registrasi user yang berhasil"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'strongpassword123',
            'password2': 'strongpassword123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        response = self.client.post(self.registration_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(User.objects.count(), 1)
        
        # Verify user data
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
    
    def test_registration_with_existing_username(self):
        """Test registrasi dengan username yang sudah ada"""
        # Create existing user
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        data = {
            'username': 'existinguser',
            'email': 'newemail@example.com',
            'password': 'password123',
            'password2': 'password123'
        }
        response = self.client.post(self.registration_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
    
    def test_registration_with_existing_email(self):
        """Test registrasi dengan email yang sudah ada"""
        User.objects.create_user(
            username='user1',
            email='existing@example.com',
            password='password123'
        )
        
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'password123',
            'password2': 'password123'
        }
        response = self.client.post(self.registration_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
    
    def test_registration_with_mismatched_passwords(self):
        """Test registrasi dengan password yang tidak cocok"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password2': 'differentpassword'
        }
        response = self.client.post(self.registration_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
    
    def test_registration_with_missing_fields(self):
        """Test registrasi dengan field yang tidak lengkap"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com'
            # Missing password fields
        }
        response = self.client.post(self.registration_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
    
    def test_registration_with_invalid_email(self):
        """Test registrasi dengan format email yang tidak valid"""
        data = {
            'username': 'newuser',
            'email': 'invalidemail',
            'password': 'password123',
            'password2': 'password123'
        }
        response = self.client.post(self.registration_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class LoginViewTest(APITestCase):
    """Test LoginView"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/auth/login/'  # Sesuaikan dengan URL Anda
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
    
    def test_successful_login_with_username(self):
        """Test login yang berhasil dengan username"""
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_successful_login_with_email(self):
        """Test login yang berhasil dengan email"""
        data = {
            'username': 'test@example.com',  # Using email as identifier
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_login_with_wrong_password(self):
        """Test login dengan password yang salah"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_login_with_nonexistent_user(self):
        """Test login dengan user yang tidak ada"""
        data = {
            'username': 'nonexistent',
            'password': 'somepassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_login_with_missing_username(self):
        """Test login tanpa username"""
        data = {
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('wajib diisi', response.data['error'])
    
    def test_login_with_missing_password(self):
        """Test login tanpa password"""
        data = {
            'username': 'testuser'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('wajib diisi', response.data['error'])
    
    def test_login_with_empty_credentials(self):
        """Test login dengan credentials kosong"""
        data = {
            'username': '',
            'password': ''
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_login_response_contains_user_data(self):
        """Test response login mengandung data user yang lengkap"""
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['user']
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['first_name'], 'Test')
        self.assertEqual(user_data['last_name'], 'User')
    
    def test_tokens_are_valid(self):
        """Test bahwa token yang di-generate valid"""
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to use the access token
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Make an authenticated request (you'll need to adjust the URL)
        # auth_response = self.client.get('/api/auth/me/')
        # self.assertEqual(auth_response.status_code, status.HTTP_200_OK)


class LogoutViewTest(APITestCase):
    """Test LogoutView"""
    
    def setUp(self):
        self.client = APIClient()
        self.logout_url = '/api/auth/logout/'  # Sesuaikan dengan URL Anda
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Generate tokens
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.refresh_token = str(self.refresh)
    
    def test_successful_logout(self):
        """Test logout yang berhasil"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        data = {
            'refresh': self.refresh_token
        }
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Logout successful')
    
    def test_logout_without_authentication(self):
        """Test logout tanpa authentication"""
        data = {
            'refresh': self.refresh_token
        }
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_without_refresh_token(self):
        """Test logout tanpa refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        data = {}
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Refresh token is required')
    
    def test_logout_with_invalid_refresh_token(self):
        """Test logout dengan refresh token yang tidak valid"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        data = {
            'refresh': 'invalid_token_string'
        }
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid or expired', response.data['error'])
    
    def test_logout_with_already_blacklisted_token(self):
        """Test logout dengan token yang sudah di-blacklist"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # First logout
        data = {
            'refresh': self.refresh_token
        }
        self.client.post(self.logout_url, data)
        
        # Try to logout again with same token
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class AuthViewTest(APITestCase):
    """Test AuthView (Get current user info)"""
    
    def setUp(self):
        self.client = APIClient()
        self.auth_url = '/api/auth/me/'  # Sesuaikan dengan URL Anda
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        
        # Generate tokens
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
    
    def test_get_authenticated_user_info(self):
        """Test mendapatkan info user yang terautentikasi"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get(self.auth_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
    
    def test_get_user_info_without_authentication(self):
        """Test mendapatkan info user tanpa authentication"""
        response = self.client.get(self.auth_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Not authenticated')
    
    def test_get_user_info_with_invalid_token(self):
        """Test mendapatkan info user dengan token yang tidak valid"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        response = self.client.get(self.auth_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_response_contains_all_user_fields(self):
        """Test response mengandung semua field user yang dibutuhkan"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get(self.auth_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
    
    def test_auth_view_does_not_expose_password(self):
        """Test bahwa response tidak mengandung password"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get(self.auth_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)


class AuthIntegrationTest(APITestCase):
    """Integration tests untuk full authentication flow"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.logout_url = '/api/auth/logout/'
        self.auth_url = '/api/auth/me/'
    
    def test_full_auth_flow(self):
        """Test complete authentication flow: register -> login -> get user -> logout"""
        
        # 1. Register
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'strongpassword123',
            'password2': 'strongpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        register_response = self.client.post(self.register_url, register_data)
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        
        # 2. Login
        login_data = {
            'username': 'newuser',
            'password': 'strongpassword123'
        }
        login_response = self.client.post(self.login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # 3. Get user info
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        auth_response = self.client.get(self.auth_url)
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_response.data['username'], 'newuser')
        
        # 4. Logout
        logout_data = {
            'refresh': refresh_token
        }
        logout_response = self.client.post(self.logout_url, logout_data)
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)
    
    def test_login_with_email_after_registration(self):
        """Test login menggunakan email setelah registrasi"""
        
        # Register
        register_data = {
            'username': 'emailuser',
            'email': 'emailuser@example.com',
            'password': 'password123',
            'password2': 'password123'
        }
        self.client.post(self.register_url, register_data)
        
        # Login with email
        login_data = {
            'username': 'emailuser@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_cannot_access_protected_endpoint_after_logout(self):
        """Test tidak bisa akses protected endpoint setelah logout"""
        
        # Create and login user
        user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_data = {'refresh': refresh_token}
        self.client.post(self.logout_url, logout_data)
        
        # Note: Access token masih valid sampai expire
        # Tapi refresh token sudah di-blacklist
        # Jadi user tidak bisa mendapatkan access token baru