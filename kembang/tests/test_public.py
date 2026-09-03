from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from kembang.models import Announcement, AnnouncementImage, TentangDesa


class PublicPageTests(TestCase):
    def test_homepage_is_public(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/home.html")

    def test_tentang_is_public(self):
        response = self.client.get(reverse("tentang"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/tentang.html")

    def test_profil_is_public(self):
        response = self.client.get(reverse("profil"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/tentang.html")

    def test_persyaratan_is_public(self):
        response = self.client.get(reverse("persyaratan"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/persyaratan.html")

    def test_public_announcements_show_only_active_items(self):
        active = Announcement.objects.create(
            title="Pengumuman Aktif",
            content="Konten aktif",
            is_active=True,
        )
        inactive = Announcement.objects.create(
            title="Pengumuman Nonaktif",
            content="Konten nonaktif",
            is_active=False,
        )
        AnnouncementImage.objects.create(
            announcement=active,
            image="announcement_images/aktif.jpg",
        )

        response = self.client.get(reverse("announcement_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active.title)
        self.assertNotContains(response, inactive.title)

    def test_public_announcements_empty_state(self):
        response = self.client.get(reverse("announcement_page"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["announcements"],
            Announcement.objects.filter(is_active=True),
            transform=lambda item: item,
        )

    def test_active_announcement_ajax_detail_is_public(self):
        announcement = Announcement.objects.create(
            title="Detail Aktif",
            content="Isi detail",
            is_active=True,
        )

        response = self.client.get(
            reverse("announcement_ajax_detail", args=[announcement.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["html"].count("Detail Aktif"), 1)

    def test_inactive_announcement_ajax_detail_returns_404(self):
        announcement = Announcement.objects.create(
            title="Detail Nonaktif",
            content="Isi detail",
            is_active=False,
        )

        response = self.client.get(
            reverse("announcement_ajax_detail", args=[announcement.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_dashboard_aliases_resolve_to_same_staff_view(self):
        staff = User.objects.create_user(
            username="staff-public",
            password="StaffPass123!",
            is_staff=True,
        )
        self.client.force_login(staff)

        first = self.client.get("/admin-dashboard/")
        second = self.client.get("/dashboard/")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.context["status_summary"], second.context["status_summary"])

    def test_rekap_aliases_resolve_to_same_staff_view(self):
        staff = User.objects.create_user(
            username="staff-rekap",
            password="StaffPass123!",
            is_staff=True,
        )
        self.client.force_login(staff)

        first = self.client.get("/semua/")
        second = self.client.get("/pengajuan/semua-pengajuan/")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(first.context["semua_surat"]), len(second.context["semua_surat"]))

    def test_tentang_empty_data_renders_defaults(self):
        TentangDesa.objects.all().delete()

        response = self.client.get(reverse("tentang"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belum diisi")
