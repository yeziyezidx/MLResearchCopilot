"""
Web application module - Flask app
"""
from flask import Flask, render_template, request, jsonify
import os


def create_app(config=None) -> Flask:
    """
    Create Flask application

    Args:
        config: configuration object

    Returns:
        Flask: Flask application instance
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    )
    
    if config:
        app.config.from_object(config)
    
    # Register routes
    @app.route("/")
    def index():
        """Home page"""
        return render_template("index.html")
    
    @app.route("/results")
    def results():
        """Results page"""
        return render_template("results.html")
    
    @app.route("/health")
    def health():
        """Health check endpoint"""
        return jsonify({"status": "healthy"}), 200
    
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler"""
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler"""
        return jsonify({"error": "Internal server error"}), 500
    
    return app
