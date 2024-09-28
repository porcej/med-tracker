from flask import Blueprint
from flask_restx import Api

api_bp = Blueprint('api_bp', __name__, url_prefix='/api/v1')
authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Enter: **'Bearer &lt;JWT&gt;'**, where JWT is the access token",
    }
}

api = Api(api_bp, version='1.0',
            title='Medical Tracking Public API',
            description='API To Interact with the Medical Tracking Database',
            authorizations=authorizations,
            security='Bearer Auth')

# Import the routes to register the endpoints
from . import routes