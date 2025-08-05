# Flask Tabanlı Rezervasyon SistemiFlask Tabanlı Rezervasyon Sistemi

## Genel BakışGenel Bakış

Bu program, Flask çerçevesi kullanılarak geliştirilmiş bir web tabanlı rezervasyon sistemidir. Kullanıcıların, ev sahiplerinin ve adminlerin bir ev kiralama platformunda
çeşitli işlemler yapmasını sağlar. Sistem, kullanıcı kaydı, giriş/çıkış, ilan oluşturma/düzenleme/silme, rezervasyon yapma/iptal etme/onaylama ve yorum bırakma gibi
işlevsellikler sunar. Veritabanı işlemleri için Microsoft SQL Server ve pyodbc kütüphanesi kullanılır. Kullanıcı arayüzü HTML şablonları ile oluşturulmuş ve statik
dosyalar (örneğin resimler) static/uploads klasöründe saklanır.

## KurulumKurulum

```
GereksinimlerGereksinimler:
Python 3.8 veya üstü.
Gerekli kütüphaneler: flask, pyodbc, werkzeug.
Microsoft SQL Server veritabanı (yerel sunucu).
Veritabanı adı: projeveritabanı.
Kurulum AdımlarıKurulum Adımları:
1. Gerekli kütüphaneleri yükleyin: pip install flask pyodbc werkzeug.
2. SQL Server'da projeveritabanı adında bir veritabanı oluşturun ve gerekli tabloları/fonksiyonları/stored procedure'leri tanımlayın (örneğin,
kullanicilar, ilanlar, rezervasyon, odemeler, yorumlar tabloları).
3. Kodu çalıştırın: python app.py.
ÇalıştırmaÇalıştırma:
Uygulama varsayılan olarak http://0.0.0.0:5000 adresinde çalışır.
Komut: python app.py.
```
## Kod YapısıKod Yapısı

Kod, Flask uygulamasını temel alan bir web uygulamasıdır ve aşağıdaki ana bileşenlerden oluşur:

```
Flask UygulamasıFlask Uygulaması: Web sunucusunu başlatır ve yönlendirmeleri (route) yönetir.
Veritabanı BağlantısıVeritabanı Bağlantısı: connect_db() fonksiyonu ile SQL Server'a bağlanır.
ŞifrelemeŞifreleme: hash_password() fonksiyonu ile kullanıcı şifreleri SHA-256 ile şifrelenir.
Dosya YüklemeDosya Yükleme: allowed_file() ve secure_filename() ile güvenli resim yükleme yapılır.
Oturum YönetimiOturum Yönetimi: Kullanıcı oturumları session ile yönetilir.
RotalarRotalar: Kullanıcı, ev sahibi ve admin panelleri için farklı URL yolları (/login, /admin, /ev_sahibi, vb.) tanımlanmıştır.
```
## Rotalar (Endpoints)Rotalar (Endpoints)

```
1. // (login) (login):
```
```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Kullanıcı giriş sayfasını yapar ve giriş işlemini gerçekleştirir.
POST İşlemiPOST İşlemi:
Kullanıcı e-posta ve şifresini alır, veritabanında kontrol eder.
Şifre doğrulanırsa, kullanıcı tipine (admin, ev_sahibi, kullanici) göre ilgili panele yönlendirir.
Oturum (session) oluşturur ve aktif durumunu günceller.
TemplateTemplate: login.html.
```
```
2. /ev_sahibi/ev_sahibi (ev_sahibi_paneli) (ev_sahibi_paneli):
```
```
MetotMetot: GET.
AçıklamaAçıklama: Ev sahibi panelini gösterir; ilan sayısı, bekleyen rezervasyonlar ve toplam geliri listeler.
Veritabanı İşlemleriVeritabanı İşlemleri:
fn_AktifIlanSayisi, fn_BeklemedeRezervasyonSayisi, fn_EvSahibiGelirHesapla fonksiyonlarını kullanır.
TemplateTemplate: ev_sahibi.html.
```
```
3. /admin/admin (admin_paneli) (admin_paneli):
```
```
MetotMetot: GET.
AçıklamaAçıklama: Admin panelini gösterir; kullanıcı sayısı, aktif kullanıcılar, onaylanmış rezervasyonlar ve aktif ilanları listeler.
TemplateTemplate: admin.html.
```
```
4. /kullanicilar/kullanicilar:
```
```
MetotMetot: GET.
AçıklamaAçıklama: Admin için kullanıcı listesini gösterir.
TemplateTemplate: admin_kullanici.html.
```
```
5. /user_sil/<u_id>/user_sil/<u_id>:
```
```
MetotMetot: GET.
AçıklamaAçıklama: Admin tarafından belirtilen kullanıcıyı siler.
Veritabanı İşlemiVeritabanı İşlemi: DELETE FROM kullanicilar.
```
```
6. /ilanlar/ilanlar:
```
```
MetotMetot: GET.
```

