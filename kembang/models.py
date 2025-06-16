from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator

STATUS_CHOICES = [
    ('diajukan', 'Diajukan'),
    ('diproses', 'Sedang Diproses'),
    ('selesai', 'Sudah Diproses'),
]


nik = models.CharField(
    max_length=16,
    validators=[
        RegexValidator(r'^[1-9]\d{15}$', message="NIK harus terdiri dari 16 digit angka dan tidak boleh diawali nol")
    ]
)

no_whatsapp = models.CharField(
    max_length=15,
    validators=[
        RegexValidator(
            regex=r'^(?:\+62|62|08)\d{8,13}$',
            message="Nomor WhatsApp harus diawali +62, 62, atau 08 dan terdiri dari 10–15 digit angka"
        )
    ],
    verbose_name="No. WhatsApp"
)


class SuratKematian(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)   
    nama_jenazah = models.CharField(max_length=100)
    nik_jenazah = models.CharField(max_length=16)
    tanggal_kematian = models.DateField()
    tempat_kematian = models.CharField(max_length=100)
    penyebab_kematian = models.CharField(max_length=255, blank=True, null=True)

    nama_pelapor = models.CharField(max_length=100)
    nik_pelapor = models.CharField(max_length=16)
    hubungan_pelapor = models.CharField(max_length=100)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")

    # Upload berkas syarat:
    fotokopi_ktp_jenazah = models.FileField(upload_to='syarat/kematian/ktp_jenazah/', verbose_name="Fotokopi KTP Almarhum/Almarhumah")
    fotokopi_kk = models.FileField(upload_to='syarat/kematian/kk/', verbose_name="Fotokopi Kartu Keluarga")
    surat_keterangan_kematian = models.FileField(upload_to='syarat/kematian/keterangan_kematian/', verbose_name="Surat Keterangan Kematian dari Dokter/Rumah Sakit")
    surat_pengantar_rt_rw = models.FileField(upload_to='syarat/kematian/pengantar_rt_rw/', verbose_name="Surat Pengantar RT/RW")
    fotokopi_ktp_pelapor = models.FileField(upload_to='syarat/kematian/ktp_pelapor/', verbose_name="Fotokopi KTP Pelapor")

    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/akta_kematian/', blank=True, null=True)

    def __str__(self):
        return f"{self.nama_jenazah} - {self.nik_jenazah}"

    
class SuratKelahiran(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    tempat_lahir = models.CharField(max_length=100)
    tanggal_lahir = models.DateField()
    jenis_kelamin = models.CharField(max_length=10, choices=[('L', 'Laki-laki'), ('P', 'Perempuan')])
    nama_ayah = models.CharField(max_length=100)
    nama_ibu = models.CharField(max_length=100)
    alamat = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    no_whatsapp = models.CharField(max_length=15,  verbose_name="No. WhatsApp") 
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)

    surat_keterangan_lahir = models.FileField(upload_to='syarat/kelahiran/surat_keterangan/', verbose_name="Surat Keterangan Lahir dari RS/Bidan")
    fotokopi_ktp_kk = models.FileField(upload_to='syarat/kelahiran/ktp_kk/', verbose_name="Fotokopi KTP dan KK Orang Tua")
    fotokopi_buku_nikah = models.FileField(upload_to='syarat/kelahiran/buku_nikah/', verbose_name="Fotokopi Buku Nikah Orang Tua")
    surat_pengantar_rt_rw = models.FileField(upload_to='syarat/kelahiran/pengantar_rt_rw/', verbose_name="Surat Pengantar RT/RW")

    hasil_surat = models.FileField(upload_to='hasil_surat/akta_kelahiran/', blank=True, null=True)

    def __str__(self):
        return f'Akta Kelahiran {self.nama_lengkap}'


