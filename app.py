"""
İlaç Takip Sistemi - Production Ready Flask App
Railway Deployment ile 24/7 Çalışan Sistem
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
import uuid
import logging
import os
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Cross-Origin Resource Sharing ayarları

# Template folder setup
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
app.static_folder = os.path.join(os.path.dirname(__file__), 'static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
# Replit için Database URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/dbname')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['WTF_CSRF_ENABLED'] = True

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    medications = db.relationship('Medication', backref='user', lazy=True, cascade='all, delete-orphan')
    measurements = db.relationship('Measurement', backref='user', lazy=True, cascade='all, delete-orphan')
    taken_medications = db.relationship('TakenMedication', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Medication(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    time = db.Column(db.Time, nullable=False)
    period = db.Column(db.String(20), default='daily')  # daily, weekly, custom
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    last_taken = db.Column(db.DateTime)

class TakenMedication(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    medication_id = db.Column(db.String(36), db.ForeignKey('medication.id'), nullable=False)
    taken_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    date = db.Column(db.Date, default=lambda: datetime.utcnow().date())

class Measurement(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # blood_pressure, blood_sugar, temperature, weight
    systolic = db.Column(db.Integer)  # For blood pressure
    diastolic = db.Column(db.Integer)  # For blood pressure
    value = db.Column(db.Float, nullable=False)  # Main measurement value
    unit = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.Text)
    measured_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Helper functions
def get_current_time():
    """Get current time in Turkey timezone"""
    turkey_tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(turkey_tz)

def rate_limit(f):
    """Simple rate limiting decorator"""
    last_called = {}
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = current_user.id if current_user.is_authenticated else request.remote_addr
        now = datetime.utcnow()

        if user_id in last_called:
            time_diff = (now - last_called[user_id]).total_seconds()
            if time_diff < 1:  # 1 second minimum between requests
                return jsonify({'error': 'Too many requests'}), 429

        last_called[user_id] = now
        return f(*args, **kwargs)
    return decorated_function

def validate_medication_data(data):
    """Validate medication input data"""
    if not data.get('name') or len(data['name'].strip()) < 2:
        raise ValueError('İlaç adı en az 2 karakter olmalıdır')

    if not data.get('dosage') or not data['dosage'].strip():
        raise ValueError('Doz belirtmeniz gerekmektedir')

    if not data.get('time'):
        raise ValueError('Saat belirtmeniz gerekmektedir')

    # Validate time format
    try:
        time_val = datetime.strptime(data['time'], '%H:%M').time()
    except ValueError:
        raise ValueError('Geçersiz saat formatı (HH:MM kullanın)')

    return {
        'name': data['name'].strip(),
        'dosage': data['dosage'].strip(),
        'time': time_val,
        'notes': data.get('notes', '').strip()
    }

def validate_measurement_data(data):
    """Validate measurement input data"""
    if data.get('type') == 'blood_pressure':
        if not data.get('systolic') or not data.get('diastolic'):
            raise ValueError('Tansiyon için büyük ve küçük değerler gereklidir')
        return {
            'type': 'blood_pressure',
            'systolic': int(data['systolic']),
            'diastolic': int(data['diastolic']),
            'value': float(data['systolic']),  # Main value as systolic
            'unit': 'mmHg',
            'notes': data.get('notes', '').strip()
        }
    else:
        if not data.get('value'):
            raise ValueError('Ölçüm değeri gereklidir')
        return {
            'type': data['type'],
            'value': float(data['value']),
            'unit': data.get('unit', ''),
            'notes': data.get('notes', '').strip()
        }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
@csrf.exempt
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'error': 'Geçerli bir email adresi girin'}), 400

    # Simple email-based auth (production'da gerçek OAuth kullanın)
    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(email=email)
        user.set_password('temp_password')  # Real auth yapılacak
        db.session.add(user)
        db.session.commit()

        flash('Yeni kullanıcı oluşturuldu. şifre belirleyin.', 'info')

    login_user(user, remember=True)
    session.permanent = True

    return jsonify({'success': True, 'message': 'Giriş başarılı'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/user/status')
def user_status():
    """Check user login status"""
    if current_user.is_authenticated:
        return jsonify({
            'email': current_user.email,
            'id': current_user.id,
            'logged_in': True
        })
    return jsonify({'logged_in': False}), 401

@app.route('/api/ping')
def ping():
    """Keep session alive ping endpoint"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/csrf-token')
def get_csrf_token():
    return jsonify({'csrf_token': generate_csrf()})

@app.route('/api/medications', methods=['GET'])
@login_required
@rate_limit
def get_medications():
    medications = Medication.query.filter_by(user_id=current_user.id, is_active=True).all()

    result = []
    for med in medications:
        result.append({
            'id': med.id,
            'name': med.name,
            'dosage': med.dosage,
            'time': med.time.strftime('%H:%M'),
            'notes': med.notes,
            'last_taken': med.last_taken.isoformat() if med.last_taken else None
        })

    return jsonify(result)

