from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:

    @staticmethod
    def create(
        db: Session,
        conversation_id,
        role,
        content
    ):

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id
    ):
        return (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.created_at.asc()
            )
            .all()
        )
    @staticmethod
    def get_history(
        db,
        conversation_id
    ):

        messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(Message.created_at.asc())
            .all()
        )

        history = []

        for message in messages:

            history.append(
                {
                    "role": message.role,
                    "content": message.content
                }
            )

        return history