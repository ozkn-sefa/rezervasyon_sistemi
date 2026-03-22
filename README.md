# Flask Tabanlı Rezervasyon Sistemi

## Genel Bakış

Bu program, Flask çerçevesi kullanılarak geliştirilmiş bir web tabanlı rezervasyon sistemidir. Kullanıcıların, ev sahiplerinin ve adminlerin bir ev kiralama platformunda çeşitli işlemler yapmasını sağlar. Sistem, kullanıcı kaydı, giriş/çıkış, ilan oluşturma/düzenleme/silme, rezervasyon yapma/iptal etme/onaylama ve yorum bırakma gibi işlevsellikler sunar. Veritabanı işlemleri için Microsoft SQL Server ve pyodbc kütüphanesi kullanılır. Kullanıcı arayüzü HTML şablonları ile oluşturulmuş ve statik dosyalar (örneğin resimler) `static/uploads` klasöründe saklanır.

## Kurulum

### Gereksinimler
- Python 3.8 veya üstü.
- Gerekli kütüphaneler: `flask`, `pyodbc`, `werkzeug`.
- Microsoft SQL Server veritabanı (yerel sunucu).
- Veritabanı adı: `projeveritabanı`.

### Kurulum Adımları
1. Gerekli kütüphaneleri yükleyin: `pip install flask pyodbc werkzeug`.
2. SQL Server'da `projeveritabanı` adında bir veritabanı oluşturun ve gerekli tabloları/fonksiyonları/stored procedure'leri tanımlayın (örneğin, `kullanicilar`, `ilanlar`, `rezervasyon`, `odemeler`, `yorumlar` tabloları).
3. Kodu çalıştırın: `python app.py`.

### Çalıştırma
- Uygulama varsayılan olarak `http://0.0.0.0:5000` adresinde çalışır.
- Komut: `python app.py`.

## Kod Yapısı

Kod, Flask uygulamasını temel alan bir web uygulamasıdır ve aşağıdaki ana bileşenlerden oluşur:

- **Flask Uygulaması**: Web sunucusunu başlatır ve yönlendirmeleri (route) yönetir.
- **Veritabanı Bağlantısı**: `connect_db()` fonksiyonu ile SQL Server'a bağlanır.
- **Şifreleme**: `hash_password()` fonksiyonu ile kullanıcı şifreleri SHA-256 ile şifrelenir.
- **Dosya Yükleme**: `allowed_file()` ve `secure_filename()` ile güvenli resim yükleme yapılır.
- **Oturum Yönetimi**: Kullanıcı oturumları `session` ile yönetilir.
- **Rotalar**: Kullanıcı, ev sahibi ve admin panelleri için farklı URL yolları (`/login`, `/admin`, `/ev_sahibi`, vb.) tanımlanmıştır.

## Rotalar (Endpoints)

1. **/** (`login`):
   - **Metotlar**: GET, POST.
   - **Açıklama**: Kullanıcı giriş sayfasını yapar ve giriş işlemini gerçekleştirir.
   - **POST İşlemi**:
     - Kullanıcı e-posta ve şifresini alır, veritabanında kontrol eder.
     - Şifre doğrulanırsa, kullanıcı tipine (admin, ev_sahibi, kullanici) göre ilgili panele yönlendirir.
     - Oturum (`session`) oluşturur ve aktif durumunu günceller.
   - **Template**: `login.html`.

2. **/ev_sahibi** (`ev_sahibi_paneli`):
   - **Metot**: GET.
   - **Açıklama**: Ev sahibi panelini gösterir; ilan sayısı, bekleyen rezervasyonlar ve toplam geliri listeler.
   - **Veritabanı İşlemleri**:
     - `fn_AktifIlanSayisi`, `fn_BeklemedeRezervasyonSayisi`, `fn_EvSahibiGelirHesapla` fonksiyonlarını kullanır.
   - **Template**: `ev_sahibi.html`.

3. **/admin** (`admin_paneli`):
   - **Metot**: GET.
   - **Açıklama**: Admin panelini gösterir; kullanıcı sayısı, aktif kullanıcılar, onaylanmış rezervasyonlar ve aktif ilanları listeler.
   - **Template**: `admin.html`.

