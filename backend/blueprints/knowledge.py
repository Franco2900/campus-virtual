from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import knowledge_service
from services.errors import NotFoundError, ValidationError
from services.knowledge_service import KnowledgeServiceError

knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/api/knowledge")


@knowledge_bp.get("/sources")
@login_required
@require_roles(UserRole.ADMIN)
def list_sources_endpoint(current_user):
    sources = knowledge_service.list_sources()
    return jsonify({"sources": [knowledge_service.serialize_source(row) for row in sources]}), 200


@knowledge_bp.post("/sources")
@login_required
@require_roles(UserRole.ADMIN)
def create_source_endpoint(current_user):
    file_storage = request.files.get("file")
    form_data = {
        "name": request.form.get("name"),
        "description": request.form.get("description", ""),
        "source_type": request.form.get("source_type"),
        "target_roles": request.form.getlist("target_roles"),
    }
    try:
        source = knowledge_service.create_source(file_storage, form_data, current_user=current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except KnowledgeServiceError as error:
        return jsonify({"error": str(error)}), 400
    return (
        jsonify(
            {
                "message": "Fuente cargada y procesada correctamente",
                "source": knowledge_service.serialize_source(source),
            }
        ),
        201,
    )


@knowledge_bp.delete("/sources/<int:source_id>")
@login_required
@require_roles(UserRole.ADMIN)
def delete_source_endpoint(current_user, source_id):
    try:
        knowledge_service.delete_source(source_id)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except KnowledgeServiceError as error:
        return jsonify({"error": str(error)}), 500
    return jsonify({"message": "Fuente eliminada"}), 200