class DomisiliUsaha(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_pemilik = models.CharField(max_length=100)
    nik_pemilik = models.CharField(max_length=16)
    nama_usaha = models.CharField(max_length=100)
    jenis_usaha = models.CharField(max_length=100)
    alamat_usaha = models.CharField(max_length=100)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")

    # Upload syarat:
    nib = models.FileField(upload_to='domisili_usaha/nib/', verbose_name="NIB")
    fotokopi_ktp = models.FileField(upload_to='domisili_usaha/KTP/', verbose_name="Fotokopi KTP")
    surat_pengantar_rt_rw = models.FileField(upload_to='domisili_usaha/pengantar_rt_rw/', verbose_name="Surat Pengantar RT/RW")
    fotokopi_kk = models.FileField(upload_to='domisili_usaha/KK/', verbose_name="Fotokopi KK")
    foto_lokasi_usaha = models.FileField(upload_to='domisili_usaha/foto_lokasi/', verbose_name="Foto Lokasi Usaha")

    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/domisili_usaha/', blank=True, null=True)

    def __str__(self):
        return f"Domisili Usaha - {self.nama_usaha} ({self.nama_pemilik})"




class PindahDatang(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)
    nik = models.CharField(max_length=16, )
    asal_daerah = models.CharField(max_length=100)
    tujuan_daerah = models.CharField(max_length=100)
    tanggal_pindah = models.DateField()
    alasan_pindah = models.CharField(max_length=200)
    kk_lama = models.FileField(upload_to='pindah_datang/kk_lama/')
    ktp = models.FileField(upload_to='pindah_datang/ktp/')
    surat_pengantar = models.FileField(upload_to='pindah_datang/surat_pengantar/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")  # tambahkan ini
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    hasil_surat = models.FileField(upload_to='hasil_surat/pindah_datang/', blank=True, null=True)


    def __str__(self):
        return f"Pindah Datang - {self.nama} ({self.nik})"





class SKTMPengajuan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    nik = models.CharField(max_length=16)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")

    # Berkas wajib
    surat_pengantar = models.FileField(upload_to='sktm/surat_pengantar/', verbose_name="Surat Pengantar RT/RW")
    foto_ktp = models.ImageField(upload_to='sktm/foto_ktp/', verbose_name="Fotokopi KTP")
    foto_kk = models.ImageField(upload_to='sktm/foto_kk/', verbose_name="Fotokopi Kartu Keluarga")
    surat_pernyataan = models.FileField(upload_to='sktm/surat_pernyataan/', verbose_name="Surat Pernyataan Tidak Mampu")

    # Berkas opsional (bergantung tujuan)
    surat_keterangan_sekolah = models.FileField(upload_to='sktm/keterangan_sekolah/', blank=True, null=True, verbose_name="Surat Keterangan Sekolah")
    surat_keterangan_usaha = models.FileField(upload_to='sktm/keterangan_usaha/', blank=True, null=True, verbose_name="Surat Keterangan Usaha / NIB")

    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='sktm/hasil_surat/', blank=True, null=True)

    def __str__(self):
        return f"SKTM - {self.nama_lengkap} ({self.nik})"

    


    
class DomisiliPengajuan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    nik = models.CharField(max_length=16)
    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")

    surat_pengantar = models.FileField(upload_to='domisili/surat_pengantar/')
    foto_ktp = models.ImageField(upload_to='domisili/foto_ktp/')
    foto_kk = models.ImageField(upload_to='domisili/foto_kk/')
    surat_permohonan = models.FileField(upload_to='domisili/surat_permohonan/')
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='domisili/hasil_surat/', blank=True, null=True)
    

    def __str__(self):
        return f"{self.nama_lengkap} - {self.nik}"

class SKUPengajuan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    nik = models.CharField(max_length=16)
    no_whatsapp = models.CharField(max_length=15,verbose_name="No. WhatsApp")
    npwp = models.CharField(max_length=50, blank=True, null=True)  # jadi bisa kosong
    surat_pengantar = models.FileField(upload_to='SKU/surat_pengantar/')
    surat_permohonan = models.FileField(upload_to='SKU/surat_permohonan/')
    foto_ktp = models.ImageField(upload_to='SKU/foto_ktp/')
    foto_kk = models.ImageField(upload_to='SKU/foto_kk/')
    surat_kuasa = models.ImageField(upload_to='SKU/surat_kuasa/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='SKU/hasil_surat/', blank=True, null=True)
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.npwp:  # Jika npwp kosong
            self.npwp = self.nik  # otomatis isi dengan nik
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nama_lengkap} - {self.nik}"


class SuratKTPBaruPengantar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    alamat_lengkap = models.CharField(max_length=200)
    foto_kk = models.ImageField(upload_to='ktp_baru/foto_kk/', verbose_name="Foto Kartu Keluarga")

    no_whatsapp = models.CharField(max_length=15, verbose_name="No. WhatsApp")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/ktp_baru/', blank=True, null=True)

    def __str__(self):
        return f"KTP Baru - {self.nama_lengkap}"

class SuratKKPengantar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=100)
    nik = models.CharField(max_length=16)
    alamat = models.CharField(max_length=200)

    foto_kk = models.ImageField(upload_to='kk_pengantar/foto_kk/', verbose_name="Foto Kartu Keluarga")

    # Dokumen opsional
    ijazah = models.FileField(upload_to='kk_pengantar/ijazah/', blank=True, null=True, verbose_name="Ijazah (Jika ubah status pendidikan)")
    surat_kelahiran = models.FileField(upload_to='kk_pengantar/surat_kelahiran/', blank=True, null=True, verbose_name="Surat Kelahiran (Jika tambah anggota keluarga)")
    surat_kematian = models.FileField(upload_to='kk_pengantar/surat_kematian/', blank=True, null=True, verbose_name="Surat Kematian (Jika kurangi anggota keluarga)")

    no_whatsapp = models.CharField(max_length=15,verbose_name="No. WhatsApp")
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='diajukan')
    hasil_surat = models.FileField(upload_to='hasil_surat/kk_pengantar/', blank=True, null=True)

    def __str__(self):
        return f"Pengantar KK - {self.nama_lengkap} ({self.nik})"





class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)
    alamat = models.CharField(max_length=100)

    def __str__(self):
        return self.nama
    

class Announcement(models.Model):
    title = models.CharField(max_length=200)             
    content = models.CharField(max_length=300)                        
    published_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)        
    is_active = models.BooleanField(default=True)           

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at']   # pengumuman terbaru muncul paling atas
        verbose_name = "Pengumuman"
        verbose_name_plural = "Pengumuman"



class AnnouncementImage(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='announcement_images/')

    def __str__(self):
        return f"Gambar untuk {self.announcement.title}"
