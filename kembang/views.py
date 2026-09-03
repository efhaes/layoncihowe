import json
from datetime import datetime, timedelta
from collections import defaultdict
from itertools import chain

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST


from .models import (
    SuratKematian, SuratKelahiran, PindahDatang, UserProfile,
    SKTMPengajuan, Announcement, AnnouncementImage, SuratKKPengantar,
    SuratKTPBaruPengantar, DomisiliUsaha, SuratLainnya,
    DomisiliPengajuan, SKUPengajuan, ProfilDesa, TentangDesa, StrukturOrganisasi,VisiItem, MisiItem
)
from .forms import (
    SuratKematianForm, SuratKelahiranForm, PindahDatangForm, SKUPengajuanForm,
    AnnouncementForm, AnnouncementImageForm, AnnouncementImageFormSet,
    KTPBaruPengantarForm, KKPengantarForm, DomisiliUsahaForm, SuratLainnyaForm,
    RegisterForm, SKTMPengajuanForm, DomisiliPengajuanForm, TentangDesaForm, ProfilDesaForm, StrukturOrganisasiForm
)
import json as json_lib
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from .models import ChatThread, ChatMessage, UserEncryptionKey, DesaEncryptionKey





def is_admin(user):
    return user.is_authenticated and user.is_staff


staff_required = user_passes_test(is_admin, login_url='login')

# Whitelist model yang BOLEH dihapus lewat view generik `hapus_surat`.
# INI PERBAIKAN KEAMANAN UTAMA — lihat penjelasan di bawah fungsinya.
SURAT_MODEL_WHITELIST = {
    'suratkematian': SuratKematian,
    'suratkelahiran': SuratKelahiran,
    'domisiliusaha': DomisiliUsaha,
    'pindahdatang': PindahDatang,
    'sktmpengajuan': SKTMPengajuan,
    'domisilipengajuan': DomisiliPengajuan,
    'skupengajuan': SKUPengajuan,
    'suratktpbarupengantar': SuratKTPBaruPengantar,
    'suratkkpengantar': SuratKKPengantar,
    'suratlainnya': SuratLainnya,
}


def get_tanggal(obj):
    return (
        getattr(obj, 'tanggal_pengajuan', None) or
        getattr(obj, 'tanggal', None) or
        getattr(obj, 'tanggal_dibuat', None) or
        datetime.min
    )


def get_nama_pemohon(obj):
    return (
        getattr(obj, 'nama_lengkap', None) or
        getattr(obj, 'nama_pemilik', None) or
        getattr(obj, 'nama_jenazah', None) or
        getattr(obj, 'nama', None) or
        str(obj)
    )


# =========================================================================
# HALAMAN PUBLIK / PROFIL
# =========================================================================

def persyaratan(request):
    return render(request, 'profile/persyaratan.html')


def logout_view(request):
    logout(request)
    return redirect('home')

def _geser_urutan(queryset, item_id, arah):
    """
    Tukar posisi field `urutan` antara item_id dengan tetangganya
    (naik/turun) di dalam queryset yang sama.

    queryset harus berisi item-item yang urutannya saling berkaitan —
    mis. semua VisiItem milik TentangDesa yang sama, atau semua
    StrukturOrganisasi dengan slot yang sama (supaya swap urutan gak
    nyampur antar grup slot yang berbeda).
    """
    items = list(queryset.order_by('urutan'))
    try:
        index = next(i for i, obj in enumerate(items) if str(obj.pk) == str(item_id))
    except StopIteration:
        return

    if arah == 'naik' and index > 0:
        tukar_dengan = index - 1
    elif arah == 'turun' and index < len(items) - 1:
        tukar_dengan = index + 1
    else:
        return

    a, b = items[index], items[tukar_dengan]
    a.urutan, b.urutan = b.urutan, a.urutan
    a.save(update_fields=['urutan'])
    b.save(update_fields=['urutan'])


