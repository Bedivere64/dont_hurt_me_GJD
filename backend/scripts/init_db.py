import sys
sys.path.insert(0, '/opt/etf-dashboard/backend')

from app import create_app, db
from app.models import User, ETFInfo, ETFDailyShare

app = create_app()

with app.app_context():
    db.create_all()
    print('数据库表创建完成')
    
    # 创建管理员账号
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@bedivere.space')
        admin.set_password('Admin2026!')
        db.session.add(admin)
        db.session.commit()
        print('管理员账号创建完成: admin / Admin2026!')
    else:
        print('管理员账号已存在')