4. **/kullanicilar**:
   - **Metot**: GET.
   - **Açıklama**: Admin için kullanıcı listesini gösterir.
   - **Template**: `admin_kullanici.html`.

5. **/user_sil/<u_id>**:
   - **Metot**: GET.
   - **Açıklama**: Admin tarafından belirtilen kullanıcıyı siler.
   - **Veritabanı İşlemi**: `DELETE FROM kullanicilar`.

6. **/ilanlar**:
   - **Metot**: GET.
   - **Açıklama**: Admin için aktif ve pasif ilanları listeler.
   - **Template**: `admin_ilanlar.html`.

7. **/ailan_sil/<ilan_id>**:
   - **Metot**: GET.
   - **Açıklama**: Admin tarafından belirtilen ilanın durumunu silindi olarak günceller.

8. **/rezer**:
   - **Metot**: GET.
   - **Açıklama**: Admin için tüm rezervasyonları listeler; ödeme ve yorum bilgileriyle birlikte.
   - **Template**: `admin_rezer.html`.

9. **/rezer_iptal/<rezers_id>,<rezers_kullanici>**:
   - **Metot**: GET.
   - **Açıklama**: Admin tarafından rezervasyonu iptal eder (`sp_iptal_rezervasyon`).

10. **/ilanlarim**:
    - **Metot**: GET.
    - **Açıklama**: Ev sahibinin kendi ilanlarını listeler.
    - **Template**: `ilanlarim.html`.

11. **/ilan_ekle**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Ev sahibinin yeni ilan eklemesini sağlar; resim yükleme desteklenir.
    - **Template**: `ilan_ekle.html`.

12. **/ilan_duzenle/<ilan_id>**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Ev sahibinin mevcut ilanı düzenlemesini sağlar.
    - **Template**: `ilan_duzenle.html`.

13. **/ilan_sil/<ilan_id>**:
    - **Metot**: GET.
    - **Açıklama**: Ev sahibinin kendi ilanını siler (durum silindi olur).

14. **/register**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Yeni kullanıcı kaydı yapar (`sp_kullanici_ekle`).
    - **Template**: `register.html`.

15. **/register2**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Admin tarafından yeni kullanıcı eklenmesini sağlar.
    - **Template**: `admin_ekle.html`.

16. **/reset**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Şifre sıfırlama işlemini gerçekleştirir.
    - **Template**: `reset.html`.

17. **/kullanici** (`kullanici_paneli`):
    - **Metot**: GET.
    - **Açıklama**: Kullanıcıların aktif ilanları filtreleyerek görmesini sağlar.
    - **Template**: `kullanici.html`.

18. **/rezervasyon/<ilan_id>**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Kullanıcıların rezervasyon yapmasını sağlar; ödeme bilgileri kaydedilir.
    - **Template**: `rezervasyon.html`.

19. **/rezervasyonlarim**:
    - **Metot**: GET.
    - **Açıklama**: Kullanıcının rezervasyonlarını listeler; yorum yapma durumu kontrol edilir.
    - **Template**: `rezervasyonlarim.html`.

20. **/evsahibi_rezervasyonlar**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Ev sahibinin rezervasyonlarını listeler.
    - **Template**: `evsahibi_rezervasyonlar.html`.

21. **/rezervasyon_iptal**:
    - **Metot**: POST.
    - **Açıklama**: Kullanıcı veya admin tarafından rezervasyon iptali (`sp_iptal_rezervasyon`).

22. **/rezervasyon_iptal1**:
    - **Metot**: POST.
    - **Açıklama**: Ev sahibi tarafından rezervasyon iptali.

23. **/rezervasyon_onay**:
    - **Metot**: POST.
    - **Açıklama**: Ev sahibinin rezervasyonu onaylaması.

24. **/yorum-gonder**:
    - **Metot**: POST.
    - **Açıklama**: Kullanıcının rezervasyona yorum ve puan eklemesi.

