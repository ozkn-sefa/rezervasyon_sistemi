from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import pyodbc
from datetime import date
import hashlib
import os
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__, template_folder='arayüz')
app.secret_key = '53535353'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def send_reservation_email(recipient_email, message):
    sender_email = "osefaa5353@gmail.com"
    app_password = "ztnz uufd ebhi oabj"


    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Rezervasyon Onay Bilgisi"


    msg.attach(MIMEText(message, 'plain', 'utf-8'))

    try:

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)


        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:

        return False
def connect_db():
    return pyodbc.connect(
        'DRIVER={SQL Server};SERVER=localhost;DATABASE=projeveritabanı;Trusted_Connection=yes;')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        conn, cursor = None, None
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE rezervasyon SET [bugün] = ?", (date.today().strftime("%Y-%m-%d"),))
            cursor.execute('SELECT [kullanici_id], [kullanici_ad], [sifre], [kullanici_tipi] FROM [kullanicilar] WHERE [eposta] = ?', email)
            result = cursor.fetchone()


            if not result:
                flash('Böyle bir kullanıcı bulunamadı!', 'error')
            else:
                userid, username, stored_password, user_type = result
                if stored_password == hash_password(password):
                    session['user_id'] = userid
                    session['username'] = username
                    session['user_type'] = user_type
                    cursor.execute('UPDATE [kullanicilar] SET [aktif] = 1 WHERE [kullanici_id] = ?', userid)
                    conn.commit()

                    if user_type == 'admin':
                        return redirect(url_for('admin_paneli'))
                    elif user_type == 'ev_sahibi':
                        return redirect(url_for('ev_sahibi_paneli'))
                    elif user_type == 'kullanici':
                        return redirect(url_for('kullanici_paneli'))
                else:
                    flash('Kullanıcı adı veya şifre yanlış!', 'error')
        except Exception as e:
            flash(f'Veritabanı hatası: {str(e)}', 'error')
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template('login.html')

@app.route('/ev_sahibi')
def ev_sahibi_paneli():
    if 'user_id' not in session or session.get('user_type') != 'ev_sahibi':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT [kullanici_ad] FROM [kullanicilar] WHERE [kullanici_id] = ?', (session['user_id'],))
        kullanici = cursor.fetchone()
        kullanici_adi = kullanici[0] if kullanici else 'Kullanıcı'

        cursor.execute('SELECT dbo.fn_AktifIlanSayisi(?)', (session['user_id'],))
        ilan_sayisi = cursor.fetchone()[0]

        cursor.execute('SELECT dbo.fn_BeklemedeRezervasyonSayisi(?)', (session['user_id'],))
        bekleyen_rezervasyon = cursor.fetchone()[0]

        # Toplam gelir için scalar fonksiyon kullanımı
        cursor.execute("SELECT dbo.fn_EvSahibiGelirHesapla(?)", (session['user_id'],))
        toplam_gelir = cursor.fetchone()[0]

    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return render_template('ev_sahibi.html',
                           kullanici_adi=kullanici_adi,
                           ilan_sayisi=ilan_sayisi,
                           bekleyen_rezervasyon=bekleyen_rezervasyon,
                           toplam_gelir=toplam_gelir)



@app.route('/admin')
def admin_paneli():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kullanicilar")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE aktif=1")
        active_user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM rezervasyon WHERE durum = 'onaylandı'")
        rezervasyon = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ilanlar WHERE durum='aktif'")
        ilanlar = cursor.fetchone()[0]
        return render_template('admin.html', user_count=user_count-1, active_user_count=active_user_count-1, rezervasyon=rezervasyon, ilanlar=ilanlar)
    except Exception as e:
        flash(f'Bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/kullanicilar')
def kullanicilar():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT kullanici_id, kullanici_ad, kullanici_tipi, eposta, kullanici_tarihi
            FROM kullanicilar
            WHERE kullanici_tipi IN ('kullanici', 'ev_sahibi')
        """)
        rows = cursor.fetchall()

        users = []
        for row in rows:
            tarih = row[4]
            # Tarih datetime objesi ise saniyeye kadar al
            if isinstance(tarih, datetime):
                tarih_str = tarih.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Eğer string ise milisaniyeyi sil
                tarih_str = str(tarih).split('.')[0]

            users.append({
                "id": row[0],
                "ad": row[1],
                "rol": row[2],
                "email": row[3],
                "tarih": tarih_str
            })

        return render_template('admin_kullanici.html', users=users)

    except Exception as e:
        flash(f'Bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('login'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/user_sil/<int:u_id>')
def user_sil(u_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('kullanicilar'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM [kullanicilar] WHERE [kullanici_id] = ?', (u_id,))
        user = cursor.fetchone()
        if not user:
            flash('Bu kullanıcıyı silme yetkiniz yok veya kullanıcı bulunamadı!', 'error')
            return redirect(url_for('kullanicilar'))

        cursor.execute('DELETE FROM [kullanicilar] WHERE [kullanici_id] = ?', (u_id,))
        conn.commit()
        flash('Kullanıcı başarıyla silindi!', 'success')
        return redirect(url_for('kullanicilar'))

    except Exception as e:
        flash(f'Veritabanı hatası: {str(e)}', 'error')
        return redirect(url_for('kullanicilar'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/ilanlar')
def ilanlar():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.ilan_id, k.kullanici_ad, i.baslik, i.fiyat, i.oda_sayisi, i.durum, i.ilan_tarihi, i.adres ,i.ev_sahibi_id
            FROM ilanlar i
            JOIN kullanicilar k ON i.ev_sahibi_id = k.kullanici_id
            WHERE i.durum IN ('aktif', 'pasif')
        """)

        rows = cursor.fetchall()

        ilanlar = []
        for row in rows:
            tarih = row[6]
            # Tarihi saniyeye kadar formatla
            if isinstance(tarih, datetime):
                tarih_str = tarih.strftime('%Y-%m-%d %H:%M:%S')
            else:
                tarih_str = str(tarih).split('.')[0]

            ilanlar.append({
                "id": row[0],
                "evsahibi": row[1],
                "baslik": row[2],
                "fiyat": row[3],
                "oda_sayisi": row[4],
                "durum": row[5],
                "tarih": tarih_str,
                "adres": row[7]
            })

        return render_template('admin_ilanlar.html', ilanlar=ilanlar)

    except Exception as e:
        flash(f'Bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('login'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/ailan_sil/<int:ilan_id>')
