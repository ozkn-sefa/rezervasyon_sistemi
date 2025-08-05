CREATE TRIGGER trg_gun_gecti_mi
ON rezervasyon
AFTER UPDATE
AS
BEGIN
   
    IF UPDATE(bugün)
    BEGIN
        
        UPDATE rezervasyon
        SET durum = 'tamamlandı'
        WHERE durum = 'onaylandı'
          AND bitis_tarihi < CAST(GETDATE() AS DATE);

        
        UPDATE rezervasyon
        SET durum = 'iptal edildi'
        WHERE durum = 'beklemede'
          AND baslangic_tarihi < CAST(GETDATE() AS DATE);
    END
END;
GO
CREATE TRIGGER trg_kullanici_sil
ON kullanicilar
AFTER DELETE
AS
BEGIN
    UPDATE ilanlar
    SET durum = 'silindi'
    WHERE ev_sahibi_id IN (
        SELECT kullanici_id FROM deleted
    );
END;
GO
CREATE TRIGGER trg_rezervasyon_iptal
ON ilanlar 
AFTER UPDATE
AS
BEGIN
    IF UPDATE(durum)
    BEGIN
        UPDATE rezervasyon
        SET durum = 'iptal edildi'
        WHERE ilan_id IN (
            SELECT i.ilan_id
            FROM inserted i
            JOIN deleted d ON i.ilan_id = d.ilan_id
            WHERE i.durum = 'silindi' AND d.durum <> 'silindi'
        );
    END
END;