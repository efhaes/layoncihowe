import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from kembang.models import ChatMessage, ChatThread, DesaEncryptionKey, UserEncryptionKey


class ChatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warga = User.objects.create_user(
            username="chat-warga",
            password="WargaPass123!",
        )
        cls.warga_lain = User.objects.create_user(
            username="chat-lain",
            password="WargaPass123!",
        )
        cls.staff = User.objects.create_user(
            username="chat-staff",
            password="StaffPass123!",
            is_staff=True,
        )

    def office_key(self):
        return DesaEncryptionKey.objects.create(
            public_key_jwk=json.dumps({"kty": "RSA", "n": "A" * 342, "e": "AQAB"}),
            wrapped_private_key=json.dumps({"ciphertext": "wrapped"}),
            wrapped_private_key_recovery=json.dumps({"ciphertext": "recovery"}),
        )

    def payload(self, thread_id):
        return {
            "thread_id": thread_id,
            "ciphertext": "ciphertext",
            "iv": "iv",
            "wrapped_key_warga": "warga-key",
            "wrapped_key_desa": "desa-key",
        }

    def test_warga_chat_creates_one_thread(self):
        self.client.force_login(self.warga)
        self.office_key()

        first = self.client.get(reverse("chat_saya"))
        second = self.client.get(reverse("chat_saya"))

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(ChatThread.objects.filter(user=self.warga).count(), 1)

    def test_warga_can_register_public_key_once(self):
        self.client.force_login(self.warga)
        data = {"public_key_jwk": {"kty": "RSA", "n": "A" * 342, "e": "AQAB"}}

        first = self.client.post(
            reverse("chat_daftar_kunci"),
            data=json.dumps(data),
            content_type="application/json",
        )
        second = self.client.post(
            reverse("chat_daftar_kunci"),
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(first.json()["status"], "created")
        self.assertEqual(second.json()["status"], "exists")
        self.assertEqual(UserEncryptionKey.objects.filter(user=self.warga).count(), 1)

    def test_warga_can_send_and_read_own_thread_messages(self):
        self.client.force_login(self.warga)
        thread = ChatThread.objects.create(user=self.warga)

        response = self.client.post(
            reverse("chat_kirim"),
            data=json.dumps(self.payload(thread.pk)),
            content_type="application/json",
        )
        messages = self.client.get(
            reverse("chat_pesan_list"),
            {"thread_id": thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(messages.status_code, 200)
        self.assertEqual(len(messages.json()["pesan"]), 1)

    def test_warga_cannot_access_other_thread(self):
        self.client.force_login(self.warga)
        other_thread = ChatThread.objects.create(user=self.warga_lain)

        response = self.client.get(
            reverse("chat_pesan_list"),
            {"thread_id": other_thread.pk},
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_can_open_chat_thread_after_keys_exist(self):
        self.client.force_login(self.staff)
        self.office_key()
        thread = ChatThread.objects.create(user=self.warga)
        UserEncryptionKey.objects.create(
            user=self.warga,
            public_key_jwk=json.dumps({"kty": "RSA", "n": "A" * 342, "e": "AQAB"}),
        )

        response = self.client.get(reverse("chat_admin_thread", args=[thread.pk]))

        self.assertEqual(response.status_code, 200)

    def test_staff_can_setup_office_key_only_once(self):
        self.client.force_login(self.staff)
        payload = {
            "public_key_jwk": {"kty": "RSA", "n": "A" * 342, "e": "AQAB"},
            "wrapped_private_key": {"ciphertext": "one"},
            "wrapped_private_key_recovery": {"ciphertext": "two"},
        }

        first = self.client.post(
            reverse("chat_setup_kunci_desa"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        second = self.client.post(
            reverse("chat_setup_kunci_desa"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 403)
        self.assertEqual(DesaEncryptionKey.objects.count(), 1)

    def test_recovery_replaces_wrapped_keys(self):
        self.client.force_login(self.staff)
        key = self.office_key()
        payload = {
            "wrapped_private_key": {"ciphertext": "new"},
            "wrapped_private_key_recovery": {"ciphertext": "new-recovery"},
        }

        response = self.client.post(
            reverse("chat_pemulihan_kunci"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        key.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(key.wrapped_private_key)["ciphertext"], "new")

    def test_invalid_chat_json_returns_bad_request(self):
        self.client.force_login(self.warga)

        response = self.client.post(
            reverse("chat_daftar_kunci"),
            data="not-json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_malformed_public_key_returns_bad_request(self):
        self.client.force_login(self.warga)

        response = self.client.post(
            reverse("chat_daftar_kunci"),
            data=json.dumps({"public_key_jwk": {"kty": "RSA", "n": "bad", "e": "AQAB"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_oversized_public_key_payload_returns_bad_request(self):
        self.client.force_login(self.warga)

        response = self.client.post(
            reverse("chat_daftar_kunci"),
            data=json.dumps({"public_key_jwk": {"kty": "RSA", "n": "A" * 9000, "e": "AQAB"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_chat_send_requires_post(self):
        self.client.force_login(self.warga)

        response = self.client.get(reverse("chat_kirim"))

        self.assertEqual(response.status_code, 405)
