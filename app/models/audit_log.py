from datetime import datetime

from ..extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)  # create/update/delete/verify/reject/end
    module = db.Column(db.String(64), nullable=False, index=True)  # trips/fuel/documents
    entity_type = db.Column(db.String(64), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    details_json = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    actor = db.relationship("User", foreign_keys=[actor_user_id])
