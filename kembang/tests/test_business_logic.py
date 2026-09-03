from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from kembang.models import Announcement, SuratKelahiran


class BusinessLogicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(
            username="business-staff",
            password="StaffPass123!",
            is_staff=True,
        )
        cls.warga = User.objects.create_user(
            username="3201010101010201",
            password="WargaPass123!",
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def make_birth(self, status="diajukan", user=None):
        return SuratKelahiran.objects.create(
            user=user or self.warga,
            nama_lengkap="Bayi",
            tempat_lahir="Bogor",
            tanggal_lahir="2024-01-01",
            jenis_kelamin="L",
            nama_ayah="Ayah",
            nama_ibu="Ibu",
            alamat="Alamat",
            no_whatsapp="081234567890",
            status=status,
            surat_keterangan_lahir="lahir.pdf",
            fotokopi_ktp_kk="ktpkk.pdf",
            fotokopi_buku_nikah="nikah.pdf",
            surat_pengantar_rt_rw="pengantar.pdf",
        )

    def test_dashboard_statistics_count_all_application_statuses(self):
        self.make_birth("diajukan")
        self.make_birth("diproses")
        self.make_birth("selesai")

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status_summary"]["diajukan"], 1)
        self.assertEqual(response.context["status_summary"]["diproses"], 1)
        self.assertEqual(response.context["status_summary"]["selesai"], 1)
        self.assertEqual(response.context["belum_selesai_total"], 2)

    def test_combined_submission_recap_contains_model_and_owner_nik(self):
        self.make_birth()

        response = self.client.get(reverse("semua_pengajuan"))

        self.assertEqual(response.status_code, 200)
        item = response.context["semua_surat"][0]
        self.assertEqual(item.jenis_surat, "Surat Kelahiran")
        self.assertEqual(item.nik_display, self.warga.username)

    def test_staff_notification_counts_pending_records(self):
        self.make_birth("diajukan")
        self.make_birth("selesai")

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.context["notifikasi"]["kelahiran"], 1)
        self.assertEqual(response.context["notifikasi"]["total"], 1)

    def test_active_announcements_are_loaded_on_homepage(self):
        Announcement.objects.create(title="Aktif", content="Isi", is_active=True)
        Announcement.objects.create(title="Mati", content="Isi", is_active=False)
        self.client.force_login(self.warga)

        response = self.client.get(reverse("home"))

        announcement_titles = [item.title for item in response.context["announcements"]]
        self.assertIn("Aktif", announcement_titles)
        self.assertNotIn("Mati", announcement_titles)

    def test_year_filter_excludes_other_years(self):
        current = self.make_birth()
        current.tanggal_pengajuan = "2024-01-01T00:00:00Z"
        current.save(update_fields=["tanggal_pengajuan"])

        response = self.client.get(reverse("semua_pengajuan"), {"tahun": "2024"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["semua_surat"]), 1)
