import logging
from flask import render_template, request, jsonify
from .extensions import db

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Register global error handlers for the application.
    """
    
    @app.errorhandler(400)
    def handle_400(e):
        if request.path.startswith('/ml/'):
            return jsonify({"error": "Bad Request", "message": str(e)}), 400
        return render_template('400.html', error=e), 400

    @app.errorhandler(403)
    def handle_403(e):
        if request.path.startswith('/ml/'):
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/ml/'):
            return jsonify({"error": "Not Found", "message": "Resource not found"}), 404
        return render_template('404.html'), 404

    @app.errorhandler(429)
    def handle_429(e):
        if request.path.startswith('/ml/'):
            return jsonify({"error": "Too Many Requests", "message": "Rate limit exceeded"}), 429
        return render_template('429.html'), 429

    @app.errorhandler(500)
    def handle_500(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        if request.path.startswith('/ml/'):
            return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500
        return render_template('500.html'), 500