def ailan_sil(ilan_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM [ilanlar] WHERE [ilan_id] = ?', (ilan_id,))
        ailan = cursor.fetchone()
        if not ailan:
            flash('Bu ilanı silme yetkiniz yok veya ilan bulunamadı!', 'error')
            return redirect(url_for('ilanlar'))

            # Durumu 'silindi' olarak güncelle
        cursor.execute('UPDATE [ilanlar] SET [durum] = ? WHERE [ilan_id] = ?', ('silindi', ilan_id))
        conn.commit()
        flash('İlan başarıyla silindi!', 'success')
        return redirect(url_for('ilanlar'))

    except Exception as e:
        flash(f'Veritabanı hatası: {str(e)}', 'error')
        return redirect(url_for('ilanlar'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/rezer')
def rezer():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("EXEC sp_rezervasyon_listele @mod = ?", ('admin',))

        rows = cursor.fetchall()

        rezervasyon_listesi = []

        for row in rows:
            rezervasyon_id = row[0]
            cursor.execute("""
                SELECT kart_numara, kayit_tarihi, toplam_tutar
                FROM odemeler
                WHERE rezervasyon_id = ?
            """, (rezervasyon_id,))
            odeme = cursor.fetchone()

            cursor.execute("""
                SELECT yorum, puan, yorum_tarihi
                FROM yorumlar
                WHERE rezervasyon_id = ?
            """, (rezervasyon_id,))
            yorum = cursor.fetchone()

            rezervasyon_listesi.append({
                "ilan": {"id": row[1]},
                "adsoyad": row[2],
                "email": row[3],
                "telefon": row[4],
                "baslangic": row[5],
                "bitis": row[6],
                "fiyat": row[7],
                "durum": row[8],
                "tarih": row[9].strftime('%Y-%m-%d %H:%M:%S'),
                "kullanici": row[10],
                "id": rezervasyon_id,
                "neden": row[11],
                "baslik": row[12],
                "kullaniciad":row[13],

                "odeme": {
                    "kart": odeme[0][-4:] if odeme else "Yok",
                    "kayittarihi": odeme[1].strftime('%Y-%m-%d %H:%M:%S') if odeme and isinstance(odeme[1], datetime) else "Yok",
                    "tutar": odeme[2] if odeme else "Yok"
                },
                "yorum": {
                    "yorum": yorum[0] if yorum else None,
                    "puan": yorum[1] if yorum else None,
                    "tarih": yorum[2].strftime('%Y-%m-%d %H:%M:%S') if yorum and isinstance(yorum[2], datetime) else None
                } if yorum else None
            })

        return render_template('admin_rezer.html', rezervasyons=rezervasyon_listesi)

    except Exception as e:
        flash(f'Bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/ilanlarim')
def ilanlarim():
    if 'user_id' not in session or session.get('user_type') != 'ev_sahibi':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Kullanıcı adını çek
        cursor.execute('SELECT [kullanici_ad] FROM [kullanicilar] WHERE [kullanici_id] = ?', (session['user_id'],))
        kullanici = cursor.fetchone()
        kullanici_adi = kullanici[0] if kullanici else 'Kullanıcı'

        # Sadece aktif veya pasif ilanları çek
        cursor.execute('''
            SELECT [ilan_id], [baslik], [aciklama], [adres], [fiyat], [oda_sayisi], 
                   [kisi_sayisi], [resim_path], [durum]
            FROM [ilanlar] 
            WHERE [ev_sahibi_id] = ? AND [durum] IN ('aktif', 'pasif')
            ORDER BY [ilan_id] DESC
        ''', (session['user_id'],))

        columns = [column[0] for column in cursor.description]
        ilanlar = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return render_template('ilanlarim.html',
                               kullanici_adi=kullanici_adi,
                               ilanlar=ilanlar)
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/ilan_ekle', methods=['GET', 'POST'])
def ilan_ekle():
    if 'user_id' not in session or session.get('user_type') != 'ev_sahibi':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        baslik = request.form['baslik']
        aciklama = request.form['aciklama']
        adres = request.form['adres']
        fiyat = request.form['fiyat']
        oda_sayisi = request.form['oda_sayisi']
        kisi_sayisi = request.form['kisi_sayisi']
        resim = request.files['resim']

        if not resim or not allowed_file(resim.filename):
            flash('Geçersiz dosya formatı! Lütfen PNG, JPG, JPEG veya GIF uzantılı bir dosya yükleyin.', 'error')
            return render_template('ilan_ekle.html')

        filename = secure_filename(resim.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resim.save(filepath)

        conn, cursor = None, None
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO [ilanlar] ([ev_sahibi_id], [baslik], [aciklama], [adres], [fiyat], 
                [oda_sayisi], [kisi_sayisi], [resim_path], [durum])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'aktif')
            ''', (session['user_id'], baslik, aciklama, adres, fiyat, oda_sayisi, kisi_sayisi, filename))
            conn.commit()
            flash('İlan başarıyla eklendi!', 'success')
            return redirect(url_for('ilanlarim'))
        except Exception as e:
            flash(f'Veritabanı hatası: {str(e)}', 'error')
            return render_template('ilan_ekle.html')
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template('ilan_ekle.html')

@app.route('/ilan_duzenle/<int:ilan_id>', methods=['GET', 'POST'])
def ilan_duzenle(ilan_id):
    if 'user_id' not in session or session.get('user_type') != 'ev_sahibi':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT baslik, aciklama, adres, fiyat, oda_sayisi, kisi_sayisi, durum, resim_path 
            FROM ilanlar 
            WHERE ilan_id = ? AND ev_sahibi_id = ?
        ''', (ilan_id, session['user_id']))

        ilan = cursor.fetchone()

        if not ilan:
            flash('Bu ilanı düzenleme yetkiniz yok veya ilan bulunamadı!', 'error')
            return redirect(url_for('ilanlarim'))

        if request.method == 'GET':
            return render_template('ilan_duzenle.html',
                                   ilan_id=ilan_id,
                                   baslik=ilan[0],
                                   aciklama=ilan[1],
                                   adres=ilan[2],
                                   fiyat=ilan[3],
                                   oda_sayisi=ilan[4],
                                   kisi_sayisi=ilan[5],
                                   durum=ilan[6],
                                   resim_path=ilan[7])

        baslik = request.form['baslik']
        aciklama = request.form['aciklama']
        adres = request.form['adres']
        fiyat = request.form['fiyat']
        oda_sayisi = request.form['oda_sayisi']
        kisi_sayisi = request.form['kisi_sayisi']
        durum = request.form['durum']

        resim_path = None
        if 'resim' in request.files:
            file = request.files['resim']
            if file.filename != '':
                if not allowed_file(file.filename):
                    flash('Geçersiz dosya formatı! Lütfen PNG, JPG, JPEG veya GIF uzantılı bir dosya yükleyin.', 'error')
                    return render_template('ilan_duzenle.html', ilan_id=ilan_id, baslik=baslik, aciklama=aciklama, adres=adres, fiyat=fiyat, oda_sayisi=oda_sayisi, kisi_sayisi=kisi_sayisi, durum=durum, resim_path=ilan[7])
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(app.root_path, 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                resim_path = f'{filename}'

        if resim_path:
            cursor.execute('''
                UPDATE ilanlar SET
                    baslik = ?, aciklama = ?, adres = ?, fiyat = ?, oda_sayisi = ?, kisi_sayisi = ?, durum = ?, resim_path = ?
                WHERE ilan_id = ? AND ev_sahibi_id = ?
            ''', (baslik, aciklama, adres, fiyat, oda_sayisi, kisi_sayisi, durum, resim_path, ilan_id, session['user_id']))
        else:
            cursor.execute('''
                UPDATE ilanlar SET
                    baslik = ?, aciklama = ?, adres = ?, fiyat = ?, oda_sayisi = ?, kisi_sayisi = ?, durum = ?
                WHERE ilan_id = ? AND ev_sahibi_id = ?
            ''', (baslik, aciklama, adres, fiyat, oda_sayisi, kisi_sayisi, durum, ilan_id, session['user_id']))

        conn.commit()
        flash('İlan başarıyla güncellendi!', 'success')
        return redirect(url_for('ilanlarim'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('ilanlarim'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/ilan_sil/<int:ilan_id>')
def ilan_sil(ilan_id):
    if 'user_id' not in session or session.get('user_type') != 'ev_sahibi':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # İlan ev sahibine mi ait kontrolü
        cursor.execute('SELECT * FROM [ilanlar] WHERE [ilan_id] = ? AND [ev_sahibi_id] = ?', (ilan_id, session['user_id']))
        ilan = cursor.fetchone()
        if not ilan:
            flash('Bu ilanı silme yetkiniz yok veya ilan bulunamadı!', 'error')
            return redirect(url_for('ilanlarim'))

        # Durumu 'silindi' olarak güncelle
        cursor.execute('UPDATE [ilanlar] SET [durum] = ? WHERE [ilan_id] = ?', ('silindi', ilan_id))
        conn.commit()

        flash('İlan başarıyla silindi !', 'success')
        return redirect(url_for('ilanlarim'))

    except Exception as e:
        flash(f'Veritabanı hatası: {str(e)}', 'error')
        return redirect(url_for('ilanlarim'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        user_type = request.form.get('user_type', '').strip()

        if not username or not password or not user_type:
            flash('Kullanıcı adı, şifre ve kullanıcı türü boş olamaz!', 'error')
        else:
            conn, cursor = None, None
            try:
                hashed_pw = hash_password(password)
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("EXEC sp_kullanici_ekle ?, ?, ?, ?", (username, email, hashed_pw, user_type))
                conn.commit()
                flash('Kullanıcı başarıyla eklendi!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'error')
            finally:
                if cursor: cursor.close()
                if conn: conn.close()

    return render_template('register.html')

@app.route('/register2', methods=['GET', 'POST'])
def register2():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        user_type = request.form.get('user_type', '').strip()

        if not username or not password or not user_type:
            flash('Kullanıcı adı, şifre ve kullanıcı türü boş olamaz!', 'error')
        else:
            conn, cursor = None, None
            try:
                hashed_pw = hash_password(password)
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("EXEC sp_kullanici_ekle ?, ?, ?, ?", (username, email, hashed_pw, user_type))
                conn.commit()
                flash('Kullanıcı başarıyla eklendi!', 'success')
                return redirect(url_for('kullanicilar'))
            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'error')
            finally:
                if cursor: cursor.close()
                if conn: conn.close()

    return render_template('admin_ekle.html')


@app.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username'].strip()
        new_password = request.form['new_password'].strip()

        if not username or not new_password:
            flash('Kullanıcı adı ve yeni şifre boş olamaz!', 'error')
        else:
            conn, cursor = None, None
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM [kullanicilar] WHERE [eposta] = ?', username)
                if not cursor.fetchone():
                    flash('Böyle bir kullanıcı bulunamadı!', 'error')
                else:
                    hashed_pw = hash_password(new_password)
                    cursor.execute('UPDATE [kullanicilar] SET [sifre] = ? WHERE [eposta] = ?', (hashed_pw, username))
                    conn.commit()
                    flash('Şifre başarıyla sıfırlandı! Lütfen giriş yapın.', 'success')
                    return redirect(url_for('login'))
            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'error')
            finally:
                if cursor: cursor.close()
                if conn: conn.close()

    return render_template('reset.html')

@app.route('/kullanici')
def kullanici_paneli():
    if 'user_id' not in session or session.get('user_type') != 'kullanici':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        adres = request.args.get('adres', '').strip()
        fiyat = request.args.get('fiyat', '').strip()
        oda = request.args.get('oda', '').strip()
        kisi = request.args.get('kisi', '').strip()
        baslangic_tarihi = request.args.get('baslangic_tarihi', '').strip()
        bitis_tarihi = request.args.get('bitis_tarihi', '').strip()

        sql = """
            SELECT ilan_id, baslik, aciklama, adres, fiyat, oda_sayisi, kisi_sayisi, resim_path
            FROM ilanlar
            WHERE durum = 'aktif'
        """
        params = []

        if adres:
            sql += " AND adres LIKE ?"
            params.append(f"%{adres}%")
        if fiyat:
            sql += " AND fiyat <= ?"
            params.append(fiyat)
        if oda:
            sql += " AND oda_sayisi = ?"
            params.append(oda)
        if kisi:
            sql += " AND kisi_sayisi = ?"
            params.append(kisi)

        if baslangic_tarihi and bitis_tarihi:
            sql += """
                AND ilan_id NOT IN (
                    SELECT ilan_id FROM rezervasyon
                    WHERE (
                        (baslangic_tarihi BETWEEN ? AND ?) OR 
                        (bitis_tarihi BETWEEN ? AND ?)
                    )
                    AND durum IN ('onaylandı', 'beklemede')
                )
            """
            params.extend([baslangic_tarihi, bitis_tarihi, baslangic_tarihi, bitis_tarihi])

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        ilanlar = [
            {
                'ilan_id': row.ilan_id,
                'baslik': row.baslik,
                'aciklama': row.aciklama,
                'adres': row.adres,
                'fiyat': row.fiyat,
                'oda_sayisi': row.oda_sayisi,
                'kisi_sayisi': row.kisi_sayisi,
                'resim_path': row.resim_path
            }
            for row in rows
        ]

        return render_template('kullanici.html', ilanlar=ilanlar)

    except Exception as e:
        flash(f'Hata oluştu: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

from datetime import datetime, timedelta


@app.route('/rezervasyon/<int:ilan_id>', methods=['GET', 'POST'])
def rezervasyon_yap(ilan_id):
    if 'user_id' not in session:
        flash('Rezervasyon yapmak için lütfen giriş yapın!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ilan_id, baslik, fiyat, kisi_sayisi, resim_path, ev_sahibi_id, oda_sayisi, adres, aciklama
            FROM ilanlar 
            WHERE ilan_id = ? AND durum = 'aktif'
        """, (ilan_id,))
        ilan = cursor.fetchone()

        if ilan is None:
            flash('İlan bulunamadı veya pasif durumda!', 'error')
            return redirect(url_for('kullanici_paneli'))

        cursor.execute("""
                    SELECT baslangic_tarihi, bitis_tarihi
                    FROM rezervasyon
                    WHERE ilan_id = ? AND durum IN ('beklemede', 'onaylandı')
                """, (ilan_id,))
        rezerve_gunler = []
        for baslangic, bitis in cursor.fetchall():
            # Convert strings to datetime objects
            baslangic_dt = datetime.strptime(baslangic, '%Y-%m-%d')
            bitis_dt = datetime.strptime(bitis, '%Y-%m-%d')
            gun = baslangic_dt
            while gun <= bitis_dt:
                rezerve_gunler.append(gun.strftime('%Y-%m-%d'))
                gun += timedelta(days=1)

        if request.method == 'POST':
            adsoyad = request.form['adsoyad'].strip()
            email = request.form['email'].strip().lower()
            telefon = request.form['telefon'].strip()
            baslangic_tarihi = request.form['baslangic_tarihi']
            bitis_tarihi = request.form['bitis_tarihi']
            kullanici_id = session['user_id']

            kart_adi = request.form['kart_adi'].strip().upper()
            kart_numara = request.form['kart_numara'].strip().replace(" ", "").replace("-", "")
            kart_son_kullanim = request.form['kart_son_kullanim'].strip()
            kart_cvv = request.form['kart_cvv'].strip()

            try:
                baslangic_dt = datetime.strptime(baslangic_tarihi, '%Y-%m-%d')
                bitis_dt = datetime.strptime(bitis_tarihi, '%Y-%m-%d')

                if baslangic_dt >= bitis_dt:
                    flash('Başlangıç tarihi bitiş tarihinden önce olmalıdır!', 'error')
                    return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

                rezervasyon_suresi = (bitis_dt - baslangic_dt).days or 1

                try:
                    kart_son_ay, kart_son_yil = kart_son_kullanim.split('/')
                    kart_son_tarih = datetime(int("20" + kart_son_yil), int(kart_son_ay), 1)
                    if kart_son_tarih < datetime.now():
                        flash('Kartın son kullanma tarihi geçmiş!', 'error')
                        return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)
                except ValueError:
                    flash('Geçersiz kart son kullanma tarihi formatı (AA/YY olmalı)!', 'error')
                    return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

                if not (len(kart_numara) == 16 and kart_numara.isdigit()):
                    flash('Geçersiz kart numarası (16 haneli olmalı)!', 'error')
                    return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

                if not (len(kart_cvv) in (3, 4) and kart_cvv.isdigit()):
                    flash('Geçersiz CVV kodu (3 veya 4 haneli olmalı)!', 'error')
                    return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

                # Kullanıcının çakışan rezervasyonu var mı?
                cursor.execute("""
                    SELECT 1 FROM rezervasyon
                    WHERE kullanici_id = ? AND (
                        (baslangic_tarihi <= ? AND bitis_tarihi >= ?) OR
                        (baslangic_tarihi <= ? AND bitis_tarihi >= ?) OR
                        (baslangic_tarihi >= ? AND bitis_tarihi <= ?)
                    )
                    AND durum IN ('beklemede', 'onaylandı')
                """, (kullanici_id, bitis_dt, baslangic_dt,
                      baslangic_dt, bitis_dt, baslangic_dt, bitis_dt))
                if cursor.fetchone():
                    flash('Bu tarih aralığında başka bir rezervasyonunuz zaten var!', 'error')
                    return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

                # İlan çakışması kontrolü
                cursor.execute("""
                    SELECT 1 FROM rezervasyon
                    WHERE ilan_id = ? AND (
                        (baslangic_tarihi <= ? AND bitis_tarihi >= ?) OR
                        (baslangic_tarihi <= ? AND bitis_tarihi >= ?) OR
                        (baslangic_tarihi >= ? AND bitis_tarihi <= ?)
                    )
                    AND durum IN ('beklemede', 'onaylandı')
                """, (ilan_id, bitis_dt, baslangic_dt,
                      baslangic_dt, bitis_dt, baslangic_dt, bitis_dt))
                if cursor.fetchone():
                    flash('Bu tarih aralığı için ilan zaten rezerve edilmiş!', 'error')
                    return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

                toplam_fiyat = ilan[2] * rezervasyon_suresi
                ev_sahibi_id = ilan[5]

                cursor.execute("""
                    INSERT INTO rezervasyon (
                        ilan_id, kullanici_id, ev_sahibi_id, adsoyad, email, telefon,
                        baslangic_tarihi, bitis_tarihi, toplam_fiyat,
                        durum, olusturma_tarihi
                    )
                    OUTPUT INSERTED.rezervasyon_id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'beklemede', GETDATE())
                """, (
                    ilan_id, kullanici_id, ev_sahibi_id, adsoyad, email, telefon,
                    baslangic_dt, bitis_dt, toplam_fiyat
                ))
                rezervasyon_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO odemeler (
                        kullanici_id, ilan_id, rezervasyon_id, kart_adi, kart_numara, 
                        kart_son_kullanim, kart_cvv, toplam_tutar
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kullanici_id, ilan_id, rezervasyon_id, kart_adi, kart_numara,
                    kart_son_kullanim, kart_cvv, toplam_fiyat
                ))

                conn.commit()
                # Prepare email message with reservation details
                reservation_details = (
                    f"Sayin {adsoyad},\n\n"
                    f"Rezervasyonunuz basariyla olusturulmustur!\n\n"
                    f"Rezervasyon Bilgileri:\n"
                    f"Ilan: {ilan[1]}\n"
                    f"Baslangic Tarihi: {baslangic_tarihi}\n"
                    f"Bitis Tarihi: {bitis_tarihi}\n"
                    f"Toplam Fiyat: {toplam_fiyat} TL\n"
                    f"Adres: {ilan[7]}\n\n"
                    f"Rezervasyonunuz ev sahibi tarafindan onaylandiginda size tekrar bilgilendirme yapilacaktir.\n"
                    f"Iyi tatiller dileriz!"
                )

                # Send confirmation email
                if send_reservation_email(email, reservation_details):
                    flash('Rezervasyon başarıyla oluşturuldu ve onay e-postası gönderildi! Onay bekleniyor.', 'success')
                else:
                    flash('Rezervasyon başarıyla oluşturuldu ancak e-posta gönderimi başarısız oldu! Onay bekleniyor.',
                          'warning')

                return redirect(url_for('kullanici_paneli'))

            except ValueError as e:
                flash(f'Geçersiz veri formatı: {str(e)}', 'error')
                return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

            except Exception as e:
                conn.rollback()
                flash(f'Rezervasyon oluşturulurken hata oluştu: {str(e)}', 'error')
                return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

        return render_template('rezervasyon.html', ilan=ilan, rezerve_gunler=rezerve_gunler)

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Sistem hatası: {str(e)}', 'error')
        return redirect(url_for('kullanici_paneli'))

    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/rezervasyonlarim')
def rezervasyonlarim():
    if 'user_id' not in session:
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    bugun = date.today()
    conn, cursor = None, None

    try:
        kullanici_id = session['user_id']
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("EXEC sp_rezervasyon_listele @kullanici_id = ?, @mod = ?", (kullanici_id, 'kullanici'))

        columns = [col[0] for col in cursor.description]
        rezervasyonlar_raw = [dict(zip(columns, row)) for row in cursor.fetchall()]
        rezervasyonlar = []

        for rezervasyon in rezervasyonlar_raw:
            for key in ['baslangic_tarihi', 'bitis_tarihi', 'olusturma_tarihi']:
                if isinstance(rezervasyon[key], datetime):
                    rezervasyon[key] = rezervasyon[key].strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT kart_numara, kayit_tarihi, toplam_tutar
                FROM [odemeler]
                WHERE rezervasyon_id = ?
            """, (rezervasyon['rezervasyon_id'],))
            odeme = cursor.fetchone()
            odeme_bilgi = {
                'kart_numara': str(odeme[0])[-4:] if odeme else "Yok",
                'kayit_tarihi': odeme[1].strftime('%Y-%m-%d %H:%M') if odeme and isinstance(odeme[1], datetime) else "Yok",
                'toplam_tutar': odeme[2] if odeme else "Yok"
            } if odeme else None

            cursor.execute("""
                SELECT yorum, puan, yorum_tarihi
                FROM [yorumlar]
                WHERE rezervasyon_id = ?
            """, (rezervasyon['rezervasyon_id'],))
            yorum = cursor.fetchone()
            yorum_bilgi = {
                'yorum': yorum[0],
                'puan': yorum[1],
                'yorum_tarihi': yorum[2].strftime('%Y-%m-%d %H:%M') if yorum and isinstance(yorum[2], datetime) else str(yorum[2])
            } if yorum else None

            rezervasyonlar.append({
                'rezervasyon_id': rezervasyon['rezervasyon_id'],
                'ilan': {
                    'baslik': rezervasyon['baslik'],
                    'adres': rezervasyon['adres'],
                },
                'adsoyad': rezervasyon['adsoyad'],
                'email': rezervasyon['email'],
                'telefon': rezervasyon['telefon'],
                'baslangic_tarihi': rezervasyon['baslangic_tarihi'],
                'bitis_tarihi': rezervasyon['bitis_tarihi'],
                'toplam_fiyat': rezervasyon['toplam_fiyat'],
                'olusturma_tarihi': rezervasyon['olusturma_tarihi'],
                'durum': rezervasyon['durum'],
                'odeme': odeme_bilgi,
                'yorum': yorum_bilgi,
                'yorum_yapilabilir': not yorum and datetime.strptime(rezervasyon['bitis_tarihi'], '%Y-%m-%d').date() < bugun and rezervasyon['durum'] == 'onaylandı'
            })

        return render_template('rezervasyonlarim.html', rezervasyonlar=rezervasyonlar)

    except Exception as e:
        flash(f'Rezervasyonlar getirilirken hata oluştu: {str(e)}', 'error')
        return redirect(url_for('kullanici_paneli'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/evsahibi_rezervasyonlar', methods=['GET', 'POST'])
def evsahibi_rezervasyonlar():
    if 'user_id' not in session or session.get('user_type') != 'ev_sahibi':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    conn, cursor = None, None
    try:
        ev_sahibi_id = session['user_id']
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("EXEC sp_rezervasyon_listele @ev_sahibi_id = ?, @mod = ?", (ev_sahibi_id, 'ev_sahibi'))

        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        rezervasyonlar = []

        for rezervasyon in rows:
            for key in ['baslangic_tarihi', 'bitis_tarihi', 'olusturma_tarihi']:
                if isinstance(rezervasyon[key], datetime):
                    rezervasyon[key] = rezervasyon[key].strftime('%Y-%m-%d')
                elif isinstance(rezervasyon[key], str):
                    try:
                        rezervasyon[key] = datetime.strptime(rezervasyon[key], '%Y-%m-%d').strftime('%Y-%m-%d')
                    except ValueError:
                        pass

            cursor.execute("""
                SELECT kart_numara, kayit_tarihi, toplam_tutar
                FROM [odemeler]
                WHERE rezervasyon_id = ?
            """, (rezervasyon['rezervasyon_id'],))
            odeme = cursor.fetchone()

            odeme_bilgi = {
                'kart_numara': str(odeme[0])[-4:] if odeme else "Yok",
                'kayit_tarihi': odeme[1].strftime('%Y-%m-%d %H:%M') if odeme and isinstance(odeme[1], datetime) else "Yok",
                'toplam_tutar': odeme[2] if odeme else "Yok"
            } if odeme else None

            cursor.execute("""
                SELECT yorum, puan, yorum_tarihi
                FROM [yorumlar]
                WHERE rezervasyon_id = ?
            """, (rezervasyon['rezervasyon_id'],))
            yorum = cursor.fetchone()
            yorum_bilgi = {
                'yorum': yorum[0],
                'puan': yorum[1],
                'yorum_tarihi': yorum[2].strftime('%Y-%m-%d %H:%M') if yorum and isinstance(yorum[2], datetime) else str(yorum[2])
            } if yorum else None

            rezervasyonlar.append({
                'rezervasyon_id': rezervasyon['rezervasyon_id'],
                'ilan': {
                    'baslik': rezervasyon['baslik'],
                    'adres': rezervasyon['adres'],
                },
                'adsoyad': rezervasyon['adsoyad'],
                'email': rezervasyon['email'],
                'telefon': rezervasyon['telefon'],
                'baslangic_tarihi': rezervasyon['baslangic_tarihi'],
                'bitis_tarihi': rezervasyon['bitis_tarihi'],
                'toplam_fiyat': rezervasyon['toplam_fiyat'],
                'olusturma_tarihi': rezervasyon['olusturma_tarihi'],
                'durum': rezervasyon['durum'],
                'odeme': odeme_bilgi,
                'yorum': yorum_bilgi
            })

        return render_template('evsahibi_rezervasyonlar.html', rezervasyonlar=rezervasyonlar)

    except Exception as e:
        flash(f'Rezervasyonlar getirilirken hata oluştu: {str(e)}', 'error')
        return redirect(url_for('ev_sahibi_paneli'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/rezervasyon_iptal', methods=['POST'])
def rezervasyon_iptal():
    if 'user_id' not in session:
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    rezervasyon_id = request.form.get('rezervasyon_id')
    kullanici_id = session['user_id']

    if not rezervasyon_id:
        flash('Rezervasyon ID bulunamadı!', 'error')
        return redirect(url_for('rezervasyonlarim'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.kullanici_id, r.durum, r.baslangic_tarihi, r.email, r.adsoyad, 
                   i.baslik, r.bitis_tarihi, i.adres, r.toplam_fiyat
            FROM [rezervasyon] r
            JOIN [ilanlar] i ON r.ilan_id = i.ilan_id
            WHERE r.rezervasyon_id = ?
        """, (rezervasyon_id,))
        result = cursor.fetchone()

        if not result or result[0] != kullanici_id:
            flash('Bu rezervasyon sizin hesabınıza ait değil veya bulunamadı!', 'error')
            return redirect(url_for('rezervasyonlarim'))

        durum, baslangic_tarihi = result[1], result[2]
        now = datetime.now()

        if isinstance(baslangic_tarihi, str):
            try:
                baslangic_tarihi = datetime.strptime(baslangic_tarihi, '%Y-%m-%d')
            except ValueError:
                flash('Başlangıç tarihi biçimi geçersiz!', 'error')
                return redirect(url_for('rezervasyonlarim'))

        if durum not in ['beklemede', 'onaylandı']:
            flash('Sadece beklemede veya onaylanmış rezervasyonlar iptal edilebilir!', 'error')
            return redirect(url_for('rezervasyonlarim'))

        if now >= baslangic_tarihi:
            flash('Rezervasyon tarihi geçtiği için iptal edilemez!', 'error')
            return redirect(url_for('rezervasyonlarim'))

        iptal_nedeni = 'Kullanıcı tarafından iptal edildi'
        cursor.execute("""
            UPDATE [rezervasyon]
            SET durum = 'iptal edildi',
                iptal_tarihi = GETDATE(),
                iptal_nedeni = ?
            WHERE rezervasyon_id = ? AND kullanici_id = ?
        """, (iptal_nedeni, rezervasyon_id, kullanici_id))

        conn.commit()

        # Prepare email message with cancellation details
        email, adsoyad, baslik, bitis_tarihi, adres, toplam_fiyat = result[3:9]
        cancellation_message = (
            f"Sayın {adsoyad},\n\n"
            f"Rezervasyonunuz iptal edilmiştir.\n\n"
            f"İptal Nedeni: {iptal_nedeni}\n\n"
            f"Rezervasyon Bilgileri:\n"
            f"İlan: {baslik}\n"
            f"Başlangıç Tarihi: {baslangic_tarihi}\n"
            f"Bitiş Tarihi: {bitis_tarihi}\n"
            f"Toplam Fiyat: {toplam_fiyat} TL\n"
            f"Adres: {adres}\n\n"
            f"Başka bir rezervasyon için sizi tekrar bekleriz!"
        )

        # Send cancellation email
        if send_reservation_email(email, cancellation_message):
            flash('Rezervasyon başarıyla iptal edildi ve iptal e-postası gönderildi!', 'success')
        else:
            flash('Rezervasyon başarıyla iptal edildi ancak e-posta gönderimi başarısız oldu!', 'warning')

        return redirect(url_for('rezervasyonlarim'))

    except Exception as e:
        flash(f'İptal işlemi sırasında hata oluştu: {str(e)}', 'error')
        return redirect(url_for('rezervasyonlarim'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/rezervasyon_iptal1', methods=['POST'])
def rezervasyon_iptal1():
    if 'user_id' not in session:
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    rezervasyon_id = request.form.get('rezervasyon_id')
    ev_sahibi_id = session['user_id']

    if not rezervasyon_id:
        flash('Rezervasyon ID bulunamadı!', 'error')
        return redirect(url_for('evsahibi_rezervasyonlar'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.ev_sahibi_id, r.durum, r.bitis_tarihi, r.email, r.adsoyad, 
                   i.baslik, r.baslangic_tarihi, i.adres, r.toplam_fiyat
            FROM [rezervasyon] r
            JOIN [ilanlar] i ON r.ilan_id = i.ilan_id
            WHERE r.rezervasyon_id = ?
        """, (rezervasyon_id,))
        result = cursor.fetchone()

        if not result or result[0] != ev_sahibi_id:
            flash('Bu rezervasyon sizin hesabınıza ait değil veya bulunamadı!', 'error')
            return redirect(url_for('evsahibi_rezervasyonlar'))

        durum, bitis_tarihi = result[1], result[2]
        now = datetime.now()

        if isinstance(bitis_tarihi, str):
            try:
                bitis_tarihi = datetime.strptime(bitis_tarihi, '%Y-%m-%d')
            except ValueError:
                flash('Bitiş tarihi biçimi geçersiz!', 'error')
                return redirect(url_for('evsahibi_rezervasyonlar'))

        if bitis_tarihi.date() < now.date():
            flash('Tarihi geçmiş rezervasyonlar iptal edilemez!', 'error')
            return redirect(url_for('evsahibi_rezervasyonlar'))

        if durum not in ['beklemede', 'onaylandı']:
            flash('Sadece beklemede veya onaylanmış rezervasyonlar iptal edilebilir!', 'error')
            return redirect(url_for('evsahibi_rezervasyonlar'))

        iptal_nedeni = 'Ev sahibi tarafından iptal edildi'
        cursor.execute("""
            UPDATE [rezervasyon]
            SET durum = 'iptal edildi',
                iptal_tarihi = GETDATE(),
                iptal_nedeni = ?
            WHERE rezervasyon_id = ? AND ev_sahibi_id = ?
        """, (iptal_nedeni, rezervasyon_id, ev_sahibi_id))

        conn.commit()

        # Prepare email message with cancellation details
        email, adsoyad, baslik, baslangic_tarihi, adres, toplam_fiyat = result[3:9]
        cancellation_message = (
            f"Sayın {adsoyad},\n\n"
            f"Rezervasyonunuz iptal edilmiştir.\n\n"
            f"İptal Nedeni: {iptal_nedeni}\n\n"
            f"Rezervasyon Bilgileri:\n"
            f"İlan: {baslik}\n"
            f"Başlangıç Tarihi: {baslangic_tarihi}\n"
            f"Bitiş Tarihi: {bitis_tarihi}\n"
            f"Toplam Fiyat: {toplam_fiyat} TL\n"
            f"Adres: {adres}\n\n"
            f"Başka bir rezervasyon için sizi tekrar bekleriz!"
        )

        # Send cancellation email
        if send_reservation_email(email, cancellation_message):
            flash('Rezervasyon başarıyla iptal edildi ve iptal e-postası gönderildi!', 'success')
        else:
            flash('Rezervasyon başarıyla iptal edildi ancak e-posta gönderimi başarısız oldu!', 'warning')

        return redirect(url_for('evsahibi_rezervasyonlar'))

    except Exception as e:
        flash(f'İptal işlemi sırasında hata oluştu: {str(e)}', 'error')
        return redirect(url_for('evsahibi_rezervasyonlar'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/rezer_iptal/<int:rezers_id>,<int:rezers_kullanici>')
def rezer_iptal(rezers_id, rezers_kullanici):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    if not rezers_id:
        flash('Rezervasyon ID bulunamadı!', 'error')
        return redirect(url_for('rezer'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.email, r.adsoyad, i.baslik, r.baslangic_tarihi, r.bitis_tarihi, 
                   i.adres, r.toplam_fiyat
            FROM [rezervasyon] r
            JOIN [ilanlar] i ON r.ilan_id = i.ilan_id
            WHERE r.rezervasyon_id = ?
        """, (rezers_id,))
        result = cursor.fetchone()

        if not result:
            flash('Rezervasyon bulunamadı!', 'error')
            return redirect(url_for('rezer'))

        iptal_nedeni = 'Admin tarafından iptal edildi'
        kullanici_turu = 'admin'

        cursor.execute("""
            EXEC sp_iptal_rezervasyon 
                @RezervasyonID=?, 
                @KullaniciID=?, 
                @KullaniciTuru=?, 
                @IptalNedeni=?
        """, (rezers_id, rezers_kullanici, kullanici_turu, iptal_nedeni))

        conn.commit()

        # Prepare email message with cancellation details
        email, adsoyad, baslik, baslangic_tarihi, bitis_tarihi, adres, toplam_fiyat = result
        cancellation_message = (
            f"Sayın {adsoyad},\n\n"
            f"Rezervasyonunuz iptal edilmiştir.\n\n"
            f"İptal Nedeni: {iptal_nedeni}\n\n"
            f"Rezervasyon Bilgileri:\n"
            f"İlan: {baslik}\n"
            f"Başlangıç Tarihi: {baslangic_tarihi}\n"
            f"Bitiş Tarihi: {bitis_tarihi}\n"
            f"Toplam Fiyat: {toplam_fiyat} TL\n"
            f"Adres: {adres}\n\n"
            f"Başka bir rezervasyon için sizi tekrar bekleriz!"
        )

        # Send cancellation email
        if send_reservation_email(email, cancellation_message):
            flash('Rezervasyon başarıyla iptal edildi ve iptal e-postası gönderildi!', 'success')
        else:
            flash('Rezervasyon başarıyla iptal edildi ancak e-posta gönderimi başarısız oldu!', 'warning')

        return redirect(url_for('rezer'))

    except Exception as e:
        flash(f'İptal işlemi sırasında hata oluştu: {str(e)}', 'error')
        return redirect(url_for('rezer'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/rezervasyon_onay', methods=['POST'])
def rezervasyon_onay():
    if 'user_id' not in session or session.get('user_type') != 'ev_sahibi':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    rezervasyon_id = request.form.get('rezervasyon_id')
    ev_sahibi_id = session['user_id']

    if not rezervasyon_id:
        flash('Rezervasyon ID bulunamadı!', 'error')
        return redirect(url_for('evsahibi_rezervasyonlar'))

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.ev_sahibi_id, r.durum, r.email, r.adsoyad, i.baslik, r.baslangic_tarihi, 
                   r.bitis_tarihi, i.adres, r.toplam_fiyat
            FROM [rezervasyon] r
            JOIN [ilanlar] i ON r.ilan_id = i.ilan_id
            WHERE r.rezervasyon_id = ?
        """, (rezervasyon_id,))
        result = cursor.fetchone()

        if not result or result[0] != ev_sahibi_id:
            flash('Bu rezervasyon sizin hesabınıza ait değil veya bulunamadı!', 'error')
            return redirect(url_for('evsahibi_rezervasyonlar'))

        durum = result[1]
        if durum != 'beklemede':
            flash('Sadece beklemede olan rezervasyonlar onaylanabilir!', 'error')
            return redirect(url_for('evsahibi_rezervasyonlar'))

        cursor.execute("""
            UPDATE [rezervasyon]
            SET durum = 'onaylandı'
            WHERE rezervasyon_id = ? AND ev_sahibi_id = ?
        """, (rezervasyon_id, ev_sahibi_id))

        conn.commit()

        # Prepare email message with approval details
        email, adsoyad, baslik, baslangic_tarihi, bitis_tarihi, adres, toplam_fiyat = result[2:9]
        approval_message = (
            f"Sayın {adsoyad},\n\n"
            f"Rezervasyonunuz onaylanmıştır!\n\n"
            f"Rezervasyon Bilgileri:\n"
            f"İlan: {baslik}\n"
            f"Başlangıç Tarihi: {baslangic_tarihi}\n"
            f"Bitiş Tarihi: {bitis_tarihi}\n"
            f"Toplam Fiyat: {toplam_fiyat} TL\n"
            f"Adres: {adres}\n\n"
            f"İyi tatiller dileriz!"
        )

        # Send approval email
        if send_reservation_email(email, approval_message):
            flash('Rezervasyon başarıyla onaylandı ve onay e-postası gönderildi!', 'success')
        else:
            flash('Rezervasyon başarıyla onaylandı ancak e-posta gönderimi başarısız oldu!', 'warning')

        return redirect(url_for('evsahibi_rezervasyonlar'))

    except Exception as e:
        flash(f'Onay işlemi sırasında hata oluştu: {str(e)}', 'error')
        return redirect(url_for('evsahibi_rezervasyonlar'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/yorum-gonder', methods=['POST'])
def yorum_gonder():
    if 'user_id' not in session:
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))

    rezervasyon_id = request.form['rezervasyon_id']
    yorum = request.form['yorum']
    puan = int(request.form['puan'])

    conn, cursor = None, None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM yorumlar WHERE rezervasyon_id = ?
        """, (rezervasyon_id,))
        yorum_var_mi = cursor.fetchone()[0]

        if yorum_var_mi:
            flash('Bu rezervasyon için zaten yorum yapmışsınız!', 'warning')
            return redirect(url_for('rezervasyonlarim'))

        cursor.execute("""
            INSERT INTO yorumlar (rezervasyon_id, yorum, puan, yorum_tarihi)
            VALUES (?, ?, ?, GETDATE())
        """, (rezervasyon_id, yorum, puan))

        conn.commit()
        flash('Yorumunuz başarıyla kaydedildi!', 'success')
        return redirect(url_for('rezervasyonlarim'))

    except Exception as e:
        flash(f'Yorum kaydedilirken bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('rezervasyonlarim'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    user_id = session.get('user_id')
    if user_id:
        conn, cursor = None, None
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE [kullanicilar] SET [aktif] = 0 WHERE [kullanici_id] = ?', (user_id,))
            conn.commit()
        except Exception as e:
            flash(f'Çıkış işlemi sırasında hata oluştu: {str(e)}', 'error')
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    session.clear()

    return redirect(url_for('login'))

@app.route('/admin/verileri_guncelle')
def verileri_guncelle():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return jsonify({'error': 'Yetkisiz erişim'}), 403

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kullanicilar")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE aktif=1")
        active_user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rezervasyon WHERE durum = 'onaylandı'")
        rezervasyon = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ilanlar WHERE durum='aktif'")
        ilanlar = cursor.fetchone()[0]

        return jsonify({
            'user_count': user_count-1,
            'active_user_count': active_user_count-1,
            'rezervasyon': rezervasyon,
            'ilanlar': ilanlar
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


if (__name__ == '__main__'):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)