25. **/logout**:
    - **Metotlar**: GET, POST.
    - **Açıklama**: Kullanıcı oturumunu kapatır ve aktif durumunu günceller.

26. **/admin/verileri_guncelle**:
    - **Metot**: GET.
    - **Açıklama**: Admin paneli için istatistikleri JSON formatında döndürür.

## Algoritma ve Mantık

- **Giriş/Çıkış**: Kullanıcı girişi SHA-256 şifreleme ile doğrulanır. Oturum yönetimi Flask `session` ile yapılır.
- **İlan Yönetimi**: Ev sahipleri ilan ekler/düzenler/siler. İlanlar veritabanında `ilanlar` tablosuna kaydedilir; durumları aktif, pasif veya silindi olabilir.
- **Rezervasyon**: Kullanıcılar tarih aralığına göre ilanları rezerve eder. Çakışma kontrolü SQL sorguları ile yapılır.
- **Ödeme**: Ödeme bilgileri (`odemeler` tablosu) kaydedilir; kart numarası, son kullanma tarihi ve CVV doğrulaması yapılır.
- **Yorum**: Kullanıcılar, rezervasyon bitiş tarihinden sonra yorum bırakabilir.
- **Veritabanı**: SQL Server stored procedure'leri (`sp_kullanici_ekle`, `sp_iptal_rezervasyon`, `sp_rezervasyon_listele`) ve fonksiyonları (`fn_AktifIlanSayisi`, `fn_BeklemedeRezervasyonSayisi`, `fn_EvSahibiGelirHesapla`) kullanılır.

## Örnek Kullanım

### Giriş
- **Girdi**: E-posta: `kullanici@example.com`, Şifre: `sifre123`.
- **Çıktı**: Kullanıcı tipine göre ilgili panele yönlendirme (`/admin`, `/ev_sahibi`, `/kullanici`).

### İlan Ekleme
- **Girdi**: Başlık: "Deniz Manzaralı Ev", Fiyat: 500, Resim: `ev.jpg`.
- **Çıktı**: İlan veritabanına eklenir ve `ilanlarim` sayfasına yönlendirilir.

### Rezervasyon
- **Girdi**: İlan ID: 1, Tarih: 2025-06-15 - 2025-06-20, Kart: `1234567812345678`.
- **Çıktı**: Rezervasyon beklemede durumuyla kaydedilir.

## Sınırlamalar ve Varsayımlar

### Sınırlamalar
- Kart doğrulama sadece temel format kontrolü yapar (gerçek ödeme entegrasyonu yoktur).
- SQL injection önlenmiştir, ancak ek güvenlik katmanları (örneğin, prepared statements) güçlendirilebilir.
- Resim yükleme sadece belirli formatları destekler (png, jpg, jpeg, gif).

### Varsayımlar
- Veritabanı şeması önceden tanımlıdır (`kullanicilar`, `ilanlar`, `rezervasyon`, vb.).
- Kullanıcıların e-posta adresleri benzersizdir.
- Tarih formatı `%Y-%m-%d` veya `%Y-%m-%d %H:%M:%S` şeklindedir.
- Uygulamanın e-posta sisteminin çalışması için kendi e-posta adresinizi ve güvenlik anahtarını koda eklemeniz gerekmektedir.

## Hata Yönetimi

- Her veritabanı işlemi `try-except` bloğu ile sarılmıştır.
- Hatalar kullanıcıya flash mesajlarıyla bildirilir.
- Oturum kontrolü her kritik rotada yapılır.


## Uygulama içi görüntüler
<img width="1472" height="857" alt="Ekran görüntüsü 2026-01-12 140913" src="https://github.com/user-attachments/assets/5f179f55-f259-4c25-bcd1-ff4a96948f60" />

<img width="1918" height="871" alt="Ekran görüntüsü 2026-01-12 141158" src="https://github.com/user-attachments/assets/12f7c5fc-9a39-486b-9fa4-969b8bde417a" />
<img width="1913" height="868" alt="Ekran görüntüsü 2026-01-12 141217" src="https://github.com/user-attachments/assets/025987c3-d6ef-4c71-b808-cade1d254b67" />


