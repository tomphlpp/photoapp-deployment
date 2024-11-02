from dotenv import load_dotenv
from flask import Flask, request, send_from_directory, render_template
from flask_restful import Api
import flask_jwt_extended
from flask_cors import CORS
import os
from models import db, User, ApiNavigator
from views import initialize_routes
import decorators

load_dotenv()

app = Flask(__name__)

# Define static folder
app.static_folder = os.path.join(app.root_path, "static")
react_dist_path = os.path.join(app.root_path, "react-client", "dist")
cors = CORS(
    app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True
)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET")
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

jwt = flask_jwt_extended.JWTManager(app)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    user_id = jwt_data["sub"]
    return User.query.filter_by(id=user_id).one_or_none()

db.init_app(app)
api = Api(app)

# Initialize routes for all API endpoints
initialize_routes(api)

# Serve main React app and static files
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
@decorators.jwt_or_login
def serve_react(path):
    dist_path = os.path.join(app.root_path, "react-client", "dist")
    if path and os.path.exists(os.path.join(dist_path, path)):
        # Serve the static file if it exists
        return send_from_directory(dist_path, path)
    else:
        # Serve the main React app for any undefined paths
        return send_from_directory(dist_path, "index.html")


@app.route("/api")
@app.route("/api/")
@decorators.jwt_or_login
def api_docs():
    access_token = request.cookies.get("access_token_cookie")
    csrf = request.cookies.get("csrf_access_token")
    navigator = ApiNavigator(flask_jwt_extended.current_user)
    return render_template(
        "api/api-docs.html",
        user=flask_jwt_extended.current_user,
        endpoints=navigator.get_endpoints(),
        access_token=access_token,
        csrf=csrf,
        url_root=request.url_root.rstrip("/"),  # trim trailing slash
    )

# Enables Flask app to run using "python3 app.py"
if __name__ == "__main__":
    app.run()
