
CREATE FUNCTION dbo.fn_EvSahibiGelirHesapla (@EvSahibiID INT)
RETURNS DECIMAL(10,2)
AS
BEGIN
    DECLARE @ToplamGelir DECIMAL(10,2)
    SELECT @ToplamGelir = ISNULL(SUM(toplam_fiyat), 0)
    FROM rezervasyon
    WHERE ev_sahibi_id = @EvSahibiID AND durum IN ('onaylandı', 'tamamlandı')
    RETURN @ToplamGelir
END
GO


CREATE FUNCTION dbo.fn_AktifIlanSayisi (@EvSahibiID INT)
RETURNS INT
AS
BEGIN
    DECLARE @AktifSayi INT;

    SELECT @AktifSayi = COUNT(*)
    FROM [ilanlar]
    WHERE [ev_sahibi_id] = @EvSahibiID
    AND [durum] = 'aktif';

    RETURN @AktifSayi;
END
GO


CREATE FUNCTION dbo.fn_BeklemedeRezervasyonSayisi (@EvSahibiID INT)
RETURNS INT
AS
BEGIN
    DECLARE @BeklemedeSayi INT;

    SELECT @BeklemedeSayi = COUNT(*)
    FROM [rezervasyon]
    WHERE [ev_sahibi_id] = @EvSahibiID
    AND [durum] = 'beklemede';

    RETURN @BeklemedeSayi;
END
GO