from flask import Blueprint, request, jsonify, Response, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.Message import Message
from app.models.User import User
from app.models.LinkedInLead import LinkedInLead
from app import db
from pydantic import BaseModel, ValidationError
from typing import Optional
from sqlalchemy import or_, and_
import requests
from datetime import datetime
import json
import time
import logging

# Configuration du logging
logger = logging.getLogger(__name__)

messages_bp = Blueprint('messages', __name__)

# Schémas de validation
class MessageCreateSchema(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageUpdateSchema(BaseModel):
    content: Optional[str] = None
    read_status: Optional[bool] = None

# Constantes
N8N_URL = "https://n8n-b2yn.onrender.com/webhook-test/e5175fdd-fd1d-4257-ba26-865a9233c7fe"
REQUEST_TIMEOUT = 300

# Utilitaires
def to_int_safe(value):
    """Convert safely to int if possible."""
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None

def to_str_safe(value):
    """Convert safely to stripped string."""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip() if value is not None else ''

def get_current_user_id():
    """Extract current user ID from headers or JWT token."""
    # Décommenter si JWT est activé
    # return get_jwt_identity()
    return int(request.headers.get('X-User-ID', 1))

def handle_database_operation(func, *args, **kwargs):
    """Wrapper pour gérer les opérations de base de données."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database operation failed: {e}")
        raise

# Gestion des messages
@messages_bp.route('/', methods=['POST'])
# @jwt_required()
def create_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        msg_data = MessageCreateSchema(**data)
        new_msg = Message(
            sender_id=msg_data.sender_id,
            receiver_id=msg_data.receiver_id,
            content=msg_data.content
        )
        
        handle_database_operation(db.session.add, new_msg)
        handle_database_operation(db.session.commit)
        
        return jsonify(new_msg.to_dict()), 201
        
    except ValidationError as e:
        return jsonify({"message": "Validation error", "errors": e.errors()}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@messages_bp.route('/<int:msg_id>', methods=['GET'])
# @jwt_required()
def get_message(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"message": "Message not found"}), 404
    return jsonify(msg.to_dict())

@messages_bp.route('/all', methods=['GET'])
# @jwt_required()
def list_all_messages():
    messages = Message.query.all()
    return jsonify([msg.to_dict() for msg in messages])

@messages_bp.route('/<int:msg_id>', methods=['PUT'])
# @jwt_required()
def update_message(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"message": "Message not found"}), 404
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        msg_data = MessageUpdateSchema(**data)
        update_data = msg_data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(msg, key, value)
            
        handle_database_operation(db.session.commit)
        return jsonify(msg.to_dict())
        
    except ValidationError as e:
        return jsonify({"message": "Validation error", "errors": e.errors()}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@messages_bp.route('/<int:msg_id>', methods=['DELETE'])
# @jwt_required()
def delete_message(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"message": "Message not found"}), 404
        
    try:
        handle_database_operation(db.session.delete, msg)
        handle_database_operation(db.session.commit)
        return jsonify({"message": "Message deleted successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Conversations
@messages_bp.route('/conversations', methods=['GET'])
# @jwt_required()
def get_conversations():
    """Get all conversations for the current user"""
    try:
        current_user_id = get_current_user_id()

        # Récupérer tous les utilisateurs sauf l'utilisateur actuel
        all_users = User.query.filter(User.id != current_user_id).all()

        conversations = []
        for user in all_users:
            partner_id = user.id

            # Dernier message entre l'utilisateur actuel et ce partenaire
            last_message = Message.query.filter(
                or_(
                    and_(Message.sender_id == current_user_id, Message.receiver_id == partner_id),
                    and_(Message.sender_id == partner_id, Message.receiver_id == current_user_id)
                )
            ).order_by(Message.created_at.desc()).first()

            # Compter les messages non lus de ce partenaire
            unread_count = Message.query.filter(
                Message.sender_id == partner_id,
                Message.receiver_id == current_user_id,
                Message.read_status == False
            ).count()

            conversations.append({
                'id': partner_id,
                'participant': {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'title': 'User',
                    'avatar': '/placeholder.svg'
                },
                'lastMessage': last_message.content if last_message else '',
                'time': last_message.created_at.isoformat() if last_message else None,
                'unreadCount': unread_count
            })

        # Trier par dernier message (plus récent d'abord)
        conversations.sort(key=lambda x: (
            x['time'] is None, 
            x['time'] or '', 
            x['participant']['name']
        ), reverse=True)

        return jsonify({'conversations': conversations})

    except Exception as e:
        logger.error(f"Error in get_conversations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@messages_bp.route('/conversations/<int:partner_id>/messages', methods=['GET'])
# @jwt_required()
def get_conversation_messages(partner_id):
    """Get all messages in a conversation with a specific partner"""
    try:
        current_user_id = get_current_user_id()

        messages = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user_id, Message.receiver_id == partner_id),
                and_(Message.sender_id == partner_id, Message.receiver_id == current_user_id)
            )
        ).order_by(Message.created_at.asc()).all()

        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'senderId': 'me' if msg.sender_id == current_user_id else 'other',
                'content': msg.content,
                'time': msg.created_at.isoformat() if msg.created_at else None,
                'readStatus': msg.read_status
            })

        return jsonify({'messages': message_list})

    except Exception as e:
        logger.error(f"Error in get_conversation_messages: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@messages_bp.route('/conversations/<int:partner_id>/messages', methods=['POST'])
# @jwt_required()
def send_message(partner_id):
    """Send a message to a specific partner"""
    try:
        current_user_id = get_current_user_id()
        data = request.get_json()

        if not data or 'content' not in data:
            return jsonify({'message': 'Content is required'}), 400

        new_message = Message(
            sender_id=current_user_id,
            receiver_id=partner_id,
            content=data['content']
        )

        handle_database_operation(db.session.add, new_message)
        handle_database_operation(db.session.commit)

        return jsonify({
            'id': new_message.id,
            'senderId': 'me',
            'content': new_message.content,
            'time': new_message.created_at.isoformat(),
            'readStatus': new_message.read_status
        }), 201

    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# LinkedIn Leads
def parse_lead_content(content):
    """Parse lead content from various formats."""
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {'Nom Complet': content}
    elif isinstance(content, dict):
        return content
    else:
        return {}

def create_lead_from_data(data, session_id):
    """Create LinkedInLead object from data."""
    content_obj = parse_lead_content(data.get('content', data))
    
    # Extraction et nettoyage des champs
    full_name = to_str_safe(content_obj.get('Nom Complet'))
    title = to_str_safe(content_obj.get('Titre'))
    position = to_str_safe(content_obj.get('Poste'))
    company = to_str_safe(content_obj.get('Entreprise'))
    location = to_str_safe(content_obj.get('Localisation'))
    profile_url = to_str_safe(content_obj.get('URL Profil'))
    education = to_str_safe(content_obj.get('Éducation'))
    personalized_message = to_str_safe(content_obj.get('Message Personnalisé'))
    url_image = to_str_safe(content_obj.get('urlImage'))
    description = to_str_safe(content_obj.get('Description'))

    # Conversions numériques sécurisées
    followers = to_int_safe(content_obj.get('Abonnés'))
    connections = to_int_safe(content_obj.get('Connexions'))
    message_length = to_int_safe(content_obj.get('Longueur Message'))
    total_leads_val = to_int_safe(content_obj.get('totalLeads'))

    # Autres champs
    job_title = to_str_safe(content_obj.get('jobTitle'))
    entreprise = to_str_safe(content_obj.get('entreprise'))
    pages = to_str_safe(content_obj.get('pages'))

    # Parse date
    generation_date = None
    generation_date_str = content_obj.get('Date Génération')
    if isinstance(generation_date_str, str) and generation_date_str.strip():
        try:
            generation_date = datetime.fromisoformat(
                generation_date_str.replace('Z', '+00:00')
            )
        except ValueError:
            generation_date = None

    return LinkedInLead(
        session_id=session_id,
        full_name=full_name,
        title=title,
        position=position,
        company=company,
        location=location,
        profile_url=profile_url,
        followers=followers,
        connections=connections,
        education=education,
        personalized_message=personalized_message,
        message_length=message_length,
        generation_date=generation_date,
        url_image=url_image,
        total_leads=total_leads_val,
        job_title=job_title,
        entreprise=entreprise,
        pages=pages,
        description=description
    )

@messages_bp.route('/linkedin-leads', methods=['POST'])
def trigger_linkedin_leads():
    """Trigger LinkedIn leads generation via n8n."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        logger.info(f"Received data for LinkedIn leads: {data}")

        if 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400

        session_id = str(data.get('id', 'unknown-session'))
        payload = {"message": data['message'], "sessionId": session_id}

        # Capture the app instance while in request context
        app = current_app._get_current_object()

        try:
            response = requests.post(
                N8N_URL,
                json=payload,
                stream=True,
                timeout=REQUEST_TIMEOUT
            )

            if not (200 <= response.status_code < 300):
                logger.error(f"n8n returned error status: {response.status_code}")
                return jsonify({
                    'error': 'n8n service error',
                    'status_code': response.status_code
                }), 502

            def generate():
                with app.app_context():
                    line_count = 0
                    total_leads = None
                    lead_count = 0

                    try:
                        for raw_line in response.iter_lines(decode_unicode=True):
                            line_count += 1
                            if raw_line is None:
                                continue

                            line = raw_line.strip()
                            if not line:
                                continue

                            try:
                                event_data = json.loads(line)
                                event_type = event_data.get('type', 'unknown')

                                if event_type == "stats":
                                    total_leads = event_data.get('totalLeads')
                                    logger.info(f"Received stats: {total_leads} total leads")
                                    yield f"data: {json.dumps(event_data)}\n\n"
                                    continue

                                elif event_type == "item":
                                    lead_count += 1
                                    event_data['leadCount'] = lead_count
                                    if total_leads:
                                        event_data['totalLeads'] = total_leads

                                    # Parser le contenu si c'est une string
                                    content = event_data.get('content', {})
                                    if isinstance(content, str):
                                        try:
                                            content = json.loads(content)
                                            event_data['content'] = content
                                        except json.JSONDecodeError:
                                            pass

                                    # Sauvegarde automatique du lead
                                    try:
                                        new_lead = create_lead_from_data(event_data, session_id)


                                        handle_database_operation(db.session.add, new_lead)
                                        handle_database_operation(db.session.commit)
                                        logger.info(f"Lead saved automatically: {new_lead.full_name}")

                                    except Exception as e:
                                        logger.error(f"Error saving lead: {e}")

                                yield f"data: {json.dumps(event_data)}\n\n"

                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON decode error: {e}")
                                yield f"data: {line}\n\n"

                    except Exception as e:
                        logger.error(f"Stream error: {e}")
                        yield f'data: {{"type": "error", "message": "Stream error"}}\n\n'

                    finally:
                        logger.info(f"Stream completed: {line_count} lines, {lead_count} leads")

            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                }
            )
            
        except requests.RequestException as e:
            logger.error(f"Request to n8n failed: {e}")
            return jsonify({'error': 'Service unavailable'}), 502

    except Exception as ex:
        logger.error(f"Unexpected error in trigger_linkedin_leads: {ex}")
        return jsonify({'error': 'Internal server error'}), 500