@app.route('/api/medications', methods=['POST'])
@login_required
@rate_limit
def create_medication():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Geçersiz veri'}), 400

        validated_data = validate_medication_data(data)

        medication = Medication(
            user_id=current_user.id,
            **validated_data
        )

        db.session.add(medication)
        db.session.commit()

        logger.info(f'New medication created: {medication.id} for user {current_user.id}')

        return jsonify({
            'id': medication.id,
            'message': 'İlaç başarıyla eklendi'
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Medication creation error: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Bir hata oluştu'}), 500

@app.route('/api/take-medication', methods=['POST'])
@login_required
@rate_limit
def take_medication():
    try:
        data = request.get_json()
        medication_id = data.get('medication_id')

        if not medication_id:
            return jsonify({'error': 'İlaç ID gerekli'}), 400

        medication = Medication.query.filter_by(
            id=medication_id,
            user_id=current_user.id,
            is_active=True
        ).first()

        if not medication:
            return jsonify({'error': 'İlaç bulunamadı'}), 404

        now = get_current_time()
        medication.last_taken = now

        taken_record = TakenMedication(
            user_id=current_user.id,
            medication_id=medication_id,
            taken_at=now,
            date=now.date()
        )

        db.session.add(taken_record)
        db.session.commit()

        return jsonify({'message': 'İlaç alımınız kaydedildi'})

    except Exception as e:
        logger.error(f'Take medication error: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Bir hata oluştu'}), 500

@app.route('/api/measurements', methods=['GET'])
@login_required
def get_measurements():
    limit = request.args.get('limit', 20, type=int)
    measurements = Measurement.query.filter_by(user_id=current_user.id)\
                                   .order_by(Measurement.measured_at.desc())\
                                   .limit(limit).all()

    result = []
    for measurement in measurements:
        item = {
            'id': measurement.id,
            'type': measurement.type,
            'value': measurement.value,
            'unit': measurement.unit,
            'notes': measurement.notes,
            'measured_at': measurement.measured_at.isoformat()
        }

        if measurement.type == 'blood_pressure':
            item.update({
                'systolic': measurement.systolic,
                'diastolic': measurement.diastolic
            })

        result.append(item)

    return jsonify(result)

@app.route('/api/measurements', methods=['POST'])
@login_required
@rate_limit
def create_measurement():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Geçersiz veri'}), 400

        validated_data = validate_measurement_data(data)

        measurement = Measurement(
            user_id=current_user.id,
            measured_at=get_current_time(),
            **validated_data
        )

        db.session.add(measurement)
        db.session.commit()

        return jsonify({'message': 'Ölçüm kaydedildi', 'id': measurement.id})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Measurement creation error: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Bir hata oluştu'}), 500

@app.route('/api/stats')
@login_required
def get_stats():
    """Get user statistics"""
    try:
        today = get_current_time().date()

        # Today's medications
        medications = Medication.query.filter_by(user_id=current_user.id, is_active=True).all()
        taken_today = {tm.medication_id for tm in TakenMedication.query.filter_by(
            user_id=current_user.id, date=today).all()}

        today_medications = []
        for med in medications:
            taken = med.id in taken_today if med.last_taken and med.last_taken.date() == today else False
            today_medications.append({
                'id': med.id,
                'name': med.name,
                'dosage': med.dosage,
                'time': med.time.strftime('%H:%M'),
                'taken': taken
            })

        # Recent measurements (BP and sugar)
        bp_measurements = Measurement.query.filter_by(
            user_id=current_user.id, type='blood_pressure'
        ).order_by(Measurement.measured_at.desc()).limit(7).all()

        sugar_measurements = Measurement.query.filter_by(
            user_id=current_user.id, type='blood_sugar'
        ).order_by(Measurement.measured_at.desc()).limit(7).all()

        return jsonify({
            'today_medications': today_medications,
            'recent_bp': [{'date': m.measured_at.strftime('%Y-%m-%d'), 'systolic': m.systolic, 'diastolic': m.diastolic}
                         for m in bp_measurements],
            'recent_sugar': [{'date': m.measured_at.strftime('%Y-%m-%d'), 'value': m.value}
                           for m in sugar_measurements]
        })

    except Exception as e:
        logger.error(f'Stats error: {str(e)}')
        return jsonify({'error': 'İstatistikler yüklenemedi'}), 500

@app.route('/api/export')
@login_required
def export_data():
    """Export all user data as JSON"""
    try:
        medications = Medication.query.filter_by(user_id=current_user.id).all()
        measurements = Measurement.query.filter_by(user_id=current_user.id).all()
        taken = TakenMedication.query.filter_by(user_id=current_user.id).all()

        # Manual serialization
        medications_data = []
        for m in medications:
            med_data = {
                'id': m.id,
                'name': m.name,
                'dosage': m.dosage,
                'time': m.time.strftime('%H:%M') if m.time else None,
                'period': m.period,
                'notes': m.notes,
                'is_active': m.is_active,
                'created_at': m.created_at.isoformat() if m.created_at else None,
                'last_taken': m.last_taken.isoformat() if m.last_taken else None
            }
            medications_data.append(med_data)

        measurements_data = []
        for m in measurements:
            meas_data = {
                'id': m.id,
                'type': m.type,
                'systolic': m.systolic,
                'diastolic': m.diastolic,
                'value': m.value,
                'unit': m.unit,
                'notes': m.notes,
                'measured_at': m.measured_at.isoformat() if m.measured_at else None
            }
            measurements_data.append(meas_data)

        taken_data = []
        for t in taken:
            taken_item = {
                'id': t.id,
                'medication_id': t.medication_id,
                'taken_at': t.taken_at.isoformat() if t.taken_at else None,
                'date': t.date.isoformat() if t.date else None
            }
            taken_data.append(taken_item)

        data = {
            'export_date': get_current_time().isoformat(),
            'user_email': current_user.email,
            'medications': medications_data,
            'measurements': measurements_data,
            'taken_history': taken_data
        }

        return jsonify(data)

    except Exception as e:
        logger.error(f'Export error: {str(e)}')
        return jsonify({'error': 'Veri dışa aktarılamadı'}), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)
