# pelayanan/urls.py
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


    path('kk/pengajuan/', views.pengajuan_surat_kk, name='pengajuan_kk'),
    path('kk/daftar/', views.daftar_surat_kk, name='daftar_kk'),
    path('kk/<int:pk>/', views.detail_kk, name='detail_pengajuan_kk'),
    path('hapus-kk/<int:pk>/', views.hapus_kk, name='hapus_kk'),

    # urls.py
    path('cek-status/', views.cek_status_surat, name='cek_status'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('kelola/pengumuman/', views.announcement_manage, name='announcement_manage'),
    path('pengumuman/', views.announcement_page, name='announcement_page'),
    path('ajax/announcement/<int:pk>/', views.ajax_announcement_detail, name='announcement_ajax_detail'),
    path('pengajuan/semua-pengajuan/', views.semua_pengajuan, name='semua_pengajuan'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

