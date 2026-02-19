"""
Audit logging utility for Fleet-Management.

Usage:
    from app.audit import log_audit
    
    log_audit('CREATE', 'vehicle', vehicle_id, {'plate_no': plate})
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from flask import has_request_context, request
from flask_login import current_user

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Ensure handler exists (will be configured in app/__init__.py)
if not audit_logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    audit_logger.addHandler(handler)


def log_audit(
    action: str,
    entity_type: str,
    entity_id: Optional[int],
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None
) -> None:
    """
    Log an audit event.
    
    Args:
        action: The action performed (CREATE, UPDATE, DELETE, APPROVE, REJECT, etc.)
        entity_type: Type of entity (vehicle, driver, trip, incident, etc.)
        entity_id: ID of the affected entity
        details: Additional context about the action
        user_id: Override user ID (defaults to current_user)
        username: Override username (defaults to current_user)
    """
    # Get user info from current context if not provided
    if user_id is None or username is None:
        if has_request_context() and current_user.is_authenticated:
            if user_id is None:
                user_id = current_user.id
            if username is None:
                username = current_user.username
    
    log_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'audit',
        'user_id': user_id,
        'username': username or 'anonymous',
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'details': details or {},
    }
    
    # Add request context if available
    if has_request_context():
        log_entry['remote_addr'] = request.remote_addr
        log_entry['user_agent'] = request.headers.get('User-Agent', '')[:200]
    
    audit_logger.info(log_entry)


# Convenience functions for common actions
def log_create(entity_type: str, entity_id: int, details: Optional[Dict] = None):
    log_audit('CREATE', entity_type, entity_id, details)


def log_update(entity_type: str, entity_id: int, details: Optional[Dict] = None):
    log_audit('UPDATE', entity_type, entity_id, details)


def log_delete(entity_type: str, entity_id: int, details: Optional[Dict] = None):
    log_audit('DELETE', entity_type, entity_id, details)


def log_approve(entity_type: str, entity_id: int, details: Optional[Dict] = None):
    log_audit('APPROVE', entity_type, entity_id, details)


def log_reject(entity_type: str, entity_id: int, details: Optional[Dict] = None):
    log_audit('REJECT', entity_type, entity_id, details)


def log_login(username: str, success: bool, remote_addr: Optional[str] = None):
    """Log a login attempt."""
    log_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'login_attempt',
        'username': username,
        'success': success,
        'remote_addr': remote_addr,
    }
    if success:
        audit_logger.info(log_entry)
    else:
        audit_logger.warning(log_entry)


def log_password_change(user_id: int, username: str):
    """Log a password change event."""
    log_audit('PASSWORD_CHANGE', 'user', user_id, {'username': username})


def log_role_change(user_id: int, username: str, old_role: str, new_role: str):
    """Log a role change event."""
    log_audit('ROLE_CHANGE', 'user', user_id, {
        'username': username,
        'old_role': old_role,
        'new_role': new_role
    })
