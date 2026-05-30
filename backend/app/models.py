from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        import bcrypt
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        import bcrypt
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

class ETFInfo(db.Model):
    __tablename__ = 'etf_info'
    
    sec_code = db.Column(db.String(20), primary_key=True)
    sec_name = db.Column(db.String(100))
    full_name = db.Column(db.String(200))
    list_date = db.Column(db.Date)
    fund_manager = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ETFDailyShare(db.Model):
    __tablename__ = 'etf_daily_share'
    
    id = db.Column(db.Integer, primary_key=True)
    sec_code = db.Column(db.String(20), db.ForeignKey('etf_info.sec_code'), nullable=False)
    stat_date = db.Column(db.Date, nullable=False)
    tot_vol = db.Column(db.Float)
    num = db.Column(db.Integer)
    close_price = db.Column(db.Float)
    market = db.Column(db.String(10), default='SH')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('sec_code', 'stat_date', name='uqc_sec_code_stat_date'),
        db.Index('idx_etf_daily_share_sec_code', 'sec_code'),
        db.Index('idx_etf_daily_share_stat_date', 'stat_date'),
    )

class ETFTopHolder(db.Model):
    __tablename__ = 'etf_top_holders'
    
    id = db.Column(db.Integer, primary_key=True)
    sec_code = db.Column(db.String(20), db.ForeignKey('etf_info.sec_code'), nullable=False)
    holder_name = db.Column(db.String(200))
    hold_volume = db.Column(db.Float)
    hold_ratio = db.Column(db.Float)
    stat_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
