from datetime import datetime

from ..extensions import db


class DocumentAttachment(db.Model):
    __tablename__ = "document_attachments"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_document_id = db.Column(db.Integer, db.ForeignKey("vehicle_documents.id"), nullable=False, index=True)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    vehicle_document = db.relationship(
        "VehicleDocument",
        backref=db.backref("attachments", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self) -> str:
        return f"<DocumentAttachment {self.id} {self.original_filename}>"
