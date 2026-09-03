import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from kembang.contact import normalize_whatsapp
from kembang.models import ChatThread, SuratKelahiran, UserProfile


class ContactTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warga = User.objects.create_user(username="contact-warga")
        cls.other = User.objects.create_user(username="contact-other")
        cls.staff = User.objects.create_user(username="contact-staff", is_staff=True)
        UserProfile.objects.create(
            user=cls.warga,
            nama="Warga Kontak",
            alamat="Alamat",
            no_whatsapp="0812-3456 (7890)",
        )
        cls.application = SuratKelahiran.objects.create(
            user=cls.warga,
            nama_lengkap="Bayi Kontak",
            tempat_lahir="Bogor",
            tanggal_lahir="2024-01-01",
            jenis_kelamin="L",
            nama_ayah="Ayah",
            nama_ibu="Ibu",
            alamat="Alamat",
            no_whatsapp="080000000000",
            surat_keterangan_lahir="lahir.pdf",
            fotokopi_ktp_kk="ktpkk.pdf",
            fotokopi_buku_nikah="nikah.pdf",
            surat_pengantar_rt_rw="pengantar.pdf",
            status="ditolak",
            alasan_penolakan="Dokumen kurang jelas.",
        )

    def test_normalize_whatsapp_formats(self):
        self.assertEqual(normalize_whatsapp("081234567890"), "6281234567890")
        self.assertEqual(normalize_whatsapp("+6281234567890"), "6281234567890")
        self.assertEqual(normalize_whatsapp("6281234567890"), "6281234567890")
        self.assertEqual(normalize_whatsapp("0812-3456 (7890)"), "6281234567890")
        self.assertIsNone(normalize_whatsapp(""))
        self.assertIsNone(normalize_whatsapp("12345"))

    def test_staff_contact_endpoint_creates_one_thread_and_redirects_directly(self):
        self.client.force_login(self.staff)

        first = self.client.get(
            reverse("chat_from_pengajuan", args=["suratkelahiran", self.application.pk])
        )
        second = self.client.get(
            reverse("chat_from_pengajuan", args=["suratkelahiran", self.application.pk])
        )

        thread = ChatThread.objects.get(user=self.warga)
        target = reverse("chat_admin_thread", args=[thread.pk])
        self.assertEqual(first.status_code, 302)
        self.assertEqual(first.url, target)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(second.url, target)
        self.assertEqual(ChatThread.objects.filter(user=self.warga).count(), 1)

    def test_anonymous_and_warga_cannot_start_staff_contact_chat(self):
        url = reverse("chat_from_pengajuan", args=["suratkelahiran", self.application.pk])

        anonymous_response = self.client.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        self.client.force_login(self.other)
        warga_response = self.client.get(url)
        self.assertEqual(warga_response.status_code, 302)
        self.assertEqual(ChatThread.objects.filter(user=self.warga).count(), 0)

    def test_public_contact_message_contains_allowed_data_only(self):
        from kembang.templatetags.contact_tags import whatsapp_message

        message = whatsapp_message(self.application, "Surat Kelahiran")
        self.assertIn("Warga Kontak", message)
        self.assertIn("Surat Kelahiran", message)
        self.assertIn("Ditolak", message)
        self.assertIn("Dokumen kurang jelas.", message)
        self.assertNotIn(self.warga.username, message)
        self.assertNotIn("080000000000", message)

    def test_staff_submission_list_renders_contact_actions(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("daftar_pengajuan_kelahiran"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hubungi")
        self.assertContains(response, "6281234567890")
        self.assertContains(response, reverse("chat_from_pengajuan", args=["suratkelahiran", self.application.pk]))
