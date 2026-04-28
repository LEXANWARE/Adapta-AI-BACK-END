import stripe
import logging
from typing import Optional, Dict, Any
from sqlmodel import Session, select
from app.models.user import User
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_API_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

logger = logging.getLogger(__name__)

class PaymentService:
    """Serviço para gerenciar pagamentos e assinaturas via Stripe."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PaymentService, cls).__new__(cls)
        return cls._instance

    def create_checkout_session(self, user: User, price_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """Cria uma sessão de checkout do Stripe."""
        try:
            # Garante que o usuário tenha um Stripe Customer ID
            customer_id = user.stripe_customer_id
            if not customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={"user_id": user.id, "username": user.username}
                )
                customer_id = customer.id
                # Opcional: Atualizar o usuário aqui ou deixar para o webhook
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user.id
                }
            )
            return {"checkout_url": session.url, "session_id": session.id}
        except Exception as e:
            logger.error(f"Erro ao criar sessão de checkout: {str(e)}")
            raise e

    def handle_webhook(self, payload: bytes, sig_header: str, session_db: Session) -> bool:
        """Processa eventos de webhook do Stripe."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error("Payload inválido")
            return False
        except stripe.error.SignatureVerificationError as e:
            logger.error("Assinatura de webhook inválida")
            return False

        # Trata os eventos
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self._handle_checkout_completed(session, session_db)
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            self._handle_subscription_updated(subscription, session_db)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            self._handle_subscription_deleted(subscription, session_db)

        return True

    def _handle_checkout_completed(self, stripe_session: Any, session_db: Session):
        user_id = stripe_session.get('metadata', {}).get('user_id')
        customer_id = stripe_session.get('customer')
        subscription_id = stripe_session.get('subscription')

        if user_id:
            user = session_db.get(User, int(user_id))
            if user:
                user.stripe_customer_id = customer_id
                user.subscription_id = subscription_id
                user.plan_type = "pro" # Por padrão no checkout
                user.subscription_status = "active"
                session_db.add(user)
                session_db.commit()
                logger.info(f"Pagamento concluído para usuário {user_id}")

    def _handle_subscription_updated(self, subscription: Any, session_db: Session):
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        
        statement = select(User).where(User.stripe_customer_id == customer_id)
        user = session_db.exec(statement).first()
        
        if user:
            user.subscription_status = status
            if status == "active":
                user.plan_type = "pro"
            else:
                user.plan_type = "free"
            session_db.add(user)
            session_db.commit()
            logger.info(f"Assinatura atualizada para cliente {customer_id}: {status}")

    def _handle_subscription_deleted(self, subscription: Any, session_db: Session):
        customer_id = subscription.get('customer')
        
        statement = select(User).where(User.stripe_customer_id == customer_id)
        user = session_db.exec(statement).first()
        
        if user:
            user.plan_type = "free"
            user.subscription_status = "canceled"
            user.subscription_id = None
            session_db.add(user)
            session_db.commit()
            logger.info(f"Assinatura cancelada para cliente {customer_id}")

# Instância única
payment_service = PaymentService()
