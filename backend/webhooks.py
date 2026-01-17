"""Webhook management and delivery system."""

import httpx
import hmac
import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from .db_models import Webhook, WebhookDelivery
import logging

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manager for webhook operations."""
    
    @staticmethod
    def create_signature(payload: dict, secret: str) -> str:
        """Create HMAC signature for webhook payload."""
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    async def trigger_webhook(
        db: Session,
        user_id: int,
        event_type: str,
        payload: dict
    ):
        """Trigger webhooks for a specific event."""
        webhooks = db.query(Webhook).filter(
            Webhook.user_id == user_id,
            Webhook.is_active == True
        ).all()
        
        for webhook in webhooks:
            # Check if webhook listens to this event
            if event_type not in (webhook.events or []):
                continue
            
            # Add metadata
            full_payload = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload
            }
            
            # Create signature
            signature = WebhookManager.create_signature(full_payload, webhook.secret or "")
            
            # Send webhook
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook.url,
                        json=full_payload,
                        headers={
                            "X-Webhook-Signature": signature,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    # Log delivery
                    delivery = WebhookDelivery(
                        webhook_id=webhook.id,
                        event_type=event_type,
                        payload=full_payload,
                        status_code=response.status_code,
                        response=response.text[:1000]  # Limit size
                    )
                    db.add(delivery)
                    db.commit()
                    
                    logger.info(f"Webhook delivered: {webhook.url} - {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Webhook failed: {webhook.url} - {str(e)}")
                delivery = WebhookDelivery(
                    webhook_id=webhook.id,
                    event_type=event_type,
                    payload=full_payload,
                    status_code=0,
                    response=str(e)
                )
                db.add(delivery)
                db.commit()

