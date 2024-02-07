from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.document import DocumentReference

import jwt, git, requests
from functools import wraps
from datetime import timedelta
from config import JWT_SECRET_KEY

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt_code = JWTManager(app)

cred = credentials.Certificate('/home/gdscmemberweb/member-server/Service/server.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def serialize_doc(doc):
    if isinstance(doc, DocumentReference):
        return doc.id
    elif isinstance(doc, dict):
        for key, value in doc.items():
            doc[key] = serialize_doc(value)
        return doc
    elif isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    else:
        return doc

def check_role(user_data):
    user_email = user_data['sub']['email']
    user_docs = db.collection('users').where('email', '==', user_email).limit(1).get()

    if len(user_docs) == 0:
        return "none"

    user_doc = user_docs[0]
    user_role = user_doc.to_dict().get('role', 'none')

    return user_role

def decode_id_token(id_token):
    url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Unable to validate token", "status_code": response.status_code}

def jwt_required_custom(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        jwt_token = request.headers.get('Authorization', None)
        if not jwt_token:
            return jsonify(message="缺少授權 token"), 401
        try:
            user_data = jwt.decode(jwt_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            return fn(user_data=user_data, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(message="Token 已過期"), 401
        except jwt.InvalidTokenError:
            return jsonify(message="無效的 token"), 401
    return wrapper

@app.route('/')
def main_root():
    return "Service is ready!!!"

@app.route('/git_update', methods=['POST'])
def git_update():
    repo = git.Repo('./member-server')
    origin = repo.remotes.origin
    repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
    origin.pull()
    return "Pulled", 200

@app.route('/google_login', methods=['POST'])
def custom_google_login():
    id_token = request.json.get('idToken')
    try:
        decoded_token = decode_id_token(id_token)
        if decoded_token.get('email_verified') == 'true':
            user_email = decoded_token.get('email')
            user_name = decoded_token.get('name')
            user_picture = decoded_token.get('picture')
            user_info = {"email": user_email, "name": user_name, "picture": user_picture}
            access_token = create_access_token(identity=user_info)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify(message="Google login failed"), 401
    except Exception as e:
        print("Error during Google login:", e)
        return jsonify(message="Google login failed"), 401

@app.route('/create', methods=['POST'])
@jwt_required_custom
def create_document(user_data):
    collection_name = request.json['collection']
    user_role = check_role(user_data)

    if collection_name in ['forms', 'notes', 'projects']:
        if user_role != "admin":
            return jsonify({"message": "權限不足"}), 400

    data = request.json['data']

    if collection_name == "users":
        if user_role != "admin":
            data.pop('paid', None)
            data.pop('payment', None)
            data['role'] = "insider"
        data['email'] = user_data["sub"]["email"]
        data['picture'] = user_data["sub"]["picture"]

    # Check Index
    unique_index_field = 'name' if collection_name in ['forms', 'notes', 'projects'] else 'email' if collection_name == 'users' else None

    if unique_index_field and unique_index_field in data:
        existing_doc = db.collection(collection_name).where(unique_index_field, '==', data[unique_index_field]).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": f"{unique_index_field} already exists"}), 400

    ref = db.collection(collection_name)
    ref.add(data)

    return jsonify({"message": "Document added successfully"}), 201

@app.route('/assign_member_to_project', methods=['POST'])
@jwt_required_custom
def assign_member_to_project(user_data):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    user_email = request.json['user_email']
    project_name = request.json['project_name']

    user_ref = db.collection('users').where('email', '==', user_email).limit(1).stream()
    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()

    user_doc = next(user_ref, None)
    project_doc = next(project_ref, None)

    if not user_doc or not project_doc:
        return jsonify({"message": "User or Project not found"}), 404

    project_doc.reference.update({
        'team_members': firestore.ArrayUnion([user_doc.reference])
    })
    user_doc.reference.update({
        'projects_involved': firestore.ArrayUnion([project_doc.reference])
    })

    return jsonify({"message": "Member assigned to project successfully"}), 200

@app.route('/assign_pm', methods=['POST'])
@jwt_required_custom
def assign_project_manager(user_data):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    user_email = request.json['user_email']
    project_name = request.json['project_name']

    user_ref = db.collection('users').where('email', '==', user_email).limit(1).stream()
    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()

    user_doc = next(user_ref, None)
    project_doc = next(project_ref, None)

    if not user_doc or not project_doc:
        return jsonify({"message": "User or Project not found"}), 404

    project_doc.reference.update({
        'project_manager': user_doc.reference
    })
    user_doc.reference.update({
        'managed_projects': firestore.ArrayUnion([project_doc.reference])
    })

    return jsonify({"message": "Project manager assigned successfully"}), 200

@app.route('/read', methods=['GET'])
@jwt_required_custom
def read_documents(user_data):
    collection_name = request.args.get('collection')
    documents = db.collection(collection_name).stream()
    user_role = check_role(user_data)

    if collection_name == 'users':
        if user_role != "admin":
            return jsonify({"message": "權限不足"}), 400

    result = []
    for doc in documents:
        doc_data = serialize_doc(doc.to_dict())

        if collection_name == 'users':
            if 'managed_projects' in doc_data:
                managed_project_names = []
                for project_ref in doc_data['managed_projects']:
                    project_data = db.collection('projects').document(project_ref).get()
                    if project_data.exists:
                        managed_project_names.append(project_data.to_dict().get('name', 'Unknown'))
                doc_data['managed_projects'] = managed_project_names

            if 'projects_involved' in doc_data:
                involved_project_names = []
                for project_ref in doc_data['projects_involved']:
                    project_data = db.collection('projects').document(project_ref).get()
                    if project_data.exists:
                        involved_project_names.append(project_data.to_dict().get('name', 'Unknown'))
                doc_data['projects_involved'] = involved_project_names

        elif collection_name == 'projects':
            if 'project_manager' in doc_data:
                pm_ref = doc_data['project_manager']
                if pm_ref:
                    pm_data = db.collection('users').document(pm_ref).get()
                    if pm_data.exists:
                        doc_data['project_manager'] = pm_data.to_dict().get('email', 'Unknown')

            if 'team_members' in doc_data:
                team_member_emails = []
                for member_ref in doc_data['team_members']:
                    member_data = db.collection('users').document(member_ref).get()
                    if member_data.exists:
                        team_member_emails.append(member_data.to_dict().get('email', 'Unknown'))
                doc_data['team_members'] = team_member_emails

        result.append({doc.id: doc_data})

    return jsonify(result), 200

@app.route('/read_project/<name>', methods=['GET'])
@jwt_required_custom
def read_project(user_data, name):
    document = db.collection('projects').where('name', '==', name).stream()
    for doc in document:
        project_data = serialize_doc(doc.to_dict())

        if 'project_manager' in project_data:
            pm_ref = project_data['project_manager']
            if pm_ref:
                pm_data = db.collection('users').document(pm_ref).get()
                if pm_data.exists:
                    project_data['project_manager'] = pm_data.to_dict().get('email', 'Unknown')

        if 'team_members' in project_data:
            team_member_emails = []
            for member_ref in project_data['team_members']:
                member_data = db.collection('users').document(member_ref).get()
                if member_data.exists:
                    team_member_emails.append(member_data.to_dict().get('email', 'Unknown'))
            project_data['team_members'] = team_member_emails

        return jsonify(project_data), 200
    return jsonify({"message": "Project not found"}), 404

@app.route('/read_member/<email>', methods=['GET'])
@jwt_required_custom
def read_member(user_data, email):
    user_role = check_role(user_data)
    if user_data["sub"]["email"] != email and user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    document = db.collection('users').where('email', '==', email).stream()

    for doc in document:
        user_data = serialize_doc(doc.to_dict())

        if 'managed_projects' in user_data:
            managed_project_names = []
            for project_ref in user_data['managed_projects']:
                project_data = db.collection('projects').document(project_ref).get()
                if project_data.exists:
                    managed_project_names.append(project_data.to_dict().get('name', 'Unknown'))
            user_data['managed_projects'] = managed_project_names

        if 'projects_involved' in user_data:
            involved_project_names = []
            for project_ref in user_data['projects_involved']:
                project_data = db.collection('projects').document(project_ref).get()
                if project_data.exists:
                    involved_project_names.append(project_data.to_dict().get('name', 'Unknown'))
            user_data['projects_involved'] = involved_project_names

        return jsonify(user_data), 200
    return jsonify({"message": "Member not found"}), 404

@app.route('/update_project/<project_name>', methods=['PUT'])
@jwt_required_custom
def update_project(user_data, project_name):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    data = request.json
    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()

    project_doc = next(project_ref, None)
    if not project_doc:
        return jsonify({"message": "Project not found"}), 404

    # Check Index
    if 'name' in data and data['name'] != project_name:
        existing_doc = db.collection('projects').where('name', '==', data['name']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Project name already exists"}), 400

    project_doc.reference.update(data)
    return jsonify({"message": "Project updated successfully"}), 200

@app.route('/update_member/<email>', methods=['PUT'])
@jwt_required_custom
def update_member(user_data, email):
    user_role = check_role(user_data)
    if user_data["sub"]["email"] != email and user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    data = request.json

    if user_role != "admin":
        data.pop('paid', None)
        data.pop('payment', None)
        data.pop('role', None)

    user_ref = db.collection('users').where('email', '==', email).limit(1).stream()

    user_doc = next(user_ref, None)
    if not user_doc:
        return jsonify({"message": "Member not found"}), 404

    # Check Index
    if 'email' in data and data['email'] != email:
        existing_doc = db.collection('users').where('email', '==', data['email']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Email already exists"}), 400

    user_doc.reference.update(data)
    return jsonify({"message": "Member updated successfully"}), 200

@app.route('/update_note/<note_name>', methods=['PUT'])
@jwt_required_custom
def update_note(user_data, note_name):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    data = request.json
    note_ref = db.collection('notes').where('name', '==', note_name).limit(1).stream()

    note_doc = next(note_ref, None)
    if not note_doc:
        return jsonify({"message": "Note not found"}), 404

    # Check Index
    if 'name' in data and data['name'] != note_name:
        existing_doc = db.collection('notes').where('name', '==', data['name']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Note name already exists"}), 400

    note_doc.reference.update(data)
    return jsonify({"message": "Note updated successfully"}), 200

@app.route('/update_form/<form_name>', methods=['PUT'])
@jwt_required_custom
def update_form(user_data, form_name):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    data = request.json
    form_ref = db.collection('forms').where('name', '==', form_name).limit(1).stream()

    form_doc = next(form_ref, None)
    if not form_doc:
        return jsonify({"message": "Form not found"}), 404

    # Check Index
    if 'name' in data and data['name'] != form_name:
        existing_doc = db.collection('forms').where('name', '==', data['name']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Form name already exists"}), 400

    form_doc.reference.update(data)
    return jsonify({"message": "Form updated successfully"}), 200

@app.route('/delete_form/<form_name>', methods=['DELETE'])
@jwt_required_custom
def delete_form(user_data, form_name):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    form_ref = db.collection('forms').where('name', '==', form_name).limit(1).stream()
    form_doc = next(form_ref, None)
    if form_doc:
        form_doc.reference.delete()
        return jsonify({"message": "Form deleted successfully"}), 200
    else:
        return jsonify({"message": "Form not found"}), 404

@app.route('/delete_note/<note_name>', methods=['DELETE'])
@jwt_required_custom
def delete_note(user_data, note_name):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    note_ref = db.collection('notes').where('name', '==', note_name).limit(1).stream()
    note_doc = next(note_ref, None)
    if note_doc:
        note_doc.reference.delete()
        return jsonify({"message": "Note deleted successfully"}), 200
    else:
        return jsonify({"message": "Note not found"}), 404

@app.route('/delete_project/<project_name>', methods=['DELETE'])
@jwt_required_custom
def delete_project(user_data, project_name):
    user_role = check_role(user_data)
    if user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()
    project_doc = next(project_ref, None)
    if project_doc:
        project_doc.reference.delete()
        return jsonify({"message": "Project deleted successfully"}), 200
    else:
        return jsonify({"message": "Project not found"}), 404

@app.route('/delete_member/<member_email>', methods=['DELETE'])
@jwt_required_custom
def delete_member(user_data, member_email):
    user_role = check_role(user_data)
    if user_data["sub"]["email"] != member_email and user_role != "admin":
        return jsonify({"message": "權限不足"}), 400

    member_ref = db.collection('users').where('email', '==', member_email).limit(1).stream()
    member_doc = next(member_ref, None)
    if member_doc:
        member_doc.reference.delete()
        return jsonify({"message": "Member deleted successfully"}), 200
    else:
        return jsonify({"message": "Member not found"}), 404

if __name__ == '__main__':
    app.run(threaded=True)
