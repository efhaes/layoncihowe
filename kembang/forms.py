from django import forms
from .models import SuratKematian, SuratKelahiran, PindahDatang,  SKTMPengajuan, DomisiliPengajuan, SKUPengajuan, Announcement,AnnouncementImage,SuratKTPBaruPengantar,SuratKKPengantar,DomisiliUsaha
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class SuratKematianForm(forms.ModelForm):
    class Meta:
        model = SuratKematian
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']
        widgets = {
            'tanggal_kematian': forms.DateInput(attrs={'type': 'date'}),
        }


class SuratKelahiranForm(forms.ModelForm):
    class Meta:
        model = SuratKelahiran
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}),
            'alamat': forms.TextInput(attrs={'rows': 2}),
        }


class PindahDatangForm(forms.ModelForm):
    class Meta:
        model = PindahDatang
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']
        widgets = {
            'tanggal_pindah': forms.DateInput(attrs={'type': 'date'}),
            'alasan_pindah': forms.TextInput(attrs={'rows': 2}),
        }


class DomisiliUsahaForm(forms.ModelForm):
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
            'no_whatsapp': forms.TextInput(attrs={'placeholder': 'Contoh: 628xxxxx'}),
        }


class SKTMPengajuanForm(forms.ModelForm):
    class Meta:
        model = SKTMPengajuan
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']


class DomisiliPengajuanForm(forms.ModelForm):
    class Meta:
        model = DomisiliPengajuan
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']


class SKUPengajuanForm(forms.ModelForm):
    npwp = forms.CharField(required=False)  # bikin npwp tidak wajib

    class Meta:
        model = SKUPengajuan
        exclude = ['user', 'status', 'hasil_surat', 'tanggal_pengajuan']





class KTPBaruPengantarForm(forms.ModelForm):
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
            'no_whatsapp': forms.TextInput(attrs={'placeholder': 'Contoh: 628xxxxxxx'}),
        }

class KKPengantarForm(forms.ModelForm):
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
            'no_whatsapp': forms.TextInput(attrs={'placeholder': 'Contoh: 628xxxxxxxx'}),
        }


class RegisterForm(forms.Form):
    nik = forms.CharField(max_length=16, label='NIK')
    nama = forms.CharField(max_length=100, label='Nama Lengkap')
    alamat = forms.CharField(widget=forms.TextInput(attrs={'rows': 3}), label='Alamat')
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Konfirmasi Password')

    def clean_nik(self):
        nik = self.cleaned_data['nik']
        if User.objects.filter(username=nik).exists():
            raise ValidationError("NIK sudah terdaftar.")
        return nik

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password tidak cocok.")

from django import forms
from .models import Announcement, AnnouncementImage
from django.forms import modelformset_factory

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_active']

class AnnouncementImageForm(forms.ModelForm):
    class Meta:
        model = AnnouncementImage
        fields = ['image']

# Formset untuk banyak gambar dalam satu pengumuman
AnnouncementImageFormSet = modelformset_factory(
    AnnouncementImage,
    form=AnnouncementImageForm,
    extra=3,  # bisa diatur sesuai kebutuhan
    can_delete=True
)


