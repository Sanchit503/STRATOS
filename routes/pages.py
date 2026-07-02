from flask import Blueprint, render_template

pages_bp = Blueprint('pages_bp', __name__)

@pages_bp.route('/')
def index():
    return render_template('index.html')

@pages_bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html', active_page='dashboard')

@pages_bp.route('/bases')
def bases_page():
    return render_template('bases.html', active_page='bases')

@pages_bp.route('/missiles')
def missiles_page():
    return render_template('missiles.html', active_page='missiles')

@pages_bp.route('/vehicles')
def vehicles_page():
    return render_template('vehicles.html', active_page='vehicles')

@pages_bp.route('/enemy')
def enemy_page():
    return render_template('enemy.html', active_page='enemy')

@pages_bp.route('/mission')
def mission_page():
    return render_template('mission.html', active_page='mission')


@pages_bp.route('/transactions')
def transactions_page():
    return render_template('transactions.html', active_page='transactions')

@pages_bp.route('/operations')
def operations_page():
    return render_template('operations.html', active_page='operations')
