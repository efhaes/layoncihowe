from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from kembang.models import (
    StrukturOrganisasi,
    SKUPengajuan,
    TentangDesa,
)


class ModelBusinessRuleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="model-user")

    def test_sku_uses_nik_when_npwp_is_empty(self):
        sku = SKUPengajuan.objects.create(
            user=self.user,
            nama_lengkap="Pemilik",
            alamat_lengkap="Alamat",
            nik="3201010101010001",
            no_whatsapp="081234567890",
            npwp="",
            surat_pengantar="surat/pengantar.pdf",
            surat_permohonan="surat/permohonan.pdf",
            foto_ktp="foto/ktp.png",
            foto_kk="foto/kk.png",
        )

        self.assertEqual(sku.npwp, sku.nik)

    def test_structure_singleton_slot_rejects_duplicate(self):
        first = StrukturOrganisasi.objects.create(
            nama="Kepala Pertama",
            jabatan="Kepala Desa",
            slot=StrukturOrganisasi.Slot.KEPALA_DESA,
        )
        duplicate = StrukturOrganisasi(
            nama="Kepala Kedua",
            jabatan="Kepala Desa",
            slot=StrukturOrganisasi.Slot.KEPALA_DESA,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        self.assertIsNotNone(first.pk)

    def test_structure_allows_multiple_kepala_dusun(self):
        for number in range(2):
            StrukturOrganisasi.objects.create(
                nama=f"Dusun {number}",
                jabatan="Kepala Dusun",
                slot=StrukturOrganisasi.Slot.KEPALA_WILAYAH,
                urutan=number,
            )

        self.assertEqual(
            StrukturOrganisasi.objects.filter(
                slot=StrukturOrganisasi.Slot.KEPALA_WILAYAH
            ).count(),
            2,
        )

    @patch("kembang.models.requests.get")
    def test_tentang_maps_network_failure_falls_back_to_empty_cache(self, mock_get):
        import requests

        mock_get.side_effect = requests.RequestException("network unavailable")
        tentang = TentangDesa(
            sejarah_singkat="Sejarah",
            potensi_kearifan_lokal="Potensi",
            lokasi_embed_url="https://maps.app.goo.gl/example",
            no_whatsapp="081234567890",
        )

        tentang.save()

        tentang.refresh_from_db()
        self.assertEqual(tentang.lokasi_embed_cache, "")
