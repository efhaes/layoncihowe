from .models import (
    SuratKelahiran, SuratKematian, PindahDatang, DomisiliUsaha,
    SKUPengajuan, DomisiliPengajuan, SKTMPengajuan,
    SuratKKPengantar, SuratKTPBaruPengantar, SuratLainnya,
)

def notifikasi_admin(request):
    # Hanya hitung kalau user memang staff & sedang login,
    # biar nggak query sia-sia di tiap request halaman publik.
    if not (request.user.is_authenticated and request.user.is_staff):
        return {}

    notifikasi = {
        'kelahiran': SuratKelahiran.objects.filter(status='diajukan').count(),
        'kematian': SuratKematian.objects.filter(status='diajukan').count(),
        'pindah': PindahDatang.objects.filter(status='diajukan').count(),
        'skdu': DomisiliUsaha.objects.filter(status='diajukan').count(),
        'sku': SKUPengajuan.objects.filter(status='diajukan').count(),
        'domisili': DomisiliPengajuan.objects.filter(status='diajukan').count(),
        'sktm': SKTMPengajuan.objects.filter(status='diajukan').count(),
        'kk': SuratKKPengantar.objects.filter(status='diajukan').count(),
        'ktp': SuratKTPBaruPengantar.objects.filter(status='diajukan').count(),
        'lainnya': SuratLainnya.objects.filter(status='diajukan').count(),
    }
    notifikasi['total'] = sum(notifikasi.values())

    return {'notifikasi': notifikasi}