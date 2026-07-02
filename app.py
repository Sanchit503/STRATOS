"""
STRATOS Strategic Map — Flask Backend
Serves API endpoints for the interactive military map.
"""

from flask import Flask
from routes.pages import pages_bp
from routes.dashboard import dashboard_bp
from routes.bases import bases_bp
from routes.missiles import missiles_bp
from routes.vehicles import vehicles_bp
from routes.enemy import enemy_bp
from routes.map import map_bp
from routes.missions import missions_bp
from routes.transactions import transactions_bp
from routes.operations import operations_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(pages_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(bases_bp)
app.register_blueprint(missiles_bp)
app.register_blueprint(vehicles_bp)
app.register_blueprint(enemy_bp)
app.register_blueprint(map_bp)
app.register_blueprint(missions_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(operations_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
