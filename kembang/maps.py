import re
import requests


def resolve_maps_embed_url(share_url):
    """
    Ambil URL share Google Maps (mis. https://maps.app.goo.gl/xxxxx),
    ikuti redirect-nya, terus tarik koordinat dari URL final buat
    disusun jadi iframe-embeddable URL (gak butuh API key).

    Return None kalau gagal (network error / format URL gak dikenali) —
    caller wajib fallback ke tampilan link-out biasa.
    """
    try:
        resp = requests.get(share_url, allow_redirects=True, timeout=5)
        final_url = resp.url
    except requests.RequestException:
        return None

    # Format umum: .../@-6.123456,106.123456,17z/...
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
    if not match:
        # Format alternatif: !3d-6.123456!4d106.123456
        match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)

    if not match:
        return None

    lat, lng = match.group(1), match.group(2)
    return f"https://maps.google.com/maps?q={lat},{lng}&z=16&output=embed"


# ===== Perubahan di TentangDesa =====
#
# class TentangDesa(models.Model):
#     ...
#     lokasi_embed_url = models.URLField(
#         blank=True, null=True,
#         help_text="Paste link share dari Google Maps (klik tombol Bagikan di Maps, "
#                    "copy link-nya). Contoh: https://maps.app.goo.gl/xxxxxxx"
#     )
#     lokasi_embed_cache = models.URLField(
#         blank=True, null=True, editable=False,
#         help_text="Auto-generated, jangan diedit manual.",
#     )
#     ...
#
#     def save(self, *args, **kwargs):
#         self.pk = 1  # singleton
#
#         try:
#             old = TentangDesa.objects.get(pk=1)
#         except TentangDesa.DoesNotExist:
#             old = None
#
#         url_changed = (old is None) or (old.lokasi_embed_url != self.lokasi_embed_url)
#
#         if not self.lokasi_embed_url:
#             self.lokasi_embed_cache = ""
#         elif url_changed:
#             resolved = resolve_maps_embed_url(self.lokasi_embed_url)
#             self.lokasi_embed_cache = resolved or ""
#
#         super().save(*args, **kwargs)