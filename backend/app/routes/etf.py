from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app import db
from app.models import ETFInfo, ETFDailyShare

bp = Blueprint('etf', __name__)

@bp.route('/list', methods=['GET'])
@jwt_required()
def get_etf_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = ETFInfo.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [{'sec_code': e.sec_code, 'sec_name': e.sec_name, 'full_name': e.full_name} for e in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    })

@bp.route('/<sec_code>', methods=['GET'])
@jwt_required()
def get_etf(sec_code):
    etf = ETFInfo.query.get(sec_code)
    if not etf:
        return jsonify({'error': 'ETF not found'}), 404
    return jsonify({
        'sec_code': etf.sec_code,
        'sec_name': etf.sec_name,
        'full_name': etf.full_name,
        'list_date': str(etf.list_date) if etf.list_date else None,
        'fund_manager': etf.fund_manager
    })

@bp.route('/<sec_code>/trend', methods=['GET'])
@jwt_required()
def get_etf_trend(sec_code):
    days = request.args.get('days', 30, type=int)
    
    from datetime import datetime, timedelta
    start_date = datetime.now().date() - timedelta(days=days)
    
    data = ETFDailyShare.query.filter(
        ETFDailyShare.sec_code == sec_code,
        ETFDailyShare.stat_date >= start_date
    ).order_by(ETFDailyShare.stat_date).all()
    
    return jsonify([{
        'date': str(d.stat_date),
        'tot_vol': d.tot_vol,
        'close_price': d.close_price
    } for d in data])

@bp.route('/ranking', methods=['GET'])
@jwt_required()
def get_ranking():
    sort_by = request.args.get('sort_by', 'tot_vol')  # tot_vol, change, change_pct
    limit = request.args.get('limit', 10, type=int)
    
    from datetime import datetime, timedelta
    
    if sort_by == 'change':
        # 今日份额变化排名
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        today_data = db.session.query(
            ETFDailyShare.sec_code,
            ETFDailyShare.tot_vol
        ).filter(ETFDailyShare.stat_date == today).subquery()
        
        yesterday_data = db.session.query(
            ETFDailyShare.sec_code,
            ETFDailyShare.tot_vol
        ).filter(ETFDailyShare.stat_date == yesterday).subquery()
        
        query = db.session.query(
            today_data.c.sec_code,
            (today_data.c.tot_vol - func.coalesce(yesterday_data.c.tot_vol, 0)).label('change')
        ).outerjoin(yesterday_data, today_data.c.sec_code == yesterday_data.c.sec_code)
        
    result = db.session.query(
        ETFInfo.sec_code,
        ETFInfo.sec_name,
        ETFDailyShare.tot_vol,
        ETFDailyShare.stat_date
    ).join(ETFDailyShare, ETFInfo.sec_code == ETFDailyShare.sec_code
    ).order_by(ETFDailyShare.tot_vol.desc()
    ).limit(limit).all()
    
    return jsonify([{
        'sec_code': r.sec_code,
        'sec_name': r.sec_name,
        'tot_vol': r.tot_vol,
        'stat_date': str(r.stat_date)
    } for r in result])

@bp.route('/compare', methods=['GET'])
@jwt_required()
def compare_etf():
    codes = request.args.get('codes', '').split(',')
    days = request.args.get('days', 30, type=int)
    
    from datetime import datetime, timedelta
    start_date = datetime.now().date() - timedelta(days=days)
    
    data = ETFDailyShare.query.filter(
        ETFDailyShare.sec_code.in_(codes),
        ETFDailyShare.stat_date >= start_date
    ).order_by(ETFDailyShare.stat_date).all()
    
    result = {}
    for d in data:
        if d.sec_code not in result:
            result[d.sec_code] = []
        result[d.sec_code].append({
            'date': str(d.stat_date),
            'tot_vol': d.tot_vol,
            'close_price': d.close_price
        })
    
    return jsonify(result)
