import uuid
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:

    @staticmethod
    def create(
        db: Session,
        user_id,
        filename,
        file_type,
        stored_filename,
        document_id=None,
        status="indexed"
    ):

        document = Document(
            id=document_id or uuid.uuid4(),
            user_id=user_id,
            filename=filename,
            stored_filename=stored_filename,
            file_type=file_type,
            status=status
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def get_user_documents(
        db: Session,
        user_id
    ):

        return (
            db.query(Document)
            .filter(
                Document.user_id == user_id
            )
            .order_by(
                Document.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        document_id
    ):

        return (
            db.query(Document)
            .filter(
                Document.id == document_id
            )
            .first()
        )

    @staticmethod
    def delete(
        db: Session,
        document
    ):

        db.delete(document)
        db.commit()