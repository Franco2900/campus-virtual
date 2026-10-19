from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import chat_service
from services.chat_service import ChatServiceError
from services.errors import ValidationError

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def _serialize_message(message):
    if message is None:
        return None
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def _serialize_turn(user_message, assistant_message):
    return {
        "conversation_id": getattr(user_message, "conversation_id", None),
        "user_message": _serialize_message(user_message),
        "assistant_message": _serialize_message(assistant_message),
    }


@chat_bp.post("/messages")
@login_required
@require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)
def send_message_endpoint(current_user):
    data = request.get_json(silent=True)
    try:
        user_message, assistant_message = chat_service.respond(current_user, data)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ChatServiceError as error:
        return jsonify({"error": str(error)}), 502
    return jsonify(_serialize_turn(user_message, assistant_message)), 201


@chat_bp.get("/messages")
@login_required
@require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)
def list_messages_endpoint(current_user):
    conversation, messages = chat_service.get_history(current_user)
    conversation_id = conversation.id if conversation else None
    return (
        jsonify(
            {
                "conversation_id": conversation_id,
                "messages": [_serialize_message(m) for m in messages],
            }
        ),
        200,
    )


@chat_bp.delete("/messages")
@login_required
@require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)
def delete_messages_endpoint(current_user):
    chat_service.delete_history(current_user)
    return jsonify({"message": "Historial eliminado"}), 200
