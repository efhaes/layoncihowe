from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from kembang.models import SuratKelahiran, UserProfile


class PermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.warga = User.objects.create_user(
            username="3201010101010011",
            password="WargaPass123!",
        )
        cls.warga_lain = User.objects.create_user(
            username="3201010101010012",
            password="WargaPass123!",
        )
        cls.staff = User.objects.create_user(
            username="staff02",
            password="StaffPass123!",
            is_staff=True,
        )
        UserProfile.objects.create(user=cls.warga, nama="Warga", alamat="Alamat")
        UserProfile.objects.create(
            user=cls.warga_lain,
            nama="Warga Lain",
            alamat="Alamat Lain",
        )
        cls.pengajuan = SuratKelahiran.objects.create(
            user=cls.warga_lain,
            nama_lengkap="Anak Warga Lain",
            tempat_lahir="Bogor",
            tanggal_lahir="2020-01-01",
            jenis_kelamin="L",
            nama_ayah="Ayah",
            nama_ibu="Ibu",
            alamat="Alamat Lain",
            no_whatsapp="081234567890",
            surat_keterangan_lahir="syarat/kelahiran/surat_keterangan/lahir.pdf",
            fotokopi_ktp_kk="syarat/kelahiran/ktp_kk/kk.pdf",
            fotokopi_buku_nikah="syarat/kelahiran/buku_nikah/nikah.pdf",
            surat_pengantar_rt_rw="syarat/kelahiran/pengantar_rt_rw/pengantar.pdf",
        )

    def test_login_required_page_redirects_anonymous_user(self):
        response = self.client.get(reverse("cek_status"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('cek_status')}",
        )

    def test_warga_cannot_access_staff_dashboard(self):
        self.client.force_login(self.warga)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('admin_dashboard')}",
        )

    def test_warga_cannot_access_staff_detail(self):
        self.client.force_login(self.warga)

        response = self.client.get(
            reverse("detail_pengajuan_kelahiran", args=[self.pengajuan.pk])
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('detail_pengajuan_kelahiran', args=[self.pengajuan.pk])}",
        )

    def test_warga_cannot_read_another_users_status(self):
        self.client.force_login(self.warga)

        response = self.client.get(
            reverse("cek_status"),
            {"jenis": "kelahiran"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Anak Warga Lain")

    def test_warga_cannot_delete_another_users_application(self):
        self.client.force_login(self.warga)

        response = self.client.post(
            reverse("hapus_kelahiran", args=[self.pengajuan.pk])
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('hapus_kelahiran', args=[self.pengajuan.pk])}",
        )
        self.assertTrue(SuratKelahiran.objects.filter(pk=self.pengajuan.pk).exists())

    def test_staff_can_access_admin_page(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_staff_can_read_application_detail(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("detail_pengajuan_kelahiran", args=[self.pengajuan.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_invalid_generic_delete_model_is_forbidden(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("hapus_surat", args=["user", self.warga.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.warga.pk).exists())

    def test_nonexistent_application_detail_returns_404(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("detail_pengajuan_kelahiran", args=[999999])
        )

        self.assertEqual(response.status_code, 404)
