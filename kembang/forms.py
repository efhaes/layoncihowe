from django import forms
from .models import SuratKematian, SuratKelahiran, PindahDatang, SKTMPengajuan, DomisiliPengajuan, SKUPengajuan, Announcement, AnnouncementImage, SuratKTPBaruPengantar, SuratKKPengantar, DomisiliUsaha, SuratLainnya,MisiItem, VisiItem, TentangDesa, ProfilDesa, StrukturOrganisasi
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory


WHATSAPP_HELP = "Contoh: 08xxxxxxxxxx atau 628xxxxxxxxxx — nomor aktif, hasil surat dikirim ke sini via WhatsApp."
FILE_HELP = "Format JPG, PNG, atau PDF. Pastikan foto/scan terbaca jelas, tidak buram."


class BaseSuratForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            label = field.label or name.replace('_', ' ').title()

            # Pesan error wajib diisi — Bahasa Indonesia, jelas
            field.error_messages.setdefault('required', f"{label} wajib diisi.")

            # Pesan error khusus file (biar gak nyasar generic juga)
            if isinstance(field, (forms.FileField, forms.ImageField)):
                field.error_messages.setdefault(
                    'invalid', f"{label} bukan file yang valid — coba upload ulang."
                )
                if not field.help_text:
                    field.help_text = FILE_HELP

            # Help text + placeholder default no_whatsapp
            if name == 'no_whatsapp':
                if not field.help_text:
                    field.help_text = WHATSAPP_HELP
                field.widget.attrs.setdefault('placeholder', 'Contoh: 08xxxxxxxxxx')


class SuratKematianForm(BaseSuratForm):
    class Meta:
        model = SuratKematian
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']
        widgets = {
            'tanggal_kematian': forms.DateInput(attrs={'type': 'date'}),
        }


class SuratKelahiranForm(BaseSuratForm):
    class Meta:
        model = SuratKelahiran
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}),
            'alamat': forms.TextInput(attrs={'rows': 2}),
        }


class PindahDatangForm(BaseSuratForm):
    class Meta:
        model = PindahDatang
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']
        widgets = {
            'tanggal_pindah': forms.DateInput(attrs={'type': 'date'}),
            'alasan_pindah': forms.TextInput(attrs={'rows': 2}),
        }


class DomisiliUsahaForm(BaseSuratForm):
    class Meta:
        model = DomisiliUsaha
        fields = [
            'nama_pemilik',
            'nik_pemilik',
            'nama_usaha',
            'jenis_usaha',
            'alamat_usaha',
            'no_whatsapp',
            'nib',
            'fotokopi_ktp',
            'fotokopi_kk',
            'surat_pengantar_rt_rw',
            'foto_lokasi_usaha',
        ]
        widgets = {
            'alamat_usaha': forms.TextInput(attrs={'rows': 3}),
        }


class SKTMPengajuanForm(BaseSuratForm):
    class Meta:
        model = SKTMPengajuan
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']


class DomisiliPengajuanForm(BaseSuratForm):
    class Meta:
        model = DomisiliPengajuan
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']


class SKUPengajuanForm(BaseSuratForm):
    npwp = forms.CharField(
        required=False,
        help_text="Boleh dikosongkan — kalau kosong, otomatis diisi pakai NIK kamu."
    )

    class Meta:
        model = SKUPengajuan
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']


class KTPBaruPengantarForm(BaseSuratForm):
    class Meta:
        model = SuratKTPBaruPengantar
        fields = [
            'nama_lengkap',
            'alamat_lengkap',
            'foto_kk',
            'no_whatsapp',
        ]
        widgets = {
            'alamat_lengkap': forms.TextInput(attrs={'rows': 3}),
        }