```
AçıklamaAçıklama: Admin için aktif ve pasif ilanları listeler.
TemplateTemplate: admin_ilanlar.html.
```
```
7. /ailan_sil/<ilan_id>/ailan_sil/<ilan_id>:
```
```
MetotMetot: GET.
AçıklamaAçıklama: Admin tarafından belirtilen ilanın durumunu silindi olarak günceller.
```
```
8. /rezer/rezer:
```
```
MetotMetot: GET.
AçıklamaAçıklama: Admin için tüm rezervasyonları listeler; ödeme ve yorum bilgileriyle birlikte.
TemplateTemplate: admin_rezer.html.
```
```
9. /rezer_iptal/<rezers_id>,<rezers_kullanici>/rezer_iptal/<rezers_id>,<rezers_kullanici>:
```
```
MetotMetot: GET.
AçıklamaAçıklama: Admin tarafından rezervasyonu iptal eder (sp_iptal_rezervasyon).
```
10. /ilanlarim/ilanlarim:

```
MetotMetot: GET.
AçıklamaAçıklama: Ev sahibinin kendi ilanlarını listeler.
TemplateTemplate: ilanlarim.html.
```
11. /ilan_ekle/ilan_ekle:

```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Ev sahibinin yeni ilan eklemesini sağlar; resim yükleme desteklenir.
TemplateTemplate: ilan_ekle.html.
```
12. /ilan_duzenle/<ilan_id>/ilan_duzenle/<ilan_id>:

```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Ev sahibinin mevcut ilanı düzenlemesini sağlar.
TemplateTemplate: ilan_duzenle.html.
```
13. /ilan_sil/<ilan_id>/ilan_sil/<ilan_id>:

```
MetotMetot: GET.
AçıklamaAçıklama: Ev sahibinin kendi ilanını siler (durum silindi olur).
```
14. /register/register:

```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Yeni kullanıcı kaydı yapar (sp_kullanici_ekle).
TemplateTemplate: register.html.
```
15. /register2/register2:

```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Admin tarafından yeni kullanıcı eklenmesini sağlar.
TemplateTemplate: admin_ekle.html.
```
16. /reset/reset:

```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Şifre sıfırlama işlemini gerçekleştirir.
TemplateTemplate: reset.html.
```
17. /kullanici/kullanici (kullanici_paneli) (kullanici_paneli):

```
MetotMetot: GET.
AçıklamaAçıklama: Kullanıcıların aktif ilanları filtreleyerek görmesini sağlar.
TemplateTemplate: kullanici.html.
```
18. /rezervasyon/<ilan_id>/rezervasyon/<ilan_id>:

```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Kullanıcıların rezervasyon yapmasını sağlar; ödeme bilgileri kaydedilir.
TemplateTemplate: rezervasyon.html.
```
19. /rezervasyonlarim/rezervasyonlarim:

```
MetotMetot: GET.
AçıklamaAçıklama: Kullanıcının rezervasyonlarını listeler; yorum yapma durumu kontrol edilir.
TemplateTemplate: rezervasyonlarim.html.
```
20. /evsahibi_rezervasyonlar/evsahibi_rezervasyonlar:

```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Ev sahibinin rezervasyonlarını listeler.
TemplateTemplate: evsahibi_rezervasyonlar.html.
```
21. /rezervasyon_iptal/rezervasyon_iptal:


