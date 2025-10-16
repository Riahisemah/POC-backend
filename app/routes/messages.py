from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.Message import Message
from app import db
from pydantic import BaseModel, ValidationError
from typing import Optional

messages_bp = Blueprint('messages', __name__)

class MessageCreateSchema(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageUpdateSchema(BaseModel):
    content: Optional[str]
    read_status: Optional[bool]

@messages_bp.route('/', methods=['POST'])
@jwt_required()
def create_message():
    try:
        data = request.get_json()
        msg_data = MessageCreateSchema(**data)
        new_msg = Message(
            sender_id=msg_data.sender_id,
            receiver_id=msg_data.receiver_id,
            content=msg_data.content
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify(new_msg.to_dict()), 201
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@messages_bp.route('/<int:msg_id>', methods=['GET'])
@jwt_required()
def get_message(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"message": "Message not found"}), 404
    return jsonify(msg.to_dict())

@messages_bp.route('/', methods=['GET'])
@jwt_required()
def list_messages():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = Message.query

    # Filtering example: read_status
    read_status = request.args.get('read_status')
    if read_status is not None:
        if read_status.lower() == 'true':
            query = query.filter_by(read_status=True)
        elif read_status.lower() == 'false':
            query = query.filter_by(read_status=False)

    messages_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    messages = [msg.to_dict() for msg in messages_paginated.items]
    return jsonify({
        "messages": messages,
        "total": messages_paginated.total,
        "page": messages_paginated.page,
        "pages": messages_paginated.pages
    })

@messages_bp.route('/<int:msg_id>', methods=['PUT'])
@jwt_required()
def update_message(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"message": "Message not found"}), 404
    try:
        data = request.get_json()
        msg_data = MessageUpdateSchema(**data)
        for key, value in msg_data.dict(exclude_unset=True).items():
            setattr(msg, key, value)
        db.session.commit()
        return jsonify(msg.to_dict())
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@messages_bp.route('/<int:msg_id>', methods=['DELETE'])
@jwt_required()
def delete_message(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"message": "Message not found"}), 404
    try:
        db.session.delete(msg)
        db.session.commit()
        return jsonify({"message": "Message deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