@messages_bp.route('/linkedin-leads/<session_id>', methods=['GET'])
# @jwt_required()
def get_linkedin_leads_by_session(session_id):
    """Get all LinkedIn leads for a specific session ID"""
    try:
        leads = LinkedInLead.query.filter_by(session_id=session_id).all()

        leads_data = []
        for lead in leads:
            leads_data.append({
                'id': lead.id,
                'Nom_Complet': lead.full_name,
                'Titre': lead.title or lead.position,
                'Poste': lead.position,
                'Entreprise': lead.company,
                'Localisation': lead.location,
                'URL_Profil': lead.profile_url,
                'Abonnés': lead.followers,
                'Connexions': lead.connections,
                'Éducation': lead.education,
                'Message_Personnalisé': lead.personalized_message,
                'Longueur_Message': lead.message_length,
                'Date_Génération': lead.generation_date.isoformat() if lead.generation_date else None,
                'totalLeads': lead.total_leads,
                'jobTitle': lead.job_title,
                'entreprise': lead.entreprise,
                'location': lead.location,
                'pages': lead.pages,
                'Description': lead.description,
                'urlImage': lead.url_image
            })

        return jsonify({
            'sessionId': session_id,
            'leads': leads_data,
            'total': len(leads_data)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching LinkedIn leads: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@messages_bp.route('/linkedin-leads/save', methods=['POST'])
def save_linkedin_lead():
    """Save a LinkedIn lead to database when user confirms."""
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        session_id = data.get('session_id', 'unknown-session')

        with current_app.app_context():
            # Vérifier si le lead existe déjà
            full_name = to_str_safe(data.get('Nom Complet'))
            existing_lead = LinkedInLead.query.filter_by(
                session_id=session_id,
                full_name=full_name
            ).first()

            if existing_lead:
                return jsonify({
                    'message': 'Lead already exists',
                    'id': existing_lead.id
                }), 200

            # Créer un nouveau lead
            new_lead = create_lead_from_data(data, session_id)
            handle_database_operation(db.session.add, new_lead)
            handle_database_operation(db.session.commit)

            logger.info(f"Lead saved: {full_name}")
            return jsonify({
                'message': 'Lead saved successfully',
                'id': new_lead.id
            }), 201

    except Exception as e:
        logger.error(f"Error saving lead: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Routes supplémentaires pour la rétrocompatibilité
@messages_bp.route('/receive-scraping-result', methods=['POST'])
def receive_scraping_result():
    """Receive one scraping result from n8n and save to database."""
    try:
        raw = request.get_json(force=True, silent=True)

        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format'}), 400

        if not isinstance(raw, dict):
            return jsonify({'error': 'Invalid request format'}), 400

        data = raw.get("data", raw)
        
        # Extraire sessionId
        session_id = 'unknown-session'
        query_raw = raw.get("query")
        if isinstance(query_raw, list) and len(query_raw) > 0:
            first_query = query_raw[0]
            if isinstance(first_query, dict):
                session_id = str(first_query.get("sessionId", session_id))

        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid data format'}), 400

        # Créer et sauvegarder le lead
        with current_app.app_context():
            new_lead = create_lead_from_data(data, session_id)
            handle_database_operation(db.session.add, new_lead)
            handle_database_operation(db.session.commit)

            logger.info(f"Scraping result saved: {new_lead.full_name}")
            return jsonify({'status': 'success'}), 200

    except Exception as e:
        logger.error(f"Error receiving scraping result: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@messages_bp.route('/linkedin-leads/stream/<session_id>', methods=['GET'])
def stream_linkedin_leads(session_id):
    """Stream LinkedIn leads events via Server-Sent Events (SSE)"""
    def generate():
        try:
            message = request.args.get('message')
            if not message:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Message parameter is required'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'begin'})}\n\n"
            time.sleep(0.5)

            payload = {"message": message, "sessionId": session_id}

            try:
                response = requests.post(
                    N8N_URL, 
                    json=payload, 
                    stream=True, 
                    timeout=REQUEST_TIMEOUT
                )

                if not (200 <= response.status_code < 300):
                    yield f"data: {json.dumps({'type': 'error', 'message': f'n8n returned status {response.status_code}'})}\n\n"
                    return

                line_count = 0
                total_leads = None
                lead_count = 0

                for raw_line in response.iter_lines(decode_unicode=True):
                    line_count += 1
                    if raw_line is None:
                        continue

                    line = raw_line.strip()
                    if not line:
                        continue

                    try:
                        event_data = json.loads(line)
                        event_type = event_data.get('type', 'unknown')

                        if event_type == "stats":
                            total_leads = event_data.get('totalLeads')
                            yield f"data: {json.dumps(event_data)}\n\n"
                            continue

                        elif event_type == "item":
                            lead_count += 1
                            event_data['leadCount'] = lead_count
                            if total_leads:
                                event_data['totalLeads'] = total_leads

                            # Parser le contenu si c'est une string
                            content = event_data.get('content', {})
                            if isinstance(content, str):
                                try:
                                    content = json.loads(content)
                                    event_data['content'] = content
                                except json.JSONDecodeError:
                                    pass

                        yield f"data: {json.dumps(event_data)}\n\n"

                    except json.JSONDecodeError:
                        yield f"data: {line}\n\n"

            except requests.RequestException as e:
                logger.error(f"n8n request failed, sending sample data: {e}")
                # Données d'exemple en cas d'échec
                sample_data = {
                    "type": "item",
                    "content": {
                        "Nom Complet": "Nicolas Cherel",
                        "Titre": "CTO | Data Automation Engineer",
                        "Poste": "Data Science Specialist",
                        "Entreprise": "Centrale Paris",
                        "Localisation": "Paris",
                        "URL Profil": "https://linkedin.com/in/example",
                        "Message Personnalisé": "Message d'exemple",
                        "Longueur Message": 150
                    }
                }
                yield f"data: {json.dumps(sample_data)}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Stream error'})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
        }
    )