class KKPengantarForm(BaseSuratForm):
    class Meta:
        model = SuratKKPengantar
        fields = [
            'nama_lengkap',
            'nik',
            'alamat',
            'foto_kk',
            'ijazah',
            'surat_kelahiran',
            'surat_kematian',
            'no_whatsapp',
        ]
        widgets = {
            'alamat': forms.TextInput(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tiga field ini opsional (tergantung alasan pengantar KK),
        # kasih tau di help text biar gak dikira wajib diisi.
        self.fields['ijazah'].help_text = "Opsional — isi kalau pengajuan karena ubah status pendidikan."
        self.fields['surat_kelahiran'].help_text = "Opsional — isi kalau pengajuan karena tambah anggota keluarga."
        self.fields['surat_kematian'].help_text = "Opsional — isi kalau pengajuan karena kurangi anggota keluarga."


class SuratLainnyaForm(BaseSuratForm):
    class Meta:
        model = SuratLainnya
        fields = [
            'nik',
            'nama_lengkap',
            'alamat_lengkap',
            'foto_ktp',
            'foto_kk',
            'no_whatsapp',
            'jenis_pengajuan',
            'keterangan',
        ]
        widgets = {
            'nik': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_lengkap': forms.TextInput(attrs={'class': 'form-control'}),
            'alamat_lengkap': forms.TextInput(attrs={'class': 'form-control'}),
            'foto_ktp': forms.FileInput(attrs={'class': 'form-control'}),
            'foto_kk': forms.FileInput(attrs={'class': 'form-control'}),
            'no_whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'jenis_pengajuan': forms.TextInput(attrs={'class': 'form-control'}),
            'keterangan': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['jenis_pengajuan'].help_text = "Tulis jenis surat yang kamu butuhkan, misal: Surat Keterangan Belum Menikah."
        self.fields['keterangan'].help_text = "Jelaskan singkat keperluan surat ini."


class RegisterForm(forms.Form):
    nik = forms.CharField(
        max_length=16, label='NIK',
        help_text="16 digit sesuai KTP, tanpa spasi.",
        error_messages={'required': 'NIK wajib diisi.'},
    )
    nama = forms.CharField(
        max_length=100, label='Nama Lengkap',
        error_messages={'required': 'Nama lengkap wajib diisi.'},
    )
    alamat = forms.CharField(
        widget=forms.TextInput(attrs={'rows': 3}), label='Alamat',
        error_messages={'required': 'Alamat wajib diisi.'},
    )
    email = forms.EmailField(
        label='Email',
        error_messages={
            'required': 'Email wajib diisi.',
            'invalid': 'Format email tidak valid, contoh: nama@email.com',
        },
    )
    password = forms.CharField(
        widget=forms.PasswordInput, label='Password',
        help_text="Minimal 8 karakter.",
        error_messages={'required': 'Password wajib diisi.'},
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label='Konfirmasi Password',
        error_messages={'required': 'Konfirmasi password wajib diisi.'},
    )

    def clean_nik(self):
        nik = self.cleaned_data['nik']
        if User.objects.filter(username=nik).exists():
            raise ValidationError("NIK ini sudah terdaftar. Coba masuk (login), atau hubungi admin desa kalau ini bukan kamu.")
        return nik

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password tidak cocok dengan yang di atas.")


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_active']


class AnnouncementImageForm(forms.ModelForm):
    class Meta:
        model = AnnouncementImage
        fields = ['image']


AnnouncementImageFormSet = modelformset_factory(
    AnnouncementImage,
    form=AnnouncementImageForm,
    extra=3,
    can_delete=True
)

# ============================================================================
# TAMBAHKAN class-class form di bawah ini ke forms.py yang sudah ada.
# Pastikan baris import ini juga ada di bagian atas forms.py:
#
#   from .models import TentangDesa, ProfilDesa, StrukturOrganisasi
#
# (VisiItem & MisiItem sengaja TIDAK pakai ModelForm — cukup ditangani
# langsung dari request.POST.get('teks') di view, karena cuma 1 field teks)
# ============================================================================



class TentangDesaForm(forms.ModelForm):
    class Meta:
        model = TentangDesa
        fields = ['sejarah_singkat', 'potensi_kearifan_lokal', 'lokasi_embed_url', 'no_whatsapp']
        widgets = {
            'sejarah_singkat': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6,
                'placeholder': 'Cerita asal-usul nama desa, sejarah singkat, dll.'
            }),
            'potensi_kearifan_lokal': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6,
                'placeholder': 'Potensi alam, sosial-budaya, ekonomi desa.'
            }),
            'lokasi_embed_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://maps.app.goo.gl/xxxxxxx'
            }),
            'no_whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: 08xxxxxxxxxx atau 628xxxxxxxxxx'
            }),
        }
        labels = {
            'sejarah_singkat': 'Sejarah Singkat',
            'potensi_kearifan_lokal': 'Potensi & Kearifan Lokal',
            'lokasi_embed_url': 'Link Share Google Maps',
            'no_whatsapp': 'No. WhatsApp',
        }


class ProfilDesaForm(forms.ModelForm):
    class Meta:
        model = ProfilDesa
        fields = ['foto']
        widgets = {
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'foto': 'Foto Kantor Desa',
        }


class StrukturOrganisasiForm(forms.ModelForm):
    class Meta:
        model = StrukturOrganisasi
        fields = ['nama', 'jabatan', 'slot', 'foto']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama lengkap'}),
            'jabatan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'mis. Kepala Desa'}),
            'slot': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }