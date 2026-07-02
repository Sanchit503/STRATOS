from flask import Blueprint, jsonify, request
from utils import haversine

map_bp = Blueprint('map_bp', __name__)

@map_bp.route('/api/distance')
def calc_distance():
    """Calculate distance between two lat/lng points."""
    try:
        lat1 = float(request.args['lat1'])
        lng1 = float(request.args['lng1'])
        lat2 = float(request.args['lat2'])
        lng2 = float(request.args['lng2'])
    except (KeyError, ValueError):
        return jsonify({'error': 'Provide lat1, lng1, lat2, lng2'}), 400

    dist = haversine(lat1, lng1, lat2, lng2)
    return jsonify({'distance_km': dist, 'from': [lat1, lng1], 'to': [lat2, lng2]})
