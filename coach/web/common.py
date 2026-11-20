from flask import current_app, jsonify


def services():
    return current_app.extensions["coach"]


def error(message, status=400):
    return jsonify({"error": message}), status
