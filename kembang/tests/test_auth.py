from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from kembang.models import UserProfile


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warga = User.objects.create_user(
            username="3201010101010001",
            email="warga@example.com",
            password="WargaPass123!",
        )
        UserProfile.objects.create(
            user=cls.warga,
            nama="Warga Satu",
            alamat="Alamat Warga",
        )
        cls.staff = User.objects.create_user(
            username="staff01",
            email="staff@example.com",
            password="StaffPass123!",
            is_staff=True,
        )

    def test_warga_can_login(self):
        response = self.client.post(
            reverse("login"),
            {"nik": self.warga.username, "password": "WargaPass123!"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_staff_can_login_to_admin_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"nik": self.staff.username, "password": "StaffPass123!"},
        )

        self.assertRedirects(response, reverse("admin_dashboard"))
        self.assertTrue(response.wsgi_request.user.is_staff)

    def test_login_fails_with_invalid_password(self):
        response = self.client.post(
            reverse("login"),
            {"nik": self.warga.username, "password": "wrong-password"},
            follow=True,
        )

        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "NIK atau password salah")

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse("register"),
            {
                "nik": "3201010101010002",
                "nama": "Warga Baru",
                "alamat": "Alamat Baru",
                "no_whatsapp": "081234567890",
                "email": "baru@example.com",
                "password": "PasswordBaru123!",
                "confirm_password": "PasswordBaru123!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="3201010101010002")
        self.assertTrue(user.check_password("PasswordBaru123!"))
        self.assertEqual(user.userprofile.nama, "Warga Baru")
        self.assertEqual(user.userprofile.no_whatsapp, "081234567890")

    def test_register_rejects_duplicate_nik(self):
        response = self.client.post(
            reverse("register"),
            {
                "nik": self.warga.username,
                "nama": "Nama Lain",
                "alamat": "Alamat Lain",
                "email": "lain@example.com",
                "password": "PasswordBaru123!",
                "confirm_password": "PasswordBaru123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NIK ini sudah terdaftar")
        self.assertEqual(User.objects.filter(username=self.warga.username).count(), 1)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "nik": "3201010101010003",
                "nama": "Warga Lemah",
                "alamat": "Alamat",
                "email": "lemah@example.com",
                "password": "123",
                "confirm_password": "123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="3201010101010003").exists())

    def test_register_rejects_mismatched_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "nik": "3201010101010004",
                "nama": "Warga Beda",
                "alamat": "Alamat",
                "email": "beda@example.com",
                "password": "Password123!",
                "confirm_password": "Password456!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="3201010101010004").exists())

    def test_logout_ends_session(self):
        self.client.force_login(self.warga)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("home"))
        response = self.client.get(reverse("cek_status"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('cek_status')}")

    def test_logout_get_is_not_allowed(self):
        self.client.force_login(self.warga)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_without_csrf_is_rejected(self):
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(self.warga)

        response = client.post(reverse("logout"))

        self.assertEqual(response.status_code, 403)
