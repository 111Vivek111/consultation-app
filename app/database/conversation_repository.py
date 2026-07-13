from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:

    @staticmethod
    def create(
        db: Session,
        user_id,
        title: str = "New Chat"
    ):

        conversation = Conversation(
            user_id=user_id,
            title=title
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    @staticmethod
    def get_by_id(
        db: Session,
        conversation_id
    ):

        return (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id
    ):

        return (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id
            )
            .order_by(
                Conversation.created_at.desc()
            )
            .all()
        )