@login_required
@staff_required
def kelola_tentang_desa(request):
    tentang = TentangDesa.load()
    profil_desa = ProfilDesa.load()

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- Info utama (sejarah, potensi, link maps) ---
        if action == 'update_info':
            form = TentangDesaForm(request.POST, instance=tentang)
            if form.is_valid():
                form.save()
                messages.success(request, "Info Tentang Desa berhasil diperbarui.")
            else:
                messages.error(request, "Gagal menyimpan: periksa kembali form.")
            return redirect('kelola_tentang')

        # --- Foto kantor desa (singleton) ---
        elif action == 'update_foto':
            form = ProfilDesaForm(request.POST, request.FILES, instance=profil_desa)
            if form.is_valid():
                form.save()
                messages.success(request, "Foto kantor desa berhasil diperbarui.")
            else:
                messages.error(request, "Gagal upload foto: periksa kembali file yang diunggah.")
            return redirect('kelola_tentang')

        # --- Visi ---
        elif action == 'visi_add':
            teks = (request.POST.get('teks') or '').strip()
            if teks:
                VisiItem.objects.create(tentang=tentang, teks=teks, urutan=tentang.visi_items.count())
                messages.success(request, "Poin visi berhasil ditambahkan.")
            else:
                messages.error(request, "Teks visi tidak boleh kosong.")
            return redirect('kelola_tentang')

        elif action == 'visi_edit':
            item = get_object_or_404(VisiItem, pk=request.POST.get('item_id'), tentang=tentang)
            teks = (request.POST.get('teks') or '').strip()
            if teks:
                item.teks = teks
                item.save()
                messages.success(request, "Poin visi berhasil diperbarui.")
            else:
                messages.error(request, "Teks visi tidak boleh kosong.")
            return redirect('kelola_tentang')

        elif action == 'visi_delete':
            item = get_object_or_404(VisiItem, pk=request.POST.get('item_id'), tentang=tentang)
            item.delete()
            messages.success(request, "Poin visi berhasil dihapus.")
            return redirect('kelola_tentang')

        elif action == 'visi_move':
            _geser_urutan(tentang.visi_items, request.POST.get('item_id'), request.POST.get('arah'))
            return redirect('kelola_tentang')

        # --- Misi ---
        elif action == 'misi_add':
            teks = (request.POST.get('teks') or '').strip()
            if teks:
                MisiItem.objects.create(tentang=tentang, teks=teks, urutan=tentang.misi_items.count())
                messages.success(request, "Poin misi berhasil ditambahkan.")
            else:
                messages.error(request, "Teks misi tidak boleh kosong.")
            return redirect('kelola_tentang')

        elif action == 'misi_edit':
            item = get_object_or_404(MisiItem, pk=request.POST.get('item_id'), tentang=tentang)
            teks = (request.POST.get('teks') or '').strip()
            if teks:
                item.teks = teks
                item.save()
                messages.success(request, "Poin misi berhasil diperbarui.")
            else:
                messages.error(request, "Teks misi tidak boleh kosong.")
            return redirect('kelola_tentang')

        elif action == 'misi_delete':
            item = get_object_or_404(MisiItem, pk=request.POST.get('item_id'), tentang=tentang)
            item.delete()
            messages.success(request, "Poin misi berhasil dihapus.")
            return redirect('kelola_tentang')

        elif action == 'misi_move':
            _geser_urutan(tentang.misi_items, request.POST.get('item_id'), request.POST.get('arah'))
            return redirect('kelola_tentang')

        # --- Struktur organisasi ---
        elif action == 'struktur_save':
            struktur_id = request.POST.get('struktur_id')
            instance = get_object_or_404(StrukturOrganisasi, pk=struktur_id) if struktur_id else None
            form = StrukturOrganisasiForm(request.POST, request.FILES, instance=instance)
            if form.is_valid():
                obj = form.save(commit=False)
                if not struktur_id:
                    obj.urutan = StrukturOrganisasi.objects.filter(slot=obj.slot).count()
                obj.save()
                messages.success(request, "Data struktur organisasi berhasil disimpan.")
            else:
                # Kalau slot singleton (mis. Kepala Desa) udah keisi, error-nya
                # muncul otomatis di form.errors['slot'] lewat clean() model.
                pesan_error = "; ".join(
                    f"{field}: {', '.join(errs)}" for field, errs in form.errors.items()
                )
                messages.error(request, f"Gagal menyimpan: {pesan_error}")
            return redirect('kelola_tentang')

        elif action == 'struktur_delete':
            item = get_object_or_404(StrukturOrganisasi, pk=request.POST.get('item_id'))
            item.delete()
            messages.success(request, "Data struktur organisasi berhasil dihapus.")
            return redirect('kelola_tentang')

        elif action == 'struktur_move':
            item = get_object_or_404(StrukturOrganisasi, pk=request.POST.get('item_id'))
            grup_slot = StrukturOrganisasi.objects.filter(slot=item.slot)
            _geser_urutan(grup_slot, request.POST.get('item_id'), request.POST.get('arah'))
            return redirect('kelola_tentang')

        messages.error(request, "Aksi tidak dikenali.")
        return redirect('kelola_tentang')

    context = {
        'tentang': tentang,
        'profil_desa': profil_desa,
        'tentang_form': TentangDesaForm(instance=tentang),
        'profil_desa_form': ProfilDesaForm(instance=profil_desa),
        'struktur_form': StrukturOrganisasiForm(),
        'struktur_list': StrukturOrganisasi.objects.all(),
    }
    return render(request, 'admin/kelola_tentang.html', context)

def tentang(request):
    S = StrukturOrganisasi.Slot

    def satu(slot):
        return StrukturOrganisasi.objects.filter(slot=slot).first()

    def banyak(slot):
        return StrukturOrganisasi.objects.filter(slot=slot)

    return render(request, "profile/tentang.html", {
        "tentang": TentangDesa.load(),
        "bpd": satu(S.BPD),
        "kepala_desa": satu(S.KEPALA_DESA),
        "sekretaris_desa": satu(S.SEKRETARIS_DESA),
        "kasi_pemerintahan": satu(S.KASI_PEMERINTAHAN),
        "kasi_kesejahteraan": satu(S.KASI_KESEJAHTERAAN),
        "kasi_pelayanan": satu(S.KASI_PELAYANAN),
        "kaur_tatausahadannumum": satu(S.KAUR_TATAUSAHADANUMUM),
        "kaur_keuangan": satu(S.KAUR_KEUANGAN),
        "kaur_perencanaan": satu(S.KAUR_PERENCANAAN),
        "kepala_wilayah": banyak(S.KEPALA_WILAYAH),
    })


def profil(request):
    return render(request, 'profile/profil.html')


def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    notifikasi = {
        'kelahiran': SuratKelahiran.objects.filter(status='diajukan').count(),
        'kematian': SuratKematian.objects.filter(status='diajukan').count(),
        'pindah': PindahDatang.objects.filter(status='diajukan').count(),
        'sku': SKUPengajuan.objects.filter(status='diajukan').count(),
        'sktm': SKTMPengajuan.objects.filter(status='diajukan').count(),
        'domisili': DomisiliPengajuan.objects.filter(status='diajukan').count(),
        'skdu': DomisiliUsaha.objects.filter(status='diajukan').count(),
        'kk': SuratKKPengantar.objects.filter(status='diajukan').count(),
        'ktp': SuratKTPBaruPengantar.objects.filter(status='diajukan').count(),
        'lainnya': SuratLainnya.objects.filter(status='diajukan').count(),
    }
    notifikasi['total'] = sum(notifikasi.values())

    announcements = Announcement.objects.filter(is_active=True).order_by('-published_at')[:5]

    return render(request, 'profile/home.html', {
        'notifikasi': notifikasi,
        'announcements': announcements,
        'profil_desa': ProfilDesa.load(),
    })


# =========================================================================
# AUTH
# =========================================================================

