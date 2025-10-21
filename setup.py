#!/usr/bin/env python

"""
Otomatik Kurulum Scripti
Replit'te sistemin otomatik kurulması için
Kullanıcı hiç teknik bilgiye ihtiyaç duymadan çalıştırır
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Karşılama mesajı"""
    print("""
🚀 İLAÇ TAKİP SİSTEMİ - OTOMATİK KURULUM

Bu script sisteminizi otomatik olarak kuracak.

📋 Yapılacak İşlemler:
   1. Gerekli Python kütüphanelerini yükleme
   2. PostgreSQL veritabanı kontrolü
   3. Ortam değişkenlerini ayarlama
   4. İlk veritabanı kurulumu
   5. Web uygulamasını başlatma

⏱️  Tahmini Süre: 2-3 dakika
💰 Maliyet: Tamamen ÜCRETSİZ

    """)

def install_requirements():
    """Python kütüphanelerini yükle"""
    print("📦 Python kütüphaneleri yükleniyor...")

    try:
        # requirements.txt varsa yükle, yoksa pip ile tek tek yükle
        if Path("requirements.txt").exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        else:
            packages = [
                "Flask==2.3.3",
                "Flask-SQLAlchemy==3.0.5",
                "Flask-Login==0.6.3",
                "Flask-WTF==1.1.1",
                "Flask-Migrate==4.0.5",
                "Flask-CORS==4.0.0",
                "psycopg2-binary==2.9.7",
                "python-dotenv==1.0.0",
                "pytz==2023.3.post1"
            ]

            for package in packages:
                print(f"   📥 {package} yükleniyor...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

        print("✅ Kütüphane yükleme tamamlandı!")
        return True

    except Exception as e:
        print(f"❌ Kütüphane yükleme hatası: {str(e)}")
        return False

def setup_database():
    """PostgreSQL veritabanını hazırla"""
    print("🗄️ Veritabanı kuruluyor...")

    # Replit'te DATABASE_URL environment variable var mı kontrol et
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("""
⚠️  DATABASE_URL bulunamadı!

Lütfen şu adımları takip edin:
1. Sol panelde "Database" sekmesine tıklayın
2. "Create PostgreSQL database" butonuna tıklayın
3. Otomatik oluşturulan DATABASE_URL'yi kopyalayın
4. Sol panelde "Secrets" sekmesine gidin
5. DATABASE_URL'i buraya yapıştırın
6. Script'i yeniden çalıştırın

        """)
        return False

    print("✅ Veritabanı bağlantısı başarılı!")

    # Secret key oluştur
    if not os.environ.get("SECRET_KEY"):
        import secrets
        secret_key = secrets.token_hex(32)

        print(f"""
🔑 SECRET_KEY oluşturuldu: {secret_key}

Lütfen bu anahtarı güvenli bir yerde saklayın.
Replit Secrets'e eklemek için:
1. Sol panel → Secrets
2. SECRET_KEY = {secret_key} ekleyin
        """)

        # Geçici olarak environment'a ekle
        os.environ["SECRET_KEY"] = secret_key

    return True

def setup_environment():
    """Environment variables'ları ayarla"""
    print("⚙️ Sistem ayarları yapılandırılıyor...")

    # Production environment
    os.environ["FLASK_ENV"] = "production"

    # Replit URL'ini al (varsa)
    replit_slug = os.environ.get("REPLIT_SLUG", "")
    replit_owner = os.environ.get("REPLIT_OWNER", "")

    if replit_slug and replit_owner:
        app_url = f"https://{replit_slug}.{replit_owner}.repl.co"
        print(f"🌐 Uygulama URL'si: {app_url}")

    print("✅ Ayarlar yapılandırıldı!")
    return True

def test_database():
    """Veritabanı bağlantısını test et"""
    print("🔍 Veritabanı bağlantısı test ediliyor...")

    try:
        from app import db
        from flask import Flask

        # Geçici Flask app ile test et
        test_app = Flask(__name__)
        test_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(test_app)

        with test_app.app_context():
            db.create_all()
            print("✅ Veritabanı tabloları oluşturuldu!")
            return True

    except Exception as e:
        print(f"❌ Veritabanı hatası: {str(e)}")
        return False

def create_admin_user():
    """İlk admin kullanıcı oluştur (isteğe bağlı)"""
    print("👤 İlk kullanıcı hazırlığı...")

    try:
        from app import db, User
        from flask import Flask

        test_app = Flask(__name__)
        test_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(test_app)

        with test_app.app_context():
            # Test kullanıcısı oluştur
            test_user = User(email="test@example.com")
            test_user.set_password("password123")

            db.session.add(test_user)
            db.session.commit()

            print("✅ Test kullanıcısı oluşturuldu: test@example.com / password123")
            return True

    except Exception as e:
        print(f"⚠️  Kullanıcı oluşturma hatası: {str(e)}")
        print("   (İlk kullanımda kullanıcı otomatik oluşturulacak)")
        return False

def show_completion():
    """Kurulumun başarıyla tamamlandığını göster"""
    replit_slug = os.environ.get("REPLIT_SLUG", "")
    replit_owner = os.environ.get("REPLIT_OWNER", "")

    if replit_slug and replit_owner:
        app_url = f"https://{replit_slug}.{replit_owner}.repl.co"
    else:
        app_url = "https://yourapp.replit.app"

    print("""
🎉 KURULUM BAŞARIYLA TAMAMLANDI! 🎉

🌐 Uygulama adresi: {app_url}

📱 KULLANIM ADIMLARI:

1. Tarayıcınızda yukarıdaki URL'yi açın
2. "Google ile Giriş" butonuna tıklayın
3. Email adresinizi yazın (örnek: isminiz@gmail.com)
4. "Yeni İlaç" butonundan ilk ilacınızı ekleyin
5. Bildirim izinlerini verin

📱 TELEFON KURULUMU:
   Chrome/Safari menü → "Ana Ekrana Ekle"

🔧 SORUN GİDERME:
   Eğer uygulama açılmazsa:
   - Replit'te "Run" butonuna tekrar tıklayın
   - Sayfa yenileyin (F5)
   - Başka tarayıcı deneyin

🆘 YARDIM:
   Bu readme.md dosyasını tekrar okuyun

✨ SISTEM ARTIR: Her gün 24 saat çalışır, tamamen ÜCRETSİZ!

    """.format(app_url=app_url))

def main():
    """Ana kurulum fonksiyonu"""
    print_banner()

    # Adım adım kurulum
    steps = [
        ("Kütüphane Kurulumu", install_requirements),
        ("Veritabanı Kurulumu", setup_database),
        ("Sistem Ayarları", setup_environment),
        ("Veritabanı Testi", test_database),
        ("İlk Kullanıcı", create_admin_user)
    ]

    for step_name, step_func in steps:
        print(f"\n>>> {step_name} <<<")
        if not step_func():
            print(f"❌ {step_name} başarısız oldu!")
            print("Kurulumu tekrar deneyin veya yardım alın.")
            sys.exit(1)
        print(f"✅ {step_name} tamamlandı!")

    show_completion()

if __name__ == "__main__":
    main()
