CREATE PROCEDURE sp_kullanici_ekle
    @kullanici_ad NVARCHAR(100),
    @eposta NVARCHAR(100),
    @sifre NVARCHAR(255),
    @kullanici_tipi NVARCHAR(50)
AS
BEGIN
    IF EXISTS (SELECT 1 FROM kullanicilar WHERE eposta = @eposta)
    BEGIN
        RAISERROR('Bu email adresi zaten kayıtlı.', 16, 1);
        RETURN;
    END

    INSERT INTO kullanicilar (kullanici_ad, eposta, sifre, kullanici_tipi)
    VALUES (@kullanici_ad, @eposta, @sifre, @kullanici_tipi);
END
GO

CREATE PROCEDURE sp_iptalrezervasyon
    @RezervasyonID INT,
    @KullaniciID INT,
    @KullaniciTuru VARCHAR(20),
    @IptalNedeni NVARCHAR(100)
AS
BEGIN
   
    IF @KullaniciTuru = 'admin'
    BEGIN
        UPDATE rezervasyon
        SET durum = 'iptal edildi',
            iptal_tarihi = GETDATE(),
            iptal_nedeni = @IptalNedeni
        WHERE rezervasyon_id = @RezervasyonID
    END

   
    ELSE IF @KullaniciTuru = 'kullanici'
    BEGIN
        UPDATE rezervasyon
        SET durum = 'iptal edildi',
            iptal_tarihi = GETDATE(),
            iptal_nedeni = @IptalNedeni
        WHERE rezervasyon_id = @RezervasyonID AND kullanici_id = @KullaniciID
    END

    
    ELSE IF @KullaniciTuru = 'ev_sahibi'
    BEGIN
        UPDATE rezervasyon
        SET durum = 'iptal edildi',
            iptal_tarihi = GETDATE(),
            iptal_nedeni = @IptalNedeni
        WHERE rezervasyon_id = @RezervasyonID AND ev_sahibi_id = @KullaniciID
    END
END
GO

CREATE PROCEDURE sp_rezervasyon_listele
    @kullanici_id INT = NULL,
    @ev_sahibi_id INT = NULL,
    @mod NVARCHAR(20)
AS
BEGIN
    
	IF @mod = 'admin'
    BEGIN
        SELECT 
           r.rezervasyon_id, r.ilan_id, r.adsoyad, r.email, r.telefon, 
           r.baslangic_tarihi, r.bitis_tarihi, r.toplam_fiyat, r.durum, 
           r.olusturma_tarihi, r.kullanici_id, r.iptal_nedeni,i.baslik,
           k.kullanici_ad
       FROM rezervasyon r
       JOIN ilanlar i ON r.ilan_id = i.ilan_id
       JOIN kullanicilar k ON r.kullanici_id = k.kullanici_id
       ORDER BY r.olusturma_tarihi DESC;
    END
    ELSE IF @mod = 'kullanici'
    BEGIN
        SELECT 
            r.rezervasyon_id, r.ilan_id, r.adsoyad, r.email, r.telefon,
            r.baslangic_tarihi, r.bitis_tarihi, r.toplam_fiyat,
            r.durum, r.olusturma_tarihi,
            i.baslik, i.adres
        FROM rezervasyon r
        JOIN ilanlar i ON r.ilan_id = i.ilan_id
        WHERE r.kullanici_id = @kullanici_id
        ORDER BY r.olusturma_tarihi DESC;
    END
    ELSE IF @mod = 'ev_sahibi'
    BEGIN
        SELECT 
            r.rezervasyon_id, r.ilan_id, r.adsoyad, r.email, r.telefon,
            r.baslangic_tarihi, r.bitis_tarihi, r.toplam_fiyat,
            r.durum, r.olusturma_tarihi,
            i.baslik, i.adres
        FROM rezervasyon r
        JOIN ilanlar i ON r.ilan_id = i.ilan_id
        WHERE r.ev_sahibi_id = @ev_sahibi_id
        ORDER BY r.olusturma_tarihi DESC;
    END
END;