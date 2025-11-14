from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.User import User
from app.models.Profile import Profile
from app.models.Opportunity import Opportunity
from app.models.Match import Match
from app.models.Message import Message
from app import db
from sqlalchemy import func, case
from datetime import datetime, timedelta

community_bp = Blueprint('community', __name__)

@community_bp.route('/stats', methods=['GET'])
#@jwt_required()
def get_community_stats():
    """Get community statistics"""
    try:
        # Total members (users with profiles)
        total_members = db.session.query(func.count(User.id)).join(Profile).scalar() or 0

        # Active members (users who have logged in recently - last 30 days)
        # For simplicity, we'll consider users with recent profile updates as active
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_members = db.session.query(func.count(User.id)).join(Profile).filter(
            Profile.updated_at >= thirty_days_ago
        ).scalar() or 0

        # Open opportunities (not expired and not closed)
        open_opportunities = Opportunity.query.filter(
            (Opportunity.expiry_date.is_(None)) |
            (Opportunity.expiry_date > datetime.utcnow())
        ).count()

        # Completed missions (matches created - this is a proxy for completed missions)
        completed_missions = Match.query.count()

        # Matching rate (average match score for all matches)
        avg_match_score = db.session.query(func.avg(Match.score)).scalar()
        matching_rate = int(avg_match_score) if avg_match_score else 0

        # New members this month
        first_day_this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_members_this_month = db.session.query(func.count(User.id)).filter(
            User.created_at >= first_day_this_month
        ).scalar() or 0

        return jsonify({
            'totalMembers': total_members,
            'activeMembers': active_members,
            'openOpportunities': open_opportunities,
            'completedMissions': completed_missions,
            'matchingRate': matching_rate,
            'newMembersThisMonth': new_members_this_month
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@community_bp.route('/members', methods=['GET'])
#@jwt_required()
def get_community_members():
    """Get community members with their profiles"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', 'all')
        user_id = request.args.get('user_id', type=int)

        # Query Profile table
        query = Profile.query

        # Filter by user_id if provided
        if user_id:
            query = query.filter(Profile.user_id == user_id)

        # Search filter
        if search:
            query = query.filter(
                db.or_(
                    Profile.title.ilike(f'%{search}%'),
                    Profile.sector.ilike(f'%{search}%'),
                    Profile.location.ilike(f'%{search}%')
                )
            )

        # Status filter (active/inactive based on recent activity)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        if status_filter == 'active':
            query = query.filter(Profile.updated_at >= thirty_days_ago)
        elif status_filter == 'inactive':
            query = query.filter(Profile.updated_at < thirty_days_ago)

        # Get paginated results
        profiles_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        # Use the to_dict method from Profile model
        members = [profile.to_dict() for profile in profiles_paginated.items]

        return jsonify({
            'members': members,
            'total': profiles_paginated.total,
            'page': profiles_paginated.page,
            'pages': profiles_paginated.pages
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@community_bp.route('/opportunities', methods=['GET'])
#@jwt_required()
def get_community_opportunities():
    """Get community opportunities"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        user_id = request.args.get('user_id', type=int)

        query = Opportunity.query

        # Filter by user_id if provided
        if user_id:
            query = query.filter(Opportunity.created_by == user_id)

        # Filter for open opportunities (not expired)
        query = query.filter(
            (Opportunity.expiry_date.is_(None)) |
            (Opportunity.expiry_date > datetime.utcnow())
        )

        opportunities_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        opportunities = []
        for opp in opportunities_paginated.items:
            # Count applicants (matches for this opportunity)
            applicants_count = Match.query.filter_by(opportunity_id=opp.id).count()

            # Calculate average match score
            avg_match_score = db.session.query(func.avg(Match.score)).filter(
                Match.opportunity_id == opp.id
            ).scalar() or 0

            opportunities.append({
                'id': opp.id,
                'title': opp.title,
                'company': opp.company or 'Not specified',
                'type': opp.type or 'Not specified',
                'status': 'Ouvert',  # Since we filtered for open ones
                'applicants': applicants_count,
                'matchScore': int(avg_match_score * 100),
                'createdDate': opp.created_at.strftime('%Y-%m-%d') if opp.created_at else 'Unknown'
            })

        return jsonify({
            'opportunities': opportunities,
            'total': opportunities_paginated.total,
            'page': opportunities_paginated.page,
            'pages': opportunities_paginated.pages
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@community_bp.route('/members/<int:member_id>', methods=['DELETE'])
#@jwt_required()
def delete_member(member_id):
    """Delete a community member"""
    try:
        user = User.query.get(member_id)
        if not user:
            return jsonify({'message': 'Member not found'}), 404

        # Delete associated profile and matches will be cascade deleted
        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'Member deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@community_bp.route('/opportunities/<int:opportunity_id>', methods=['DELETE'])
#@jwt_required()
def delete_opportunity(opportunity_id):
    """Delete an opportunity"""
    try:
        opportunity = Opportunity.query.get(opportunity_id)
        if not opportunity:
            return jsonify({'message': 'Opportunity not found'}), 404

        db.session.delete(opportunity)
        db.session.commit()

        return jsonify({'message': 'Opportunity deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@community_bp.route('/activities', methods=['GET'])
#@jwt_required()
def get_recent_activities():
    """Get recent community activities"""
    try:
        limit = request.args.get('limit', 10, type=int)
        activities = []

        # Recent matches (applications)
        recent_matches = db.session.query(Match, User, Opportunity).join(
            User, Match.profile_id == User.id
        ).join(
            Opportunity, Match.opportunity_id == Opportunity.id
        ).order_by(Match.created_at.desc()).limit(limit).all()

        for match, user, opportunity in recent_matches:
            activities.append({
                'id': f'match_{match.id}',
                'type': 'application',
                'message': f"{user.first_name} {user.last_name} a postulé à \"{opportunity.title}\"",
                'timestamp': match.created_at.isoformat(),
                'time_ago': _get_time_ago(match.created_at),
                'color': 'accent'
            })

        # Recent opportunities created
        recent_opportunities = Opportunity.query.order_by(Opportunity.created_at.desc()).limit(limit).all()

        for opp in recent_opportunities:
            activities.append({
                'id': f'opportunity_{opp.id}',
                'type': 'opportunity',
                'message': f"Nouvelle opportunité \"{opp.title}\" créée",
                'timestamp': opp.created_at.isoformat(),
                'time_ago': _get_time_ago(opp.created_at),
                'color': 'primary'
            })

        # Recent users joined
        recent_users = User.query.order_by(User.created_at.desc()).limit(limit).all()

        for user in recent_users:
            activities.append({
                'id': f'user_{user.id}',
                'type': 'member',
                'message': f"{user.first_name} {user.last_name} a rejoint la communauté",
                'timestamp': user.created_at.isoformat(),
                'time_ago': _get_time_ago(user.created_at),
                'color': 'accent'
            })

        # Sort all activities by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        activities = activities[:limit]

        return jsonify({'activities': activities})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@community_bp.route('/notifications', methods=['GET'])
#@jwt_required()
def get_user_notifications():
    """Get notifications for the current user"""
    try:
        current_user_id = int(request.headers.get('X-User-ID', 1))

        limit = request.args.get('limit', 20, type=int)
        notifications = []

        # Unread messages notifications
        unread_messages = db.session.query(Message, User).join(
            User, Message.sender_id == User.id
        ).filter(
            Message.receiver_id == current_user_id,
            Message.read_status == False
        ).order_by(Message.created_at.desc()).limit(limit).all()

        for message, sender in unread_messages:
            notifications.append({
                'id': f'message_{message.id}',
                'type': 'message',
                'title': 'Nouveau message',
                'message': f"{sender.first_name} {sender.last_name} vous a envoyé un message",
                'time': message.created_at.isoformat(),
                'isRead': False,
                'icon': 'MessageSquare'
            })

        # New matches notifications
        recent_matches = db.session.query(Match, Opportunity).join(
            Opportunity, Match.opportunity_id == Opportunity.id
        ).filter(
            Match.profile_id == current_user_id
        ).order_by(Match.created_at.desc()).limit(limit).all()

        for match, opportunity in recent_matches:
            notifications.append({
                'id': f'match_{match.id}',
                'type': 'match',
                'title': 'Nouveau match trouvé !',
                'message': f"Votre profil correspond à {int(match.score * 100)}% avec l'opportunité '{opportunity.title}'",
                'time': match.created_at.isoformat(),
                'isRead': False,
                'icon': 'Briefcase'
            })

        # New opportunities in user's sector (if they have a profile)
        user_profile = Profile.query.filter_by(user_id=current_user_id).first()
        if user_profile and user_profile.sector:
            recent_sector_opportunities = Opportunity.query.filter(
                Opportunity.sector == user_profile.sector
            ).order_by(Opportunity.created_at.desc()).limit(limit).all()

            for opp in recent_sector_opportunities:
                notifications.append({
                    'id': f'opportunity_{opp.id}',
                    'type': 'opportunity',
                    'title': 'Opportunité dans votre secteur',
                    'message': f"Une nouvelle opportunité '{opp.title}' a été publiée dans votre secteur",
                    'time': opp.created_at.isoformat(),
                    'isRead': False,
                    'icon': 'Briefcase'
                })

        # New community members
        recent_new_members = User.query.filter(
            User.id != current_user_id
        ).order_by(User.created_at.desc()).limit(limit).all()

        for user in recent_new_members:
            notifications.append({
                'id': f'new_member_{user.id}',
                'type': 'community',
                'title': 'Nouveau membre',
                'message': f"{user.first_name} {user.last_name} a rejoint la communauté",
                'time': user.created_at.isoformat(),
                'isRead': False,
                'icon': 'Users'
            })

        # Sort all notifications by time and limit
        notifications.sort(key=lambda x: x['time'], reverse=True)
        notifications = notifications[:limit]

        return jsonify({'notifications': notifications})

    except Exception as e:
        print(f"Error in get_user_notifications: {e}")
        return jsonify({'error': str(e)}), 500

def _get_time_ago(dt):
    """Helper function to get time ago string"""
    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days}j"
    elif diff.seconds >= 3600:
        return f"{diff.seconds // 3600}h"
    elif diff.seconds >= 60:
        return f"{diff.seconds // 60}min"
    else:
        return "maintenant"