def login_view(request):
    if request.method == 'POST':
        nik = (request.POST.get('nik') or '').strip()
        password = request.POST.get('password') or ''

        # Pesan error digeneralisir ("NIK atau password salah") supaya tidak
        # bisa dipakai menebak NIK mana yang terdaftar (user enumeration).
        user = authenticate(request, username=nik, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_dashboard' if user.is_staff else 'home')

        messages.error(request, 'NIK atau password salah')
        return redirect('login')

    return render(request, 'surat/login.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            nik = form.cleaned_data['nik']
            nama = form.cleaned_data['nama']
            alamat = form.cleaned_data['alamat']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if User.objects.filter(username=nik).exists():
                messages.error(request, "NIK sudah terdaftar.")
                return render(request, 'profile/register.html', {'form': form})

            user = User.objects.create(
                username=nik,
                email=email,
                password=make_password(password),  # password sudah di-hash, bagus
            )
            UserProfile.objects.create(user=user, nama=nama, alamat=alamat)

            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'profile/register.html', {'form': form})



from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

# =========================================================================
# KELOLA AKUN WARGA — reset password untuk warga yang lupa akunnya
# =========================================================================

@login_required
@staff_required
def kelola_akun_warga(request):
    warga = UserProfile.objects.select_related('user').order_by('nama')
    return render(request, 'admin/kelola_akun_warga.html', {'warga': warga})


@login_required
@staff_required
@require_POST
def reset_password_warga(request, user_id):
    """
    Staff mengganti password akun warga (mis. warga lupa password-nya
    dan gak ada jalur "lupa password" mandiri karena sistem ini gak
    pakai email/OTP). is_staff=False memastikan endpoint ini gak bisa
    dipakai buat reset password sesama staff/admin.
    """
    target_user = get_object_or_404(User, pk=user_id, is_staff=False)
    password_baru = request.POST.get('password_baru', '')
    password_konfirmasi = request.POST.get('password_konfirmasi', '')

    if password_baru != password_konfirmasi:
        messages.error(request, "Konfirmasi password tidak cocok.")
        return redirect('kelola_akun_warga')

    try:
        validate_password(password_baru, user=target_user)
    except DjangoValidationError as e:
        messages.error(request, " ".join(e.messages))
        return redirect('kelola_akun_warga')

    target_user.set_password(password_baru)
    target_user.save()

    nama_tampil = getattr(target_user, 'userprofile', None)
    nama_tampil = nama_tampil.nama if nama_tampil else target_user.username
    messages.success(request, f"Password untuk {nama_tampil} berhasil diganti.")
    return redirect('kelola_akun_warga')

# =========================================================================
# DASHBOARD ADMIN
# (Sebelumnya `admin_dashboard` didefinisikan 2x dan `semua_pengajuan` 3x —
#  definisi belakangan diam-diam menimpa yang pertama, jadi statistik/grafik
#  di versi pertama sebenarnya tidak pernah kepakai. Sudah digabung jadi satu.)
# =========================================================================

@login_required
@staff_required
def admin_dashboard(request):
    akta_kelahiran = SuratKelahiran.objects.all()
    akta_kematian = SuratKematian.objects.all()
    pindah_datang = PindahDatang.objects.all()
    pindah_keluar = DomisiliUsaha.objects.all()
    sku = SKUPengajuan.objects.all()
    domisili = DomisiliPengajuan.objects.all()
    sktm = SKTMPengajuan.objects.all()
    kk = SuratKKPengantar.objects.all()
    ktp = SuratKTPBaruPengantar.objects.all()
    lainnya = SuratLainnya.objects.all()

    notifikasi = {
        'kelahiran': akta_kelahiran.filter(status='diajukan').count(),
        'kematian': akta_kematian.filter(status='diajukan').count(),
        'pindah': pindah_datang.filter(status='diajukan').count(),
        'skdu': pindah_keluar.filter(status='diajukan').count(),
        'sku': sku.filter(status='diajukan').count(),
        'domisili': domisili.filter(status='diajukan').count(),
        'sktm': sktm.filter(status='diajukan').count(),
        'kk': kk.filter(status='diajukan').count(),
        'ktp': ktp.filter(status='diajukan').count(),
        'lainnya': lainnya.filter(status='diajukan').count(),
    }
    notifikasi['total'] = sum(notifikasi.values())

    semua = list(chain(
        akta_kelahiran, pindah_datang, pindah_keluar, akta_kematian,
        sku, domisili, sktm, kk, ktp, lainnya,
    ))

    jenis_map = {
        SuratKelahiran: 'Surat Kelahiran',
        PindahDatang: 'Pindah Datang',
        DomisiliUsaha: 'SKDU',
        SuratKematian: 'Surat Kematian',
        SKUPengajuan: 'SKU',
        DomisiliPengajuan: 'Surat Domisili',
        SKTMPengajuan: 'SKTM',
        SuratKKPengantar: 'Pengantar KK',
        SuratKTPBaruPengantar: 'Pengantar KTP',
        SuratLainnya: 'Surat Lainnya',
    }

    status_summary = {'diajukan': 0, 'diproses': 0, 'selesai': 0}
    monthly_counts = defaultdict(int)
    yearly_counts = defaultdict(int)

    for obj in semua:
        obj.jenis_surat = jenis_map.get(type(obj), 'Lainnya')
        obj.nama_tampil = get_nama_pemohon(obj)
        status_summary[obj.status] = status_summary.get(obj.status, 0) + 1

        tgl = get_tanggal(obj)
        if tgl and tgl != datetime.min:
            monthly_counts[(tgl.year, tgl.month)] += 1
            yearly_counts[tgl.year] += 1

    belum_selesai_total = status_summary.get('diajukan', 0) + status_summary.get('diproses', 0)

    semua.sort(key=get_tanggal, reverse=True)
    recent_pengajuan = semua[:8]

    current_year = datetime.now().year
    tahun_terdata = sorted(yearly_counts.keys())
    tahun_pilihan = sorted(set(tahun_terdata + [current_year]), reverse=True)

    try:
        tahun_dipilih = int(request.GET.get('tahun', current_year))
    except (TypeError, ValueError):
        tahun_dipilih = current_year

    if tahun_dipilih not in tahun_pilihan:
        tahun_pilihan.append(tahun_dipilih)
        tahun_pilihan.sort(reverse=True)

    bulan_label = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                   'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    data_bulanan = [monthly_counts.get((tahun_dipilih, m), 0) for m in range(1, 13)]

    tahun_range = list(range(tahun_terdata[0], current_year + 1)) if tahun_terdata else [current_year]
    data_tahunan = [yearly_counts.get(y, 0) for y in tahun_range]

    context = {
        'akta_kelahiran': akta_kelahiran,
        'akta_kematian': akta_kematian,
        'pindah_datang': pindah_datang,
        'pindah_keluar': pindah_keluar,
        'sku': sku,
        'domisili': domisili,
        'sktm': sktm,
        'kk': kk,
        'ktp': ktp,
        'lainnya': lainnya,
        'notifikasi': notifikasi,
        'semua_pengajuan': semua,
        'recent_pengajuan': recent_pengajuan,
        'status_summary': status_summary,
        'belum_selesai_total': belum_selesai_total,
        'bulan_labels_json': json.dumps(bulan_label),
        'bulan_data_json': json.dumps(data_bulanan),
        'tahun_labels_json': json.dumps(tahun_range),
        'tahun_data_json': json.dumps(data_tahunan),
        'tahun_ini': current_year,
        'tahun_dipilih': tahun_dipilih,
        'tahun_pilihan': tahun_pilihan,
    }
    return render(request, 'admin/dashboard.html', context)


# =========================================================================
# HELPER — dipakai di semua_pengajuan
# =========================================================================

def get_nama(obj):
    for field in ['nama_lengkap', 'nama', 'nama_pemilik', 'nama_jenazah', 'nama_usaha']:
        value = getattr(obj, field, None)
        if value:
            return value
    return "Tidak tersedia"


def get_nik(obj):
    """
    NIK warga yang mengajukan surat = username akun dia (lihat `register()`,
    NIK disimpan sebagai `User.username`). Ini dipakai, BUKAN field nik_*
    di masing-masing model surat — soalnya field itu beda-beda artinya
    per model (mis. nik_jenazah di SuratKematian itu NIK almarhum, bukan
    NIK pelapor) dan dua model (SuratKelahiran, SuratKTPBaruPengantar)
    malah sama sekali gak punya field NIK sendiri.
    """
    return obj.user.username if obj.user_id else ""


# =========================================================================
# SEMUA PENGAJUAN (rekap gabungan + filter tahun)
# =========================================================================

@login_required
@staff_required
def semua_pengajuan(request):
    """Daftar gabungan semua jenis pengajuan surat (khusus admin)."""

    def tandai(queryset, nama_surat):
        ct = ContentType.objects.get_for_model(queryset.model)
        result = list(queryset.select_related('user'))
        for obj in result:
            obj.jenis_surat = nama_surat
            obj.model_name = ct.model
            obj.nama_display = get_nama(obj)
            obj.nik_display = get_nik(obj)
        return result

    semua_surat = (
        tandai(SuratKematian.objects.all(), "Surat Kematian") +
        tandai(SuratKelahiran.objects.all(), "Surat Kelahiran") +
        tandai(DomisiliUsaha.objects.all(), "Surat Domisili Usaha") +
        tandai(PindahDatang.objects.all(), "Surat Pindah Datang") +
        tandai(SKTMPengajuan.objects.all(), "Surat Keterangan Tidak Mampu") +
        tandai(DomisiliPengajuan.objects.all(), "Surat Domisili") +
        tandai(SKUPengajuan.objects.all(), "Surat Keterangan Usaha") +
        tandai(SuratKTPBaruPengantar.objects.all(), "Surat Pengantar KTP") +
        tandai(SuratKKPengantar.objects.all(), "Surat Pengantar KK") +
        tandai(SuratLainnya.objects.all(), "Surat Lainnya")
    )
    semua_surat.sort(key=get_tanggal, reverse=True)

    # --- Kartu filter Tahun Pengajuan ---
    tahun_set = set()
    for obj in semua_surat:
        tgl = get_tanggal(obj)
        if tgl and tgl != datetime.min:
            tahun_set.add(tgl.year)
    tahun_list = sorted(tahun_set, reverse=True)

    tahun_dipilih = request.GET.get('tahun')
    if tahun_dipilih:
        try:
            tahun_dipilih = int(tahun_dipilih)
        except ValueError:
            tahun_dipilih = None

    if tahun_dipilih:
        semua_surat = [
            obj for obj in semua_surat
            if get_tanggal(obj) != datetime.min and get_tanggal(obj).year == tahun_dipilih
        ]

    return render(request, 'surat/semua_pengajuan.html', {
        'semua_surat': semua_surat,
        'tahun_list': tahun_list,
        'tahun_dipilih': tahun_dipilih,
    })

@login_required
@staff_required
@require_POST
def hapus_surat(request, model, pk):
    model_class = SURAT_MODEL_WHITELIST.get(model.lower())
    if model_class is None:
        return HttpResponseForbidden("Jenis surat tidak dikenali.")

    obj = get_object_or_404(model_class, pk=pk)
    obj.delete()
    messages.success(request, "Pengajuan berhasil dihapus.")
    return redirect('semua_pengajuan')


@login_required
@staff_required
@require_POST
def hapus_semua_pengajuan(request):
    """Menghapus SELURUH data pengajuan. Sangat merusak — pastikan ada
    konfirmasi eksplisit (mis. checkbox/modal "saya yakin") di templatenya."""
    total_dihapus = 0
    for model in SURAT_MODEL_WHITELIST.values():
        count = model.objects.count()
        model.objects.all().delete()
        total_dihapus += count

    messages.success(request, f"{total_dihapus} pengajuan berhasil dihapus.")
    return redirect('semua_pengajuan')


# =========================================================================
# SURAT KEMATIAN
# =========================================================================

@login_required
def pengajuan_akta_kematian(request):
    if request.method == 'POST':
        sudah_ada = SuratKematian.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_kematian')
            return redirect('pengajuan_akta_kematian')

        form = SuratKematianForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_kematian')
            return redirect('pengajuan_akta_kematian')
    else:
        form = SuratKematianForm()

    return render(request, 'surat/aktakematian_form.html', {'form': form})


@login_required
@staff_required
def daftar_pengajuan_akta_kematian(request):
    daftar = SuratKematian.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_kematian.html', {'daftar': daftar})


@login_required
@staff_required
@require_POST
def hapus_kematian(request, pk):
    daftar = get_object_or_404(SuratKematian, pk=pk)
    daftar.delete()
    return redirect('daftar_pengajuan_akta_kematian')


@login_required
@staff_required
def detail_pengajuan_akta_kematian(request, pk):
    akta = get_object_or_404(SuratKematian, pk=pk)
    if request.method == 'POST':
        akta.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            akta.hasil_surat = hasil_surat
        akta.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_akta_kematian', pk=pk)

    return render(request, 'admin/akta_kematian_detail.html', {'akta': akta})


# =========================================================================
# SURAT KELAHIRAN
# =========================================================================

@login_required
def pengajuan_akta_kelahiran(request):
    if request.method == 'POST':
        sudah_ada = SuratKelahiran.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_kelahiran')
            return redirect('pengajuan_akta_kelahiran')

        form = SuratKelahiranForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_kelahiran')
            return redirect('pengajuan_akta_kelahiran')
    else:
        form = SuratKelahiranForm()

    return render(request, 'surat/akta_kelahiran_form.html', {'form': form})


@login_required
@staff_required
def daftar_pengajuan_kelahiran(request):
    pengajuan = SuratKelahiran.objects.select_related('user').all().order_by('-tanggal_lahir')
    return render(request, 'admin/daftar_kelahiran.html', {'pengajuan': pengajuan})

@login_required
@staff_required
@require_POST
def hapus_kelahiran(request, pk):
    pengajuan = get_object_or_404(SuratKelahiran, pk=pk)
    pengajuan.delete()
    return redirect('daftar_pengajuan_kelahiran')

@login_required
@staff_required
def detail_pengajuan_kelahiran(request, pk):
    akta = get_object_or_404(SuratKelahiran, pk=pk)
    if request.method == 'POST':
        akta.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            akta.hasil_surat = hasil_surat
        akta.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_kelahiran', pk=pk)
    return render(request, 'admin/detail_kelahiran.html', {'akta': akta})


# =========================================================================
# PINDAH DATANG
# =========================================================================

@login_required
def pengajuan_pindah_datang(request):
    if request.method == 'POST':
        sudah_ada = PindahDatang.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_datang')
            return redirect('pengajuan_pindah_datang')

        form = PindahDatangForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_datang')
            return redirect('pengajuan_pindah_datang')
    else:
        form = PindahDatangForm()

    return render(request, 'surat/datang_form.html', {'form': form})


@login_required
@staff_required
def daftar_pindah_datang(request):
    pengajuan = PindahDatang.objects.select_related('user').all().order_by('-tanggal_pindah')
    return render(request, 'admin/daftar_datang.html', {'daftar': pengajuan})


@login_required
@staff_required
@require_POST
def hapus_pindah_datang(request, pk):
    pengajuan = get_object_or_404(PindahDatang, pk=pk)
    pengajuan.delete()
    return redirect('daftar_pengajuan_pindah_datang') 


@login_required
@staff_required
def detail_pindah_datang(request, pk):
    datang = get_object_or_404(PindahDatang, pk=pk)
    if request.method == 'POST':
        datang.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            datang.hasil_surat = hasil_surat
        datang.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_pindah_datang', pk=pk)
    return render(request, 'admin/detail_datang.html', {'datang': datang})

# =========================================================================
# DOMISILI USAHA (SKDU)
# =========================================================================

@login_required
def pengajuan_domisili_usaha(request):
    if request.method == 'POST':
        sudah_ada = DomisiliUsaha.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_keluar')
            return redirect('pengajuan_skdu')

        form = DomisiliUsahaForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_keluar')
            return redirect('pengajuan_skdu')
    else:
        form = DomisiliUsahaForm()

    return render(request, 'surat/domisili_usaha_form.html', {'form': form})


@login_required
@staff_required
def daftar_domisili_usaha(request):
    pengajuan = DomisiliUsaha.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_domisili_usaha.html', {'daftar': pengajuan})

@login_required
@staff_required
@require_POST
def hapus_domisili_usaha(request, pk):
    pengajuan = get_object_or_404(DomisiliUsaha, pk=pk)
    pengajuan.delete()
    return redirect('daftar_pengajuan_skdu')


@login_required
@staff_required
def detail_domisili_usaha(request, pk):
    pengajuan = get_object_or_404(DomisiliUsaha, pk=pk)
    if request.method == 'POST':
        pengajuan.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            pengajuan.hasil_surat = hasil_surat
        pengajuan.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_skdu', pk=pk)
    return render(request, 'admin/detail_skdu.html', {'pengajuan': pengajuan})


# =========================================================================
# SKTM
# =========================================================================

@login_required
def pengajuan_sktm(request):
    if request.method == 'POST':
        sudah_ada = SKTMPengajuan.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_sktm')
            return redirect('pengajuan_sktm')

        form = SKTMPengajuanForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_sktm')
            return redirect('pengajuan_sktm')
    else:
        form = SKTMPengajuanForm()

    return render(request, 'surat/sktm_form.html', {'form': form})


@login_required
@staff_required
def daftar_sktm(request):
    daftar = SKTMPengajuan.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_sktm.html', {'daftar': daftar})


@login_required
@staff_required
@require_POST
def hapus_sktm(request, pk):
    sktm = get_object_or_404(SKTMPengajuan, pk=pk)
    sktm.delete()
    return redirect('daftar_pengajuan_sktm')


@login_required
@staff_required
def detail_sktm(request, pk):
    sktm = get_object_or_404(SKTMPengajuan, pk=pk)
    if request.method == 'POST':
        sktm.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            sktm.hasil_surat = hasil_surat
        sktm.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_sktm', pk=pk)
    return render(request, 'admin/detail_sktm.html', {'sktm': sktm})


# =========================================================================
# DOMISILI (BIASA)
# =========================================================================

@login_required
@staff_required
def daftar_domisili(request):
    daftar = DomisiliPengajuan.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_domisili.html', {'daftar': daftar})


@login_required
@staff_required
@require_POST
def hapus_domisili(request, pk):
    domisili = get_object_or_404(DomisiliPengajuan, pk=pk)
    domisili.delete()
    return redirect('daftar_domisili')


@login_required
def pengajuan_domisili(request):
    if request.method == 'POST':
        sudah_ada = DomisiliPengajuan.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_domisili')
            return redirect('pengajuan_domisili')

        form = DomisiliPengajuanForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_domisili')
            return redirect('pengajuan_domisili')
    else:
        form = DomisiliPengajuanForm()

    return render(request, 'surat/domisili_form.html', {'form': form})


@login_required
@staff_required
def detail_domisili(request, pk):
    domisili = get_object_or_404(DomisiliPengajuan, pk=pk)
    if request.method == 'POST':
        domisili.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            domisili.hasil_surat = hasil_surat
        domisili.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_domisili', pk=pk)
    return render(request, 'admin/detail_domisili.html', {'domisili': domisili})


# =========================================================================
# SKU
# =========================================================================

@login_required
@staff_required
def daftar_sku(request):
    sku = SKUPengajuan.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_sku.html', {'daftar': sku})


@login_required
@staff_required
@require_POST
def hapus_sku(request, pk):
    sku = get_object_or_404(SKUPengajuan, pk=pk)
    sku.delete()
    return redirect('daftar_sku')


@login_required
def pengajuan_sku(request):
    if request.method == 'POST':
        sudah_ada = SKUPengajuan.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_sku')
            return redirect('pengajuan_sku')

        form = SKUPengajuanForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_sku')
            return redirect('pengajuan_sku')
    else:
        form = SKUPengajuanForm()

    return render(request, 'surat/sku_form.html', {'form': form})


@login_required
@staff_required
def detail_sku(request, pk):
    sku = get_object_or_404(SKUPengajuan, pk=pk)

    if request.method == 'POST':
        sku.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            sku.hasil_surat = hasil_surat
        sku.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_sku', pk=pk)

    file_fields = [
        ("Surat Pengantar", sku.surat_pengantar),
        ("Surat Permohonan", sku.surat_permohonan),
        ("Foto KTP", sku.foto_ktp),
        ("Foto KK", sku.foto_kk),
        ("Surat Kuasa", sku.surat_kuasa),
    ]

    return render(request, 'admin/detail_sku.html', {'sku': sku, 'file_fields': file_fields})


# =========================================================================
# SURAT PENGANTAR KTP
# =========================================================================

@login_required
@staff_required
def daftar_surat_ktp(request):
    ktp = SuratKTPBaruPengantar.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_Surat_ktp.html', {'daftar': ktp})


@login_required
@staff_required
@require_POST
def hapus_ktp(request, pk):
    ktp = get_object_or_404(SuratKTPBaruPengantar, pk=pk)
    ktp.delete()
    return redirect('daftar_ktp')


@login_required
def pengajuan_surat_ktp(request):
    if request.method == 'POST':
        sudah_ada = SuratKTPBaruPengantar.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_ktp')
            return redirect('pengajuan_ktp')

        form = KTPBaruPengantarForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_ktp')
            return redirect('pengajuan_ktp')
    else:
        form = KTPBaruPengantarForm()

    return render(request, 'surat/Ktp_form.html', {'form': form})


@login_required
@staff_required
def detail_ktp(request, pk):
    ktp = get_object_or_404(SuratKTPBaruPengantar, pk=pk)
    if request.method == 'POST':
        ktp.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            ktp.hasil_surat = hasil_surat
        ktp.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_ktp', pk=pk)
    return render(request, 'admin/detail_ktp.html', {'ktp': ktp})


# =========================================================================
# SURAT PENGANTAR KK
# =========================================================================

@login_required
@staff_required
def daftar_surat_kk(request):
    kk = SuratKKPengantar.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_surat_kk.html', {'daftar': kk})


@login_required
@staff_required
@require_POST
def hapus_kk(request, pk):
    kk = get_object_or_404(SuratKKPengantar, pk=pk)
    kk.delete()
    return redirect('daftar_kk')


@login_required
def pengajuan_surat_kk(request):
    if request.method == 'POST':
        sudah_ada = SuratKKPengantar.objects.filter(
            user=request.user, status__in=['diajukan', 'diproses']
        ).exists()
        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_kk')
            return redirect('pengajuan_kk')

        form = KKPengantarForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_kk')
            return redirect('pengajuan_kk')
    else:
        form = KKPengantarForm()

    return render(request, 'surat/kk_form.html', {'form': form})


@login_required
@staff_required
def detail_kk(request, pk):
    kk = get_object_or_404(SuratKKPengantar, pk=pk)
    if request.method == 'POST':
        kk.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            kk.hasil_surat = hasil_surat
        kk.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_kk', pk=pk)
    return render(request, 'admin/detail_kk.html', {'kk': kk})


# =========================================================================
# SURAT LAINNYA
# =========================================================================

@login_required
def pengajuan_surat_lainnya(request):
    if request.method == 'POST':
        form = SuratLainnyaForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_lainnya')
            return redirect('pengajuan_surat_lainnya')
    else:
        form = SuratLainnyaForm()

    return render(request, 'surat/suratlainnya_form.html', {'form': form})


@login_required
@staff_required
def daftar_surat_lainnya(request):
    daftar = SuratLainnya.objects.select_related('user').all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_suratlainnya.html', {'daftar': daftar})


@login_required
@staff_required
def detail_surat_lainnya(request, pk):
    surat = get_object_or_404(SuratLainnya, pk=pk)
    if request.method == 'POST':
        surat.status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        if hasil_surat:
            surat.hasil_surat = hasil_surat
        surat.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_surat_lainnya', pk=pk)

    return render(request, 'admin/detail_suratlainnya.html', {'surat': surat})


@login_required
@staff_required
@require_POST
def hapus_surat_lainnya(request, pk):
    surat = get_object_or_404(SuratLainnya, pk=pk)
    surat.delete()
    messages.success(request, "Data berhasil dihapus.")
    return redirect('daftar_surat_lainnya')


# =========================================================================
# CEK STATUS (WARGA)
# Sudah aman: selalu difilter `user=request.user`, jadi satu warga tidak
# bisa mengintip status pengajuan warga lain.
# =========================================================================

@login_required
def cek_status_surat(request):
    hasil = None
    jenis = request.GET.get('jenis')

    jenis_map = {
        'kelahiran': SuratKelahiran,
        'kematian': SuratKematian,
        'pindah_datang': PindahDatang,
        'domisili_usaha': DomisiliUsaha,
        'SKTM': SKTMPengajuan,
        'SKU': SKUPengajuan,
        'domisili': DomisiliPengajuan,
        'Surat_KTP': SuratKTPBaruPengantar,
        'Surat_KK': SuratKKPengantar,
        'lainnya': SuratLainnya,
    }

    model_class = jenis_map.get(jenis)
    if model_class is not None:
        hasil = model_class.objects.filter(user=request.user)

    return render(request, 'profile/cek_status.html', {'hasil': hasil, 'jenis': jenis})


# =========================================================================
# PENGUMUMAN
# =========================================================================

@login_required
@staff_required
def announcement_manage(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action_create = 'create' in request.POST
        action_edit = 'edit' in request.POST
        action_delete = 'delete' in request.POST
        title = request.POST.get('title')
        content = request.POST.get('content')
        announcement_id = request.POST.get('announcement_id')

        if action_create:
            if not title or not content:
                return JsonResponse({'status': 'error', 'message': 'Judul dan konten harus diisi.'})
            announcement = Announcement.objects.create(title=title, content=content)
            for image in request.FILES.getlist('images'):
                AnnouncementImage.objects.create(announcement=announcement, image=image)
            return JsonResponse({'status': 'success'})

        elif action_edit:
            if not (title and content and announcement_id):
                return JsonResponse({'status': 'error', 'message': 'Data tidak lengkap.'})
            announcement = get_object_or_404(Announcement, id=announcement_id)
            announcement.title = title
            announcement.content = content
            announcement.save()

            AnnouncementImage.objects.filter(announcement=announcement).delete()
            for image in request.FILES.getlist('images'):
                AnnouncementImage.objects.create(announcement=announcement, image=image)
            return JsonResponse({'status': 'success'})

        elif action_delete:
            if not announcement_id:
                return JsonResponse({'status': 'error', 'message': 'ID pengumuman tidak ditemukan.'})
            announcement = get_object_or_404(Announcement, id=announcement_id)
            announcement.delete()
            return JsonResponse({'status': 'success'})

        return JsonResponse({'status': 'error', 'message': 'Permintaan tidak valid.'})

    announcements = Announcement.objects.prefetch_related('images').all()
    return render(request, 'admin/kelola_pengumuman.html', {'announcements': announcements})


def announcement_page(request):
    announcements = Announcement.objects.filter(is_active=True).order_by('-published_at')
    return render(request, 'profile/pengumuman.html', {'announcements': announcements})


def ajax_announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
    html = render_to_string('profile/pengumuman_detail.html', {'announcement': announcement}, request=request)
    return JsonResponse({'html': html})



# --------------------------------------------------------------------------
# HALAMAN WARGA
# --------------------------------------------------------------------------

@login_required
def chat_saya(request):
    """Halaman chat warga. Thread dibuat otomatis kalau belum ada."""
    thread, _ = ChatThread.objects.get_or_create(user=request.user)
    desa_key = DesaEncryptionKey.load()

    if desa_key is None:
        # staff belum pernah setup kunci kantor -> chat belum bisa dipakai
        return render(request, 'profile/belum_siap.html')

    my_key = UserEncryptionKey.objects.filter(user=request.user).first()

    return render(request, 'profile/chat_warga.html', {
        'thread_id': thread.id,
        'desa_public_key': desa_key.public_key_jwk,  # sudah string JSON
        'has_own_key': bool(my_key),
    })


@login_required
@require_POST
def chat_daftar_kunci(request):
    """
    Dipanggil sekali oleh JS pas warga pertama kali buka chat & belum
    punya keypair di IndexedDB-nya. Menyimpan public key ke server.
    """
    try:
        body = json_lib.loads(request.body)
    except json_lib.JSONDecodeError:
        return HttpResponseBadRequest("Body bukan JSON valid.")

    pub_jwk = body.get('public_key_jwk')
    if not pub_jwk:
        return HttpResponseBadRequest("public_key_jwk wajib diisi.")

    obj, created = UserEncryptionKey.objects.get_or_create(
        user=request.user,
        defaults={'public_key_jwk': json_lib.dumps(pub_jwk)},
    )
    if not created:
        # SENGAJA tidak menimpa key lama secara diam-diam — kalau ke-timpa,
        # semua pesan lama yang dibungkus pakai public key lama gak akan
        # bisa dibuka lagi. Ganti device = alur "restore" pakai backup key
        # (lihat wrapPrivateKeyWithPassphrase di e2ee.js), bukan generate baru.
        return JsonResponse({'status': 'exists'})

    return JsonResponse({'status': 'created'})


@login_required
@require_GET
def chat_public_key_saya(request):
    """Public key memang boleh diketahui publik — bukan rahasia."""
    key = get_object_or_404(UserEncryptionKey, user=request.user)
    return JsonResponse({'public_key_jwk': json_lib.loads(key.public_key_jwk)})


# --------------------------------------------------------------------------
# KIRIM & AMBIL PESAN (dipakai warga maupun staff)
# --------------------------------------------------------------------------

@login_required
@require_POST
def chat_kirim(request):
    try:
        body = json_lib.loads(request.body)
    except json_lib.JSONDecodeError:
        return HttpResponseBadRequest("Body bukan JSON valid.")

    thread = get_object_or_404(ChatThread, pk=body.get('thread_id'))

    if not request.user.is_staff and thread.user_id != request.user.id:
        return HttpResponseForbidden("Bukan thread kamu.")

    wajib = ('ciphertext', 'iv', 'wrapped_key_warga', 'wrapped_key_desa')
    if not all(body.get(f) for f in wajib):
        return HttpResponseBadRequest("Field ciphertext/iv/wrapped_key_* wajib diisi.")

    ChatMessage.objects.create(
        thread=thread,
        pengirim=request.user,
        ciphertext=body['ciphertext'],
        iv=body['iv'],
        wrapped_key_warga=body['wrapped_key_warga'],
        wrapped_key_desa=body['wrapped_key_desa'],
    )
    ChatThread.objects.filter(pk=thread.pk).update(updated_at=timezone.now())

    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def chat_ketik(request):
    """Dipanggil (debounced) saat user mengetik di kolom input."""
    thread = get_object_or_404(ChatThread, pk=request.POST.get('thread_id'))
    if not request.user.is_staff and thread.user_id != request.user.id:
        return HttpResponseForbidden("Bukan thread kamu.")

    field = 'staff_typing_at' if request.user.is_staff else 'warga_typing_at'
    ChatThread.objects.filter(pk=thread.pk).update(**{field: timezone.now()})
    return JsonResponse({'status': 'ok'})

@login_required
@require_GET
def chat_pesan_list(request):
    thread = get_object_or_404(ChatThread, pk=request.GET.get('thread_id'))
    if not request.user.is_staff and thread.user_id != request.user.id:
        return HttpResponseForbidden("Bukan thread kamu.")

    try:
        sejak_id = int(request.GET.get('sejak', 0))
    except ValueError:
        sejak_id = 0

    pesan_qs = thread.messages.filter(id__gt=sejak_id).order_by('created_at')
    data = [{
        'id': m.id,
        'ciphertext': m.ciphertext,
        'iv': m.iv,
        'wrapped_key_warga': m.wrapped_key_warga,
        'wrapped_key_desa': m.wrapped_key_desa,
        'pengirim_is_me': m.pengirim_id == request.user.id,
        'pengirim_is_staff': m.pengirim.is_staff,
    } for m in pesan_qs]

    # cek lawan bicara lagi ngetik dalam 3 detik terakhir
    lawan_field = 'warga_typing_at' if request.user.is_staff else 'staff_typing_at'
    lawan_typing_at = getattr(thread, lawan_field)
    batas = timezone.now() - timedelta(seconds=3)
    lawan_sedang_mengetik = bool(lawan_typing_at and lawan_typing_at > batas)

    return JsonResponse({'pesan': data, 'lawan_mengetik': lawan_sedang_mengetik})


# --------------------------------------------------------------------------
# HALAMAN STAFF
# --------------------------------------------------------------------------


@login_required
@staff_required
def chat_admin_daftar(request):
    if DesaEncryptionKey.load() is None:
        return redirect('chat_setup_kunci_desa')

    threads = (
        ChatThread.objects
        .select_related('user', 'user__userprofile')
        .order_by('-updated_at')
    )
    return render(request, 'admin/chat_admin_list.html', {'threads': threads})

@login_required
@staff_required
def chat_admin_thread(request, thread_id):
    thread = get_object_or_404(
        ChatThread.objects.select_related('user', 'user__userprofile'),
        pk=thread_id
    )
    desa_key = DesaEncryptionKey.load()
    warga_key = get_object_or_404(UserEncryptionKey, user=thread.user)

    return render(request, 'admin/chat_admin_thread.html', {
        'thread': thread,
        'desa_public_key': desa_key.public_key_jwk,
        'warga_public_key': warga_key.public_key_jwk,
        'wrapped_private_key': desa_key.wrapped_private_key,
    })


@login_required
@staff_required
def chat_setup_kunci_desa(request):
    """
    Setup SEKALI SEUMUR HIDUP proyek: petugas generate keypair Kantor Desa
    di browser, private key yang sama dibungkus 2x — sekali pakai
    passphrase harian, sekali pakai kode pemulihan (recovery code) yang
    cuma ditampilkan sekali buat dicetak/dicatat manual. Server cuma
    terima dua blob terbungkus itu, gak pernah pegang plaintext-nya.
    """
    if request.method == 'POST':
        if DesaEncryptionKey.load() is not None:
            return HttpResponseForbidden("Kunci kantor sudah pernah dibuat.")

        try:
            body = json_lib.loads(request.body)
        except json_lib.JSONDecodeError:
            return HttpResponseBadRequest("Body bukan JSON valid.")

        wajib = ('public_key_jwk', 'wrapped_private_key', 'wrapped_private_key_recovery')
        if not all(body.get(f) for f in wajib):
            return HttpResponseBadRequest("Field wajib belum lengkap.")

        DesaEncryptionKey.objects.create(
            public_key_jwk=json_lib.dumps(body['public_key_jwk']),
            wrapped_private_key=json_lib.dumps(body['wrapped_private_key']),
            wrapped_private_key_recovery=json_lib.dumps(body['wrapped_private_key_recovery']),
        )
        return JsonResponse({'status': 'ok'})

    if DesaEncryptionKey.load() is not None:
        messages.info(request, "Kunci kantor sudah pernah di-setup sebelumnya.")
        return redirect('chat_admin_daftar')

    return render(request, 'admin/chat_setup_kunci.html')


@login_required
@staff_required
def chat_pemulihan_kunci(request):
    """
    Alur "lupa passphrase harian": petugas masukin kode pemulihan yang
    dicatat pas setup awal, browser buka private key pakai kode itu,
    lalu bungkus ULANG pakai passphrase baru + kode pemulihan BARU
    (yang lama dianggap sudah "terpakai", jangan dipakai lagi).

    Server di sini cuma nerima & nimpa dua blob terbungkus yang baru —
    gak ada cara buat server verifikasi isinya bener, itu memang gak
    perlu: kalau kode pemulihan yang dimasukkan salah, proses decrypt
    di browser bakal gagal duluan sebelum sempat kirim apa-apa ke sini.
    """
    desa_key = DesaEncryptionKey.load()
    if desa_key is None:
        messages.error(request, "Kunci kantor belum pernah di-setup.")
        return redirect('chat_setup_kunci_desa')

    if request.method == 'POST':
        try:
            body = json_lib.loads(request.body)
        except json_lib.JSONDecodeError:
            return HttpResponseBadRequest("Body bukan JSON valid.")

        wajib = ('wrapped_private_key', 'wrapped_private_key_recovery')
        if not all(body.get(f) for f in wajib):
            return HttpResponseBadRequest("Field wajib belum lengkap.")

        desa_key.wrapped_private_key = json_lib.dumps(body['wrapped_private_key'])
        desa_key.wrapped_private_key_recovery = json_lib.dumps(body['wrapped_private_key_recovery'])
        desa_key.save(update_fields=['wrapped_private_key', 'wrapped_private_key_recovery', 'updated_at'])
        return JsonResponse({'status': 'ok'})

    return render(request, 'admin/chat_pemulihan_kunci.html', {
        'wrapped_private_key_recovery': desa_key.wrapped_private_key_recovery,
    })