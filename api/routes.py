import sqlite3
from flask_restx import Resource, fields
from flask import current_app, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from . import api, api_bp
from models import Db
# from app import db

# Define a namespace
auth_ns = api.namespace('auth', description='Manage authentication.')
encounters_ns = api.namespace('encounters', description='Race medical Tracking Encounters')
persons_ns = api.namespace('persons', description='Registered Race Participants')

# Define API model for Auth
auth_model = auth_ns.model('Auth', {
    'username': fields.String(required=True, description='Username for authentication'),
    'password': fields.String(required=True, description='Password for authentication')
})

# Custom field to handle empty strings and convert to None
class NullableInteger(fields.Integer):
    def format(self, value):
        try:
            if value == "":
                return None  # or any other default value you want
            if isinstance(value, str):
                return value
            return super().format(value)
        except ValueError:
            raise fields.MarshallingError('Unable to marshal field "{}" value "{}"'.format(self.name, value))


# Define API model for Encounter
encounter_model = encounters_ns.model('Encounter', {
    'aid_station': fields.String(required=True, description='Aid Station Name'),
    'bib': fields.String(description='Bib Number'),
    'first_name': fields.String(description='First Name'),
    'last_name': fields.String(description='Last Name'),
    'age': NullableInteger(description='Age'),
    'sex': fields.String(description='Sex'),
    'participant': fields.Boolean(description='Participant Status'),
    'active_duty': fields.Boolean(description='Active Duty Status'),
    'time_in': fields.String(description='Time In'),
    'time_out': fields.String(description='Time Out'),
    'presentation': fields.String(description='Presentation'),
    'vitals': fields.String(description='Vitals'),
    'iv': fields.String(description='IV Status'),
    'iv_fluid_count': NullableInteger(description='IV Fluid Count'),
    'oral_fluid': fields.Boolean(description='Oral Fluid Status'),
    'food': fields.Boolean(description='Food provided'),
    'na': fields.String(description='Lab value: BMP Sodium (Na+)'),
    'kplus': fields.String(description='Lab value: BMP Potassium (K+)'),
    'cl': fields.String(description='Lab value: BMP Chlorine (Cl-)'),
    'tco': fields.String(description='Lab value: BMP Bicarbonate (tCO2)'),
    'bun': fields.String(description='Lab value: BMP Blood Urea Nitrogen (BUN)'),
    'cr': fields.String(description='Lab value: BMP Creatinine (Cr)'),
    'glu': fields.String(description='Lab value: BMP Blood Glucose (Glu)'),
    'treatments': fields.String(description='Treatments'),
    'disposition': fields.String(description='Disposition'),
    'hospital': fields.String(description='Hospital'),
    'notes': fields.String(description='Notes'),
    'delete_flag': fields.Boolean(description='Delete Flag'),
    'delete_reason': fields.String(description='Delete Reason')
})

# Define API model for Person
person_model = persons_ns.model('Person', {
    'bib': fields.String(required=True, description='Bib Number'),
    'first_name': fields.String(required=True, description='First Name'),
    'last_name': fields.String(required=True, description='Last Name'),
    'age': NullableInteger(required=True, description='Age'),
    'sex': fields.String(required=True, description='Sex'),
    'participant': fields.Boolean(required=True, description='Participant Status'),
    'active_duty': fields.Boolean(required=True, description='Active Duty Status')
})


# *====================================================================*
#         INITIALIZE DB & DB access
# *====================================================================*
db = Db()

def initialize_db():
    db.add_db(current_app.config.get('DATABASE_PATH'))


# Connect to database
def get_db():
    initialize_db()
    conn = db.db_connect()
    conn.row_factory = sqlite3.Row
    return conn

# JWT Token Generation Endpoint
@auth_ns.route('/tokens', methods=['POST'])
class Auth(Resource):
    @api.expect(auth_model)
    def post(self):
        """Get authentication token"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        from pprint import pprint
        print(pprint(current_app.config))

        if username in current_app.config['USER_ACCOUNTS'].keys():
            if password == current_app.config['USER_ACCOUNTS'][username]['password']:
                access_token = create_access_token(identity=username)
                return {'data': {'Access Token': access_token}}, 200
        
        return {'data': {"msg": "Bad username or password"}}, 401


# API Endpoints for Encounters
@encounters_ns.route('/')
class EncounterList(Resource):
    @jwt_required()
    @encounters_ns.marshal_list_with(encounter_model)
    def get(self):
        """Fetch all encounters"""
        with get_db() as conn:
            encounters = conn.execute('SELECT * FROM encounters WHERE delete_flag != 1').fetchall()
        return [dict(row) for row in encounters], 200

    @jwt_required()
    @encounters_ns.expect(encounter_model)
    def post(self):
        """Create a new encounter"""
        data = request.json
        with get_db() as conn:
            conn.execute('''INSERT INTO encounters (aid_station, bib, first_name, last_name, age, sex, participant, active_duty, time_in, time_out, presentation, vitals, iv, iv_fluid_count, oral_fluid, treatments, disposition, hospital, notes, delete_flag, delete_reason)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (data['aid_station'], data['bib'], data['first_name'], data['last_name'], data['age'], data['sex'], data['participant'], data['active_duty'], data['time_in'], data['time_out'], data['presentation'], data['vitals'], data['iv'], data['iv_fluid_count'], data['oral_fluid'], data['treatments'], data['disposition'], data['hospital'], data['notes'], data['delete_flag'], data['delete_reason']))
            conn.commit()
        return {'message': 'Encounter created'}, 201

# API Endpoints for Persons
@persons_ns.route('/')
class PersonList(Resource):
    @jwt_required()
    @persons_ns.marshal_list_with(person_model)
    def get(self):
        """Fetch all persons"""
        with get_db() as conn:
            persons = conn.execute('SELECT * FROM persons').fetchall()
        return [dict(row) for row in persons], 200

    @jwt_required()
    @persons_ns.expect(person_model)
    def post(self):
        """Create a new person"""
        data = request.json
        with get_db() as conn:
            conn.execute('''INSERT INTO persons (bib, first_name, last_name, age, sex, participant, active_duty)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (data['bib'], data['first_name'], data['last_name'], data['age'], data['sex'], data['participant'], data['active_duty']))
            conn.commit()
        return {'message': 'Person created'}, 201

# Protect API and Add Blueprint
api.add_namespace(auth_ns, path='/auth')
api.add_namespace(encounters_ns, path='/encounters')
api.add_namespace(persons_ns, path='/persons')