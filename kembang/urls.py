from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('tentang/', views.tentang, name='tentang'),
    path('profil/', views.profil, name='profil'),
    path('persyaratan/', views.persyaratan, name='persyaratan'),
    path('semua/', views.semua_pengajuan, name='semua_pengajuan'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-desa/akun-warga/', views.kelola_akun_warga, name='kelola_akun_warga'),
    path('admin-desa/akun-warga/reset-password/<int:user_id>/', views.reset_password_warga, name='reset_password_warga'),
     # Surat Kematian
    path('pengajuan-surat-kematian/', views.pengajuan_akta_kematian, name='pengajuan_akta_kematian'),
    path('kematian/surat-kematian/', views.daftar_pengajuan_akta_kematian, name='daftar_pengajuan_akta_kematian'),
    path('kematian/surat-kematian/<int:pk>/', views.detail_pengajuan_akta_kematian, name='detail_pengajuan_akta_kematian'),
    path('hapus-kematian/<int:pk>/', views.hapus_kematian, name='hapus_kematian'),
    # Akta Kelahiran
    path('pengajuan/surat-kelahiran/', views.pengajuan_akta_kelahiran, name='pengajuan_akta_kelahiran'),
    path('kelahiran/surat-kelahiran/', views.daftar_pengajuan_kelahiran, name='daftar_pengajuan_kelahiran'),
    path('kelahiran/surat-kelahiran/<int:pk>/', views.detail_pengajuan_kelahiran, name='detail_pengajuan_kelahiran'),
    path('hapus-kelahiran/<int:pk>/', views.hapus_kelahiran, name='hapus_kelahiran'),
    # Pindah Datang
    path('pengajuan/pindah-datang/', views.pengajuan_pindah_datang, name='pengajuan_pindah_datang'),
    path('datang/pindah-datang/', views.daftar_pindah_datang, name='daftar_pengajuan_pindah_datang'),
    path('datang/pindah-datang/<int:pk>/', views.detail_pindah_datang, name='detail_pengajuan_pindah_datang'),
    path('hapus-pindah-datang/<int:pk>/', views.hapus_pindah_datang, name='hapus_pindah_datang'),
    # sktm
    path('pengajuan/sktm/', views.pengajuan_sktm, name='pengajuan_sktm'),
    path('sktm/sktm/', views.daftar_sktm, name='daftar_pengajuan_sktm'),
    path('sktm/sktm/<int:pk>/', views.detail_sktm, name='detail_pengajuan_sktm'),
    path('hapus-sktm/<int:pk>/', views.hapus_sktm, name='hapus_sktm'),
    # domisili
    path('domisili/pengajuan/', views.pengajuan_domisili, name='pengajuan_domisili'),
    path('domisili/daftar/', views.daftar_domisili, name='daftar_domisili'),
    path('domisili/<int:pk>/', views.detail_domisili, name='detail_pengajuan_domisili'),
    path('hapus-domisili/<int:pk>/', views.hapus_domisili, name='hapus_domisili'),
    # sku
    path('sku/pengajuan/', views.pengajuan_sku, name='pengajuan_sku'),
    path('sku/daftar/', views.daftar_sku, name='daftar_sku'),
    path('sku/<int:pk>/', views.detail_sku, name='detail_pengajuan_sku'),
    path('hapus-sku/<int:pk>/', views.hapus_sku, name='hapus_sku'),

    path('ktp/pengajuan/', views.pengajuan_surat_ktp, name='pengajuan_ktp'),
    path('ktp/daftar/', views.daftar_surat_ktp, name='daftar_ktp'),
    path('ktp/detail/<int:pk>/', views.detail_ktp, name='detail_pengajuan_ktp'),
    path('hapus-ktp/<int:pk>/', views.hapus_ktp, name='hapus_ktp'),
 # SKDU
    path('pengajuan/domisili-usaha/', views.pengajuan_domisili_usaha, name='pengajuan_skdu'),
    path('usaha/domisili-usaha/', views.daftar_domisili_usaha, name='daftar_pengajuan_skdu'),
    path('usaha/domisili-usaha/<int:pk>/', views.detail_domisili_usaha, name='detail_skdu'),
    path('hapus-usaha/<int:pk>/', views.hapus_domisili_usaha, name='hapus_domisili_usaha'),
# KK
    path('kk/pengajuan/', views.pengajuan_surat_kk, name='pengajuan_kk'),
    path('kk/daftar/', views.daftar_surat_kk, name='daftar_kk'),
    path('kk/<int:pk>/', views.detail_kk, name='detail_pengajuan_kk'),
    path('hapus-kk/<int:pk>/', views.hapus_kk, name='hapus_kk'),
    path('pengajuan/surat-lainnya/', views.pengajuan_surat_lainnya, name='pengajuan_surat_lainnya'),
    path('surat/surat-lainnya/', views.daftar_surat_lainnya, name='daftar_surat_lainnya'),
    path('surat/surat-lainnya/<int:pk>/', views.detail_surat_lainnya, name='detail_surat_lainnya'),
    path('hapus-surat-lainnya/<int:pk>/', views.hapus_surat_lainnya, name='hapus_surat_lainnya'),

    path('admin-desa/tentang/kelola/', views.kelola_tentang_desa, name='kelola_tentang'),
    path('cek-status/', views.cek_status_surat, name='cek_status'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('kelola/pengumuman/', views.announcement_manage, name='announcement_manage'),
    path('pengumuman/', views.announcement_page, name='announcement_page'),
    path('ajax/announcement/<int:pk>/', views.ajax_announcement_detail, name='announcement_ajax_detail'),
    path('pengajuan/semua-pengajuan/', views.semua_pengajuan, name='semua_pengajuan'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('pengajuan/hapus/<str:model>/<int:pk>/', views.hapus_surat, name='hapus_surat'),
    path('pengajuan/hapus-semua/', views.hapus_semua_pengajuan, name='hapus_semua_pengajuan'),
    path('chat/', views.chat_saya, name='chat_saya'),
    path('chat/daftar-kunci/', views.chat_daftar_kunci, name='chat_daftar_kunci'),
    path('chat/public-key-saya/', views.chat_public_key_saya, name='chat_public_key_saya'),
    path('chat/kirim/', views.chat_kirim, name='chat_kirim'),
    path('chat/ketik/', views.chat_ketik, name='chat_ketik'),
    path('chat/pesan/', views.chat_pesan_list, name='chat_pesan_list'),
    path('staff/chat/', views.chat_admin_daftar, name='chat_admin_daftar'),
    path('staff/chat/setup-kunci/', views.chat_setup_kunci_desa, name='chat_setup_kunci_desa'),
    path('staff/chat/pemulihan-kunci/', views.chat_pemulihan_kunci, name='chat_pemulihan_kunci'),
    path('staff/chat/<int:thread_id>/', views.chat_admin_thread, name='chat_admin_thread'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

