from django.contrib import admin
from .models import SuratKematian,SuratKelahiran,PindahDatang,DomisiliUsaha,SKTMPengajuan, DomisiliPengajuan,SKUPengajuan,Announcement, AnnouncementImage,UserProfile, SuratKTPBaruPengantar, SuratKKPengantar


    



@admin.register(SuratKematian)
class SuratKematianAdmin(admin.ModelAdmin):
    list_display = (
        'nama_jenazah',
        'nik_jenazah',
        'tanggal_kematian',
        'nama_pelapor',
        'nik_pelapor',
        'no_whatsapp',
        'status',
        'tanggal_pengajuan',
    )
    search_fields = ('nama_jenazah', 'nik_jenazah', 'nama_pelapor', 'nik_pelapor')
    list_filter = ('status', 'tanggal_kematian', 'tanggal_pengajuan')
    readonly_fields = ('tanggal_pengajuan',)

@admin.register(SuratKelahiran)
class SuratKelahiranAdmin(admin.ModelAdmin):
    list_display = (
        'nama_lengkap',
        'tempat_lahir',
        'tanggal_lahir',
        'jenis_kelamin',
        'nama_ayah',
        'nama_ibu',
        'status',
        'no_whatsapp',
        'tanggal_pengajuan',
    )
    search_fields = ('nama_lengkap', 'nama_ayah', 'nama_ibu')
    list_filter = ('status', 'jenis_kelamin', 'tanggal_pengajuan')
    readonly_fields = ('tanggal_pengajuan',)



@admin.register(PindahDatang)
class PindahDatangAdmin(admin.ModelAdmin):
    list_display = (
        'nama',
        'nik',
        'asal_daerah',
        'tujuan_daerah',
        'tanggal_pindah',
        'status',
        'no_whatsapp',
        'tanggal_pengajuan',
    )
    search_fields = ('nama', 'nik', 'asal_daerah', 'tujuan_daerah')
    list_filter = ('status', 'tanggal_pengajuan')
    readonly_fields = ('tanggal_pengajuan',)


@admin.register(DomisiliUsaha)
class DomisiliUsahaAdmin(admin.ModelAdmin):
    list_display = (
        'nama_pemilik',
        'nik_pemilik',
        'nama_usaha',
        'jenis_usaha',
        'no_whatsapp',
        'status',
        'tanggal_pengajuan',
    )
    search_fields = ('nama_pemilik', 'nik_pemilik', 'nama_usaha')
    list_filter = ('status', 'tanggal_pengajuan')
    readonly_fields = ('tanggal_pengajuan',)




@admin.register(SKTMPengajuan)
class SKTMPengajuanAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nik', 'no_whatsapp', 'status', 'tanggal_pengajuan')
    search_fields = ('nama_lengkap', 'nik')
    list_filter = ('status', 'tanggal_pengajuan')

@admin.register(DomisiliPengajuan)
class DomisiliPengajuanAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nik', 'user' ,'no_whatsapp', 'status', 'tanggal_pengajuan')
    list_filter = ('status', 'tanggal_pengajuan')
    search_fields = ('nama_lengkap', 'nik', 'no_whatsapp')
    readonly_fields = ('tanggal_pengajuan',)

@admin.register(SKUPengajuan)
class SKUPengajuanAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nik', 'user' ,'npwp', 'no_whatsapp', 'status', 'tanggal_pengajuan')
    list_filter = ('status', 'tanggal_pengajuan')
    search_fields = ('nama_lengkap', 'nik', 'npwp', 'no_whatsapp')
    readonly_fields = ('tanggal_pengajuan',)

@admin.register(SuratKTPBaruPengantar)
class SuratKTPBaruPengantarAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'no_whatsapp', 'alamat_lengkap', 'status', 'tanggal_pengajuan')
    search_fields = ('nama_lengkap', 'no_whatsapp')
    list_filter = ('status', 'tanggal_pengajuan')


@admin.register(SuratKKPengantar)
class SuratKKPengantarAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nik', 'no_whatsapp', 'alamat', 'status', 'tanggal_pengajuan')
    search_fields = ('nama_lengkap', 'nik', 'no_whatsapp')
    list_filter = ('status', 'tanggal_pengajuan')


class AnnouncementImageInline(admin.TabularInline):  # atau bisa pakai StackedInline
    model = AnnouncementImage
    extra = 1  # jumlah form kosong tambahan yang ditampilkan

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_active')
    list_filter = ('is_active', 'published_at')
    search_fields = ('title', 'content')
    inlines = [AnnouncementImageInline]

admin.site.register(Announcement, AnnouncementAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nama', 'alamat')  # Menampilkan kolom di daftar admin
    search_fields = ('nama', 'user__username') # Kolom pencarian
    list_filter = ('nama',)                    # Filter di sidebar (opsional)

admin.site.register(UserProfile, UserProfileAdmin)