```
MetotMetot: POST.
AçıklamaAçıklama: Kullanıcı veya admin tarafından rezervasyon iptali (sp_iptal_rezervasyon).
```
```
22. /rezervasyon_iptal1/rezervasyon_iptal1:
```
```
MetotMetot: POST.
AçıklamaAçıklama: Ev sahibi tarafından rezervasyon iptali.
```
```
23. /rezervasyon_onay/rezervasyon_onay:
```
```
MetotMetot: POST.
AçıklamaAçıklama: Ev sahibinin rezervasyonu onaylaması.
```
```
24. /yorum-gonder/yorum-gonder:
```
```
MetotMetot: POST.
AçıklamaAçıklama: Kullanıcının rezervasyona yorum ve puan eklemesi.
```
```
25. /logout/logout:
```
```
MetotlarMetotlar: GET, POST.
AçıklamaAçıklama: Kullanıcı oturumunu kapatır ve aktif durumunu günceller.
```
```
26. /admin/verileri_guncelle/admin/verileri_guncelle:
```
```
MetotMetot: GET.
AçıklamaAçıklama: Admin paneli için istatistikleri JSON formatında döndürür.
```
## Algoritma ve MantıkAlgoritma ve Mantık

```
Giriş/ÇıkışGiriş/Çıkış: Kullanıcı girişi SHA-256 şifreleme ile doğrulanır. Oturum yönetimi Flask session ile yapılır.
İlan Yönetimiİlan Yönetimi: Ev sahipleri ilan ekler/düzenler/siler. İlanlar veritabanında ilanlar tablosuna kaydedilir; durumları aktif, pasif veya silindi olabilir.
RezervasyonRezervasyon: Kullanıcılar tarih aralığına göre ilanları rezerve eder. Çakışma kontrolü SQL sorguları ile yapılır.
ÖdemeÖdeme: Ödeme bilgileri (odemeler tablosu) kaydedilir; kart numarası, son kullanma tarihi ve CVV doğrulaması yapılır.
YorumYorum: Kullanıcılar, rezervasyon bitiş tarihinden sonra yorum bırakabilir.
VeritabanıVeritabanı: SQL Server stored procedure'leri (sp_kullanici_ekle, sp_iptal_rezervasyon, sp_rezervasyon_listele) ve fonksiyonları
(fn_AktifIlanSayisi, fn_BeklemedeRezervasyonSayisi, fn_EvSahibiGelirHesapla) kullanılır.
```
## Örnek KullanımÖrnek Kullanım

```
GirişGiriş:
GirdiGirdi: E-posta: kullanici@example.com, Şifre: sifre123.
ÇıktıÇıktı: Kullanıcı tipine göre ilgili panele yönlendirme (/admin, /ev_sahibi, /kullanici).
İlan Eklemeİlan Ekleme:
GirdiGirdi: Başlık: "Deniz Manzaralı Ev", Fiyat: 500, Resim: ev.jpg.
ÇıktıÇıktı: İlan veritabanına eklenir ve ilanlarim sayfasına yönlendirilir.
RezervasyonRezervasyon:
GirdiGirdi: İlan ID: 1, Tarih: 2025-06-15 - 2025-06-20, Kart: 1234567812345678.
ÇıktıÇıktı: Rezervasyon beklemede durumuyla kaydedilir.
```
## Sınırlamalar ve VarsayımlarSınırlamalar ve Varsayımlar

```
SınırlamalarSınırlamalar:
Kart doğrulama sadece temel format kontrolü yapar (gerçek ödeme entegrasyonu yoktur).
SQL injection önlenmiştir, ancak ek güvenlik katmanları (örneğin, prepared statements) güçlendirilebilir.
Resim yükleme sadece belirli formatları destekler (png, jpg, jpeg, gif).
VarsayımlarVarsayımlar:
Veritabanı şeması önceden tanımlıdır (kullanicilar, ilanlar, rezervasyon, vb.).
Kullanıcıların e-posta adresleri benzersizdir.
Tarih formatı %Y-%m-%d veya %Y-%m-%d %H:%M:%S şeklindedir.
```
## Hata YönetimiHata Yönetimi

```
Her veritabanı işlemi try-except bloğu ile sarılmıştır.
Hatalar kullanıcıya flash mesajlarıyla bildirilir.
Oturum kontrolü her kritik rotada yapılır.
```
