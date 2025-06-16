from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import SuratKematian,SuratKelahiran,PindahDatang,UserProfile,SKTMPengajuan,Announcement,AnnouncementImage,SuratKKPengantar,SuratKTPBaruPengantar,DomisiliUsaha
from .forms import SuratKematianForm,SuratKelahiranForm,PindahDatangForm,SKUPengajuanForm,AnnouncementForm,AnnouncementImageForm,AnnouncementImageFormSet,KTPBaruPengantarForm,KKPengantarForm,DomisiliUsahaForm
from .models import DomisiliPengajuan,SKUPengajuan
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .forms import RegisterForm,SKTMPengajuanForm,DomisiliPengajuanForm
from django.db.models import Q
from itertools import chain 
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string




def home(request):
    announcements = Announcement.objects.filter(is_active=True).order_by('-published_at')[:5]  # Ambil 5 pengumuman terbaru
    return render(request, 'profile/home.html', {'announcements': announcements})

def persyaratan(request):
    return render(request, 'profile/persyaratan.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def tentang(request):
    return render(request, 'profile/tentang.html')

def profil(request):
    return render(request, 'profile/profil.html')




def login_view(request):
    if request.method == 'POST':
        nik = request.POST.get('nik')
        password = request.POST.get('password')
        user = authenticate(request, username=nik, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('home')  # Redirect ke admin site Django
            else:
                return redirect('home')  # Ganti dengan URL masyarakat/home
        else:
            messages.error(request, 'NIK atau password salah')
            return redirect('login')
    return render(request, 'surat/login.html')


def is_admin(user):
    return user.is_staff

@staff_member_required
def semua_pengajuan(request):
    akta_kelahiran = SuratKelahiran.objects.all()
    pindah_datang = PindahDatang.objects.all()
    pindah_keluar = DomisiliUsaha.objects.all()
    akta_kematian = SuratKematian.objects.all()

    return render(request, 'admin/dashboard.html', {
        'akta_kelahiran': akta_kelahiran,
        'pindah_datang': pindah_datang,
        'pindah_keluar': pindah_keluar,
        'akta_kematian': akta_kematian,
    })




@login_required
def pengajuan_akta_kematian(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = SuratKematian.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_kematian')
            return redirect('pengajuan_akta_kematian')

        form = SuratKematianForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_kematian')
            return redirect('pengajuan_akta_kematian')
    else:
        form = SuratKematianForm()

    return render(request, 'surat/aktakematian_form.html', {'form': form})

@staff_member_required
def daftar_pengajuan_akta_kematian(request):
    daftar = SuratKematian.objects.all().order_by('-tanggal_pengajuan')
    context = {'daftar': daftar}
    return render(request, 'admin/daftar_kematian.html', context)


@staff_member_required
def hapus_kematian(request, pk):
    daftar = get_object_or_404(SuratKematian, pk=pk)
    daftar.delete()
    return redirect('daftar_pengajuan_akta_kematian')

@staff_member_required
def detail_pengajuan_akta_kematian(request, pk):
    akta = get_object_or_404(SuratKematian, pk=pk)

    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        akta.status = status
        if hasil_surat:
            akta.hasil_surat = hasil_surat
        akta.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_akta_kematian',pk=pk)

    return render(request, 'admin/akta_kematian_detail.html', {'akta': akta})


@login_required
def pengajuan_akta_kelahiran(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = SuratKelahiran.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_kelahiran')
            return redirect('pengajuan_akta_kelahiran')

        form = SuratKelahiranForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_kelahiran')
            return redirect('pengajuan_akta_kelahiran')
    else:
        form = SuratKelahiranForm()

    return render(request, 'surat/akta_kelahiran_form.html', {'form': form})





@staff_member_required
def daftar_pengajuan_kelahiran(request):
    pengajuan = SuratKelahiran.objects.all().order_by('-tanggal_lahir')
    context = {'pengajuan': pengajuan}
    return render(request, 'admin/daftar_kelahiran.html', context)


@staff_member_required
def hapus_kelahiran(request, pk):
    pengajuan = get_object_or_404(SuratKelahiran, pk=pk)
    pengajuan.delete()
    return redirect('daftar_pengajuan_kelahiran')


@staff_member_required
def detail_pengajuan_kelahiran(request, pk):
    akta = get_object_or_404(SuratKelahiran, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        akta.status = status
        if hasil_surat:
            akta.hasil_surat = hasil_surat
        akta.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_kelahiran', pk=pk)
    return render(request, 'admin/detail_kelahiran.html', {'akta': akta})



@login_required
def pengajuan_pindah_datang(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = PindahDatang.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_datang')
            return redirect('pengajuan_pindah_datang')

        form = PindahDatangForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_datang')
            return redirect('pengajuan_pindah_datang')
    else:
        form = PindahDatangForm()

    return render(request, 'surat/datang_form.html', {'form': form})

@staff_member_required
def daftar_pindah_datang(request):
    pengajuan = PindahDatang.objects.all().order_by('-tanggal_pindah')
    return render(request, 'admin/daftar_datang.html', {'pengajuan': pengajuan})

@staff_member_required
def hapus_pindah_datang(request, pk):
    pengajuan = get_object_or_404(PindahDatang, pk=pk)
    pengajuan.delete()
    return redirect('daftar_pengajuan_pindah_datang')




@staff_member_required
def detail_pindah_datang(request, pk):
    datang = get_object_or_404(PindahDatang, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        datang.status = status
        if hasil_surat:
            datang.hasil_surat = hasil_surat
        datang.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_pindah_datang', pk=pk)
    return render(request, 'admin/detail_datang.html', {'datang': datang})



@login_required
def pengajuan_domisili_usaha(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = DomisiliUsaha.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_keluar')
            return redirect('pengajuan_skdu')

        form = DomisiliUsahaForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_keluar')
            return redirect('pengajuan_skdu')
    else:
        form = DomisiliUsahaForm()

    return render(request, 'surat/domisili_usaha_form.html', {'form': form})


@staff_member_required
def daftar_domisili_usaha(request):
    pengajuan = DomisiliUsaha.objects.all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_domisili_usaha.html', {'pengajuan': pengajuan})

@staff_member_required
def hapus_domisili_usaha(request, pk):
    pengajuan = get_object_or_404(DomisiliUsaha, pk=pk)
    pengajuan.delete()
    return redirect('daftar_pengajuan_skdu')

@staff_member_required
def detail_domisili_usaha(request, pk):
    pengajuan = get_object_or_404(DomisiliUsaha, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        pengajuan.status = status
        if hasil_surat:
            pengajuan.hasil_surat = hasil_surat
        pengajuan.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_skdu', pk=pk)
    return render(request, 'admin/detail_skdu.html', {'pengajuan': pengajuan})


@login_required
def pengajuan_sktm(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = SKTMPengajuan.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_sktm')
            return redirect('pengajuan_sktm')

        form = SKTMPengajuanForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_sktm')
            return redirect('pengajuan_sktm')
    else:
        form = SKTMPengajuanForm()

    return render(request, 'surat/sktm_form.html', {'form': form})

@staff_member_required
def daftar_sktm(request):
    daftar = SKTMPengajuan.objects.all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_sktm.html', {'daftar': daftar})

@staff_member_required
def hapus_sktm(request, pk):
    sktm = get_object_or_404(SKTMPengajuan, pk=pk)
    sktm.delete()
    return redirect('daftar_sktm')

@staff_member_required
def detail_sktm(request, pk):
    sktm = get_object_or_404(SKTMPengajuan, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        sktm.status = status
        if hasil_surat:
            sktm.hasil_surat = hasil_surat
        sktm.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_sktm', pk=pk)
    return render(request, 'admin/detail_sktm.html', {'sktm': sktm})



@staff_member_required
def daftar_domisili(request):
    daftar = DomisiliPengajuan.objects.all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_domisili.html', {'daftar': daftar})

@staff_member_required
def hapus_domisili(request, pk):
    domisili = get_object_or_404(DomisiliPengajuan, pk=pk)
    domisili.delete()
    return redirect('daftar_domisili')

@login_required
def pengajuan_domisili(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = DomisiliPengajuan.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_domisili')
            return redirect('pengajuan_domisili')

        form = DomisiliPengajuanForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_domisili')
            return redirect('pengajuan_domisili')
    else:
        form = DomisiliPengajuanForm()

    return render(request, 'surat/domisili_form.html', {'form': form})

@staff_member_required
def detail_domisili(request, pk):
    domisili = get_object_or_404(DomisiliPengajuan, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        domisili.status = status
        if hasil_surat:
            domisili.hasil_surat = hasil_surat
        domisili.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_domisili', pk=pk)
    return render(request, 'admin/detail_domisili.html', {'domisili': domisili})



@staff_member_required
def daftar_sku(request):
    sku = SKUPengajuan.objects.all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_sku.html', {'sku': sku})

@staff_member_required
def hapus_sku(request, pk):
    sku = get_object_or_404(SKUPengajuan, pk=pk)
    sku.delete()
    return redirect('daftar_sku')


@login_required
def pengajuan_sku(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = SKUPengajuan.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_sku')
            return redirect('pengajuan_sku')

        form = SKUPengajuanForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_sku')
            return redirect('pengajuan_sku')
    else:
        form = SKUPengajuanForm()

    return render(request, 'surat/sku_form.html', {'form': form})

@staff_member_required
def detail_sku(request, pk):
    sku = get_object_or_404(SKUPengajuan, pk=pk)

    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')

        sku.status = status
        if hasil_surat:
            sku.hasil_surat = hasil_surat
        sku.save()

        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_sku', pk=pk)

    # ✅ Tambahkan ini agar tidak error di template saat for-loop file
    file_fields = [
        ("Surat Pengantar", sku.surat_pengantar),
        ("Surat Permohonan", sku.surat_permohonan),
        ("Foto KTP", sku.foto_ktp),
        ("Foto KK", sku.foto_kk),
        ("Surat Kuasa", sku.surat_kuasa),
    ]

    return render(request, 'admin/detail_sku.html', {
        'sku': sku,
        'file_fields': file_fields  # ← Kirim ke template
    })





@staff_member_required
def daftar_surat_ktp(request):
    ktp = SuratKTPBaruPengantar.objects.all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_Surat_ktp.html', {'ktp': ktp})

@staff_member_required
def hapus_ktp(request, pk):
    ktp = get_object_or_404(SuratKTPBaruPengantar, pk=pk)
    ktp.delete()
    return redirect('daftar_ktp')


@login_required
def pengajuan_surat_ktp(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = SuratKTPBaruPengantar.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_ktp')
            return redirect('pengajuan_ktp')

        form = KTPBaruPengantarForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_ktp')
            return redirect('pengajuan_ktp')
    else:
        form = KTPBaruPengantarForm()

    return render(request, 'surat/Ktp_form.html', {'form': form})




@staff_member_required
def detail_ktp(request, pk):
    ktp = get_object_or_404(SuratKTPBaruPengantar, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        ktp.status = status
        if hasil_surat:
            ktp.hasil_surat = hasil_surat
        ktp.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_ktp', pk=pk)
    return render(request, 'admin/detail_ktp.html', {'ktp': ktp})




@staff_member_required
def daftar_surat_kk(request):
    kk = SuratKKPengantar.objects.all().order_by('-tanggal_pengajuan')
    return render(request, 'admin/daftar_surat_kk.html', {'kk': kk})



@staff_member_required
def hapus_kk(request, pk):
    kk = get_object_or_404(SuratKKPengantar, pk=pk)
    kk.delete()
    return redirect('daftar_kk')


@login_required
def pengajuan_surat_kk(request):
    if request.method == 'POST':
        # Cek apakah user sudah punya pengajuan aktif
        sudah_ada = SuratKKPengantar.objects.filter(
            user=request.user,
            status__in=['diajukan', 'diproses']
        ).exists()

        if sudah_ada:
            messages.warning(request, "Anda sudah memiliki pengajuan yang sedang diproses.", extra_tags='pengajuan_kk')
            return redirect('pengajuan_kk')

        form = KKPengantarForm(request.POST, request.FILES)
        if form.is_valid():
            pengajuan = form.save(commit=False)
            pengajuan.user = request.user
            pengajuan.status = 'diajukan'  # status awal
            pengajuan.save()
            messages.success(request, "Pengajuan berhasil dikirim.", extra_tags='pengajuan_kk')
            return redirect('pengajuan_kk')
    else:
        form = KKPengantarForm()

    return render(request, 'surat/kk_form.html', {'form': form})


@staff_member_required
def detail_kk(request, pk):
    kk = get_object_or_404(SuratKKPengantar, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        hasil_surat = request.FILES.get('hasil_surat')
        kk.status = status
        if hasil_surat:
            kk.hasil_surat = hasil_surat
        kk.save()
        messages.success(request, "Status berhasil diperbarui.")
        return redirect('detail_pengajuan_kk', pk=pk)
    return render(request, 'admin/detail_kk.html', {'kk': kk})



@login_required
def cek_status_surat(request):
    hasil = None
    jenis = request.GET.get('jenis')

    if jenis:
        if jenis == 'kelahiran':
            hasil = SuratKelahiran.objects.filter(user=request.user)
        elif jenis == 'kematian':
            hasil = SuratKematian.objects.filter(user=request.user)
        elif jenis == 'pindah_datang':
            hasil = PindahDatang.objects.filter(user=request.user)
        elif jenis == 'domisili_usaha':
            hasil = DomisiliUsaha.objects.filter(user=request.user)
        elif jenis == 'SKTM':
            hasil = SKTMPengajuan.objects.filter(user=request.user)
        elif jenis == 'SKU':
            hasil = SKUPengajuan.objects.filter(user=request.user)
        elif jenis == 'domisili':
            hasil = DomisiliPengajuan.objects.filter(user=request.user)
        elif jenis == 'Surat_KTP':
            hasil = SuratKTPBaruPengantar.objects.filter(user=request.user)
        elif jenis == 'Surat_KK':
            hasil = SuratKKPengantar.objects.filter(user=request.user)

    return render(request, 'profile/cek_status.html', {
        'hasil': hasil,
        'jenis': jenis
    })



def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            nik = form.cleaned_data['nik']
            nama = form.cleaned_data['nama']
            alamat = form.cleaned_data['alamat']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Buat user baru
            user = User.objects.create(
                username=nik,
                email=email,
                password=make_password(password)
            )

            # Buat UserProfile terkait user tadi
            UserProfile.objects.create(
                user=user,
                nama=nama,
                alamat=alamat
            )

            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'profile/register.html', {'form': form})


@user_passes_test(is_admin)
@staff_member_required
def admin_dashboard(request):
    akta_kelahiran = SuratKelahiran.objects.all()
    pindah_datang = PindahDatang.objects.all()
    pindah_keluar = DomisiliUsaha.objects.all()
    akta_kematian = SuratKematian.objects.all()
    sku = SKUPengajuan.objects.all()
    domisili = DomisiliPengajuan.objects.all()
    sktm = SKTMPengajuan.objects.all()

    semua_pengajuan = list(chain(
        akta_kelahiran,
        pindah_datang,
        pindah_keluar,
        akta_kematian,
        sku,
        domisili,
        sktm
    ))

    context = {
        'akta_kelahiran': akta_kelahiran,
        'pindah_datang': pindah_datang,
        'pindah_keluar': pindah_keluar,
        'akta_kematian': akta_kematian,
        'sku': sku,
        'domisili': domisili,
        'sktm': sktm,
        'semua_pengajuan': semua_pengajuan,
    }
    return render(request, 'admin/dashboard.html', context)

 # asumsikan kamu punya fungsi is_admin

from django.utils.http import url_has_allowed_host_and_scheme

# views.py



@user_passes_test(is_admin)
@login_required
def announcement_manage(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action_create = 'create' in request.POST
        action_edit = 'edit' in request.POST
        action_delete = 'delete' in request.POST
        title = request.POST.get('title')
        content = request.POST.get('content')
        announcement_id = request.POST.get('announcement_id')

        # ✅ CREATE
        if action_create:
            if not title or not content:
                return JsonResponse({'status': 'error', 'message': 'Judul dan konten harus diisi.'})
            announcement = Announcement.objects.create(title=title, content=content)
            for image in request.FILES.getlist('images'):
                AnnouncementImage.objects.create(announcement=announcement, image=image)
            return JsonResponse({'status': 'success'})

        # ✅ EDIT
        elif action_edit:
            if not (title and content and announcement_id):
                return JsonResponse({'status': 'error', 'message': 'Data tidak lengkap.'})
            announcement = get_object_or_404(Announcement, id=announcement_id)
            announcement.title = title
            announcement.content = content
            announcement.save()

            # Optional: Hapus semua gambar lama (bisa disesuaikan jika ingin ubah sebagian)
            AnnouncementImage.objects.filter(announcement=announcement).delete()

            for image in request.FILES.getlist('images'):
                AnnouncementImage.objects.create(announcement=announcement, image=image)
            return JsonResponse({'status': 'success'})

        # ✅ DELETE
        elif action_delete:
            if not announcement_id:
                return JsonResponse({'status': 'error', 'message': 'ID pengumuman tidak ditemukan.'})
            announcement = get_object_or_404(Announcement, id=announcement_id)
            announcement.delete()
            return JsonResponse({'status': 'success'})

        # ❌ Tidak ada aksi valid
        return JsonResponse({'status': 'error', 'message': 'Permintaan tidak valid.'})

    # ✅ GET: tampilkan halaman
    announcements = Announcement.objects.prefetch_related('images').all()
    return render(request, 'admin/kelola_pengumuman.html', {
        'announcements': announcements
    })







from django.shortcuts import render, get_object_or_404
from .models import Announcement
from django.http import JsonResponse
from django.template.loader import render_to_string

def announcement_page(request):
    announcements = Announcement.objects.filter(is_active=True).order_by('-published_at')
    return render(request, 'profile/pengumuman.html', {
        'announcements': announcements
    })

def ajax_announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
    html = render_to_string('profile/pengumuman_detail.html', {
        'announcement': announcement
    }, request=request)
    return JsonResponse({'html': html})








from datetime import datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test

def get_tanggal(obj):
    return (
        getattr(obj, 'tanggal_pengajuan', None) or
        getattr(obj, 'tanggal', None) or
        getattr(obj, 'tanggal_dibuat', None) or
        datetime.min  # fallback tanggal paling awal kalau semua None
    )

@user_passes_test(is_admin)
@staff_member_required
def semua_pengajuan(request):
    def tandai(queryset, nama_surat):
        for obj in queryset:
            obj.jenis_surat = nama_surat
        return list(queryset)

    semua_surat = (
        tandai(SuratKematian.objects.all(), "Surat Kematian") +
        tandai(SuratKelahiran.objects.all(), "Surat Kelahiran") +
        tandai(DomisiliUsaha.objects.all(), "Surat Domisili Usaha") +
        tandai(PindahDatang.objects.all(), "Surat Pindah Datang") +
        tandai(SKTMPengajuan.objects.all(), "Surat Keterangan Tidak Mampu") +
        tandai(DomisiliPengajuan.objects.all(), "Surat Domisili") +
        tandai(SKUPengajuan.objects.all(), "Surat Keterangan Usaha") +
        tandai(SuratKTPBaruPengantar.objects.all(), "Surat Pengantar KTP") +
        tandai(SuratKKPengantar.objects.all(), "Surat Pengantar KK")
    )

    semua_surat.sort(key=get_tanggal, reverse=True)

    return render(request, 'surat/semua_pengajuan.html', {'semua_surat': semua_surat})
