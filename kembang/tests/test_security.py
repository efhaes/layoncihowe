import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from kembang.models import Announcement, ChatThread, SuratKelahiran


class SecurityAndEdgeCaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warga = User.objects.create_user(
            username="security-warga",
            password="WargaPass123!",
        )
        cls.warga_lain = User.objects.create_user(
            username="security-lain",
            password="WargaPass123!",
        )
        cls.staff = User.objects.create_user(
            username="security-staff",
            password="StaffPass123!",
            is_staff=True,
        )
        cls.application = SuratKelahiran.objects.create(
            user=cls.warga_lain,
            nama_lengkap="Nama Rahasia",
            tempat_lahir="Bogor",
            tanggal_lahir="2024-01-01",
            jenis_kelamin="L",
            nama_ayah="Ayah",
            nama_ibu="Ibu",
            alamat="Alamat",
            no_whatsapp="081234567890",
            surat_keterangan_lahir="lahir.pdf",
            fotokopi_ktp_kk="ktpkk.pdf",
            fotokopi_buku_nikah="nikah.pdf",
            surat_pengantar_rt_rw="pengantar.pdf",
        )

    def test_staff_status_update_rejects_invalid_status_and_preserves_old_value(self):
        self.client.force_login(self.staff)
        old_status = self.application.status

        response = self.client.post(
            reverse("detail_pengajuan_kelahiran", args=[self.application.pk]),
            {"status": "status-palsu"},
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, old_status)

    def test_rejected_status_requires_trimmed_reason(self):
        self.client.force_login(self.staff)
        detail_url = reverse("detail_pengajuan_kelahiran", args=[self.application.pk])

        response = self.client.post(detail_url, {"status": "ditolak", "alasan_penolakan": "  "})

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "diajukan")
        self.assertIsNone(self.application.alasan_penolakan)

        response = self.client.post(
            detail_url,
            {"status": "ditolak", "alasan_penolakan": "  Dokumen kurang jelas.  "},
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "ditolak")
        self.assertEqual(self.application.alasan_penolakan, "Dokumen kurang jelas.")

    def test_non_rejected_status_clears_old_reason(self):
        self.application.status = "ditolak"
        self.application.alasan_penolakan = "Dokumen kurang jelas."
        self.application.save(update_fields=["status", "alasan_penolakan"])
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("detail_pengajuan_kelahiran", args=[self.application.pk]),
            {"status": "diproses"},
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "diproses")
        self.assertIsNone(self.application.alasan_penolakan)

    def test_owner_sees_rejection_reason_but_other_warga_does_not(self):
        self.application.status = "ditolak"
        self.application.alasan_penolakan = "Dokumen tidak terbaca."
        self.application.save(update_fields=["status", "alasan_penolakan"])

        self.client.force_login(self.warga)
        other_response = self.client.get(reverse("cek_status"), {"jenis": "kelahiran"})
        self.assertNotContains(other_response, "Dokumen tidak terbaca.")

        self.client.force_login(self.warga_lain)
        owner_response = self.client.get(reverse("cek_status"), {"jenis": "kelahiran"})
        self.assertContains(owner_response, "Dokumen tidak terbaca.")

    def test_mass_assignment_cannot_change_owner_on_submission(self):
        self.client.force_login(self.warga)
        data = {
            "nama_lengkap": "Bayi Aman",
            "tempat_lahir": "Bogor",
            "tanggal_lahir": "2024-01-01",
            "jenis_kelamin": "L",
            "nama_ayah": "Ayah",
            "nama_ibu": "Ibu",
            "alamat": "Alamat",
            "no_whatsapp": "081234567890",
            "surat_keterangan_lahir": SimpleUploadedFile("lahir.pdf", b"pdf"),
            "fotokopi_ktp_kk": SimpleUploadedFile("ktpkk.pdf", b"pdf"),
            "fotokopi_buku_nikah": SimpleUploadedFile("nikah.pdf", b"pdf"),
            "surat_pengantar_rt_rw": SimpleUploadedFile("pengantar.pdf", b"pdf"),
            "user": self.warga_lain.pk,
            "status": "selesai",
        }

        response = self.client.post(reverse("pengajuan_akta_kelahiran"), data)

        self.assertEqual(response.status_code, 302)
        created = SuratKelahiran.objects.get(nama_lengkap="Bayi Aman")
        self.assertEqual(created.user_id, self.warga.pk)
        self.assertEqual(created.status, "diajukan")

    def test_xss_payload_is_escaped_in_public_announcement_response(self):
        announcement = Announcement.objects.create(
            title="<script>alert(1)</script>",
            content="<img src=x onerror=alert(1)>",
            is_active=True,
        )

        response = self.client.get(reverse("announcement_ajax_detail", args=[announcement.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("<script>alert(1)</script>", response.json()["html"])

    def test_warga_cannot_access_other_chat_thread(self):
        self.client.force_login(self.warga)
        thread = ChatThread.objects.create(user=self.warga_lain)

        response = self.client.post(
            reverse("chat_ketik"),
            {"thread_id": thread.pk},
        )

        self.assertEqual(response.status_code, 403)

    def test_missing_object_returns_404(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("detail_pengajuan_kelahiran", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_invalid_json_returns_400(self):
        self.client.force_login(self.warga)

        response = self.client.post(
            reverse("chat_kirim"),
            data="{invalid",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_get_to_post_only_delete_returns_405(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("hapus_kelahiran", args=[self.application.pk]))

        self.assertEqual(response.status_code, 405)

    def test_staff_only_endpoint_cannot_be_used_by_warga(self):
        self.client.force_login(self.warga)

        response = self.client.get(reverse("kelola_tentang"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
