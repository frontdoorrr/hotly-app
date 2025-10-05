"""Firebase Cloud Messaging service for push notifications."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import firebase_admin
from fastapi import Depends
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.deps import get_db
from app.models.notification import Notification, NotificationStatus
from app.models.user_device import UserDevice
from app.schemas.notification import PushNotificationRequest, PushNotificationResponse

logger = logging.getLogger(__name__)


class FCMService:
    """Firebase Cloud Messaging service for push notifications."""

    def __init__(self, db: Session):
        """Initialize FCM service with database session."""
        self.db = db
        self._initialize_firebase()

    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                # Initialize with service account credentials
                if settings.FIREBASE_CREDENTIALS_PATH:
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                else:
                    # Use credentials from environment variable
                    if settings.FIREBASE_CREDENTIALS_JSON is None:
                        raise RuntimeError("FIREBASE_CREDENTIALS_JSON is not set")
                    firebase_config = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                    cred = credentials.Certificate(firebase_config)

                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.info("Firebase Admin SDK already initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise RuntimeError(f"Firebase initialization failed: {e}")

    def register_device_token(
        self,
        user_id: str,
        device_token: str,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register FCM device token for user."""
        try:
            # Check if token already exists
            existing_device = (
                self.db.query(UserDevice)
                .filter(
                    UserDevice.user_id == user_id, UserDevice.fcm_token == device_token
                )
                .first()
            )

            if existing_device:
                # Update existing device
                existing_device.last_active = datetime.utcnow()
                existing_device.is_active = True
                if device_info:
                    existing_device.device_info = device_info

                self.db.commit()
                logger.info(f"Updated existing device token for user {user_id}")

                return {
                    "success": True,
                    "message": "Device token updated successfully",
                    "device_id": str(existing_device.id),
                    "is_new": False,
                }

            # Create new device registration
            device = UserDevice(
                user_id=user_id,
                fcm_token=device_token,
                device_info=device_info or {},
                is_active=True,
                registered_at=datetime.utcnow(),
                last_active=datetime.utcnow(),
            )

            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)

            logger.info(f"Registered new device token for user {user_id}")

            return {
                "success": True,
                "message": "Device token registered successfully",
                "device_id": str(device.id),
                "is_new": True,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to register device token: {e}")
            return {"success": False, "error": f"Device registration failed: {e}"}

    def unregister_device_token(
        self, user_id: str, device_token: str
    ) -> Dict[str, Any]:
        """Unregister FCM device token for user."""
        try:
            device = (
                self.db.query(UserDevice)
                .filter(
                    UserDevice.user_id == user_id, UserDevice.fcm_token == device_token
                )
                .first()
            )

            if not device:
                return {"success": False, "error": "Device token not found"}

            device.is_active = False
            device.unregistered_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Unregistered device token for user {user_id}")

            return {
                "success": True,
                "message": "Device token unregistered successfully",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to unregister device token: {e}")
            return {"success": False, "error": f"Device unregistration failed: {e}"}

    def get_user_device_tokens(self, user_id: str) -> List[str]:
        """Get all active device tokens for a user."""
        try:
            devices = (
                self.db.query(UserDevice)
                .filter(
                    UserDevice.user_id == user_id,
                    UserDevice.is_active.is_(True),
                    UserDevice.fcm_token.isnot(None),
                )
                .all()
            )

            return [device.fcm_token for device in devices]

        except Exception as e:
            logger.error(f"Failed to get device tokens for user {user_id}: {e}")
            return []

    def send_push_notification(
        self, request: PushNotificationRequest
    ) -> PushNotificationResponse:
        """Send push notification to multiple users."""
        try:
            # Collect all device tokens for target users
            all_tokens = []
            for user_id in request.user_ids:
                tokens = self.get_user_device_tokens(user_id)
                all_tokens.extend(tokens)

            if not all_tokens:
                logger.warning("No active device tokens found for target users")
                return PushNotificationResponse(
                    success=False,
                    error="No active device tokens found",
                    failure_count=len(request.user_ids),
                )

            # Create FCM message
            message = self._build_fcm_message(
                request, all_tokens[0]
            )  # Single token for now

            # Send to multiple tokens
            response = messaging.send_multicast(
                messaging.MulticastMessage(
                    tokens=all_tokens,
                    notification=message.notification,
                    data=message.data,
                    android=message.android,
                    apns=message.apns,
                )
            )

            # Process response
            success_count = response.success_count
            failure_count = response.failure_count
            failed_tokens = []

            # Handle failed tokens
            if response.responses:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(all_tokens[idx])
                        logger.warning(f"Failed to send to token: {resp.exception}")

            # Record notification in database
            self._record_notification(request, success_count, failure_count)

            # Clean up invalid tokens
            if failed_tokens:
                self._handle_invalid_tokens(failed_tokens)

            logger.info(
                f"Push notification sent: {success_count} success, "
                f"{failure_count} failures"
            )

            return PushNotificationResponse(
                success=success_count > 0,
                success_count=success_count,
                failure_count=failure_count,
                failed_tokens=failed_tokens,
            )

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return PushNotificationResponse(
                success=False, error=str(e), failure_count=len(request.user_ids)
            )

    def send_to_single_device(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> PushNotificationResponse:
        """Send push notification to a single device."""
        request = PushNotificationRequest(
            title=title,
            body=body,
            user_ids=[],  # Not needed for single device
            data=data,
            **kwargs,
        )

        try:
            message = self._build_fcm_message(request, device_token)
            response = messaging.send(message)

            logger.info(f"Single notification sent successfully: {response}")

            return PushNotificationResponse(
                success=True, message_id=response, success_count=1
            )

        except Exception as e:
            logger.error(f"Failed to send single notification: {e}")
            return PushNotificationResponse(
                success=False, error=str(e), failure_count=1
            )

    def _build_fcm_message(
        self, request: PushNotificationRequest, token: str
    ) -> messaging.Message:
        """Build FCM message object."""
        # Base notification
        notification = messaging.Notification(
            title=request.title, body=request.body, image=request.image_url
        )

        # Data payload
        data = request.data or {}
        if request.action_url:
            data["action_url"] = request.action_url
        data["notification_type"] = request.notification_type
        data["timestamp"] = str(datetime.utcnow().isoformat())

        # Convert all data values to strings (FCM requirement)
        str_data = {k: str(v) for k, v in data.items()}

        # Android specific config
        android_config = messaging.AndroidConfig(
            priority=request.priority,
            ttl=(
                timedelta(seconds=request.time_to_live)
                if request.time_to_live
                else None
            ),
            notification=messaging.AndroidNotification(
                title=request.title,
                body=request.body,
                icon="ic_notification",
                color="#FF6B35",
                sound="default",
            ),
        )

        # iOS specific config
        apns_config = messaging.APNSConfig(
            headers={"apns-priority": "10" if request.priority == "high" else "5"},
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=request.title, body=request.body),
                    badge=1,
                    sound="default",
                )
            ),
        )

        return messaging.Message(
            token=token,
            notification=notification,
            data=str_data,
            android=android_config,
            apns=apns_config,
        )

    def _record_notification(
        self, request: PushNotificationRequest, success_count: int, failure_count: int
    ) -> None:
        """Record notification sending result in database."""
        try:
            notification = Notification(
                title=request.title,
                body=request.body,
                notification_type=request.notification_type,
                target_user_ids=request.user_ids,
                data=request.data or {},
                success_count=success_count,
                failure_count=failure_count,
                status=(
                    NotificationStatus.SENT
                    if success_count > 0
                    else NotificationStatus.FAILED
                ),
                sent_at=datetime.utcnow(),
            )

            self.db.add(notification)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to record notification: {e}")

    def _handle_invalid_tokens(self, failed_tokens: List[str]) -> None:
        """Handle invalid/expired FCM tokens."""
        try:
            # Mark tokens as inactive
            self.db.query(UserDevice).filter(
                UserDevice.fcm_token.in_(failed_tokens)
            ).update(
                {"is_active": False, "unregistered_at": datetime.utcnow()},
                synchronize_session=False,
            )

            self.db.commit()

            logger.info(f"Marked {len(failed_tokens)} tokens as inactive")

        except Exception as e:
            logger.error(f"Failed to handle invalid tokens: {e}")

    def get_notification_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get notification statistics for the last N days."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            notifications = (
                self.db.query(Notification)
                .filter(Notification.sent_at >= start_date)
                .all()
            )

            total_sent = len(notifications)
            total_success = sum(n.success_count for n in notifications)
            total_failures = sum(n.failure_count for n in notifications)

            # Group by notification type
            by_type: Dict[str, Dict[str, int]] = {}
            for notification in notifications:
                ntype = notification.notification_type
                if ntype not in by_type:
                    by_type[ntype] = {"count": 0, "success": 0, "failures": 0}

                by_type[ntype]["count"] += 1
                by_type[ntype]["success"] += int(notification.success_count)
                by_type[ntype]["failures"] += int(notification.failure_count)

            return {
                "period_days": days,
                "total_notifications_sent": total_sent,
                "total_success_count": total_success,
                "total_failure_count": total_failures,
                "success_rate": (
                    total_success / (total_success + total_failures)
                    if (total_success + total_failures) > 0
                    else 0.0
                ),
                "by_notification_type": by_type,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get notification stats: {e}")
            return {"error": f"Failed to get stats: {e}"}

    def cleanup_expired_tokens(self, days_inactive: int = 30) -> Dict[str, int]:
        """Clean up device tokens that haven't been active for specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)

            # Find inactive devices
            inactive_devices = (
                self.db.query(UserDevice)
                .filter(
                    UserDevice.last_active < cutoff_date, UserDevice.is_active.is_(True)
                )
                .all()
            )

            # Mark them as inactive
            inactive_count = len(inactive_devices)
            if inactive_count > 0:
                self.db.query(UserDevice).filter(
                    UserDevice.last_active < cutoff_date, UserDevice.is_active is True
                ).update(
                    {"is_active": False, "unregistered_at": datetime.utcnow()},
                    synchronize_session=False,
                )

                self.db.commit()

            logger.info(f"Cleaned up {inactive_count} inactive device tokens")

            return {
                "cleaned_up_count": inactive_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return {"error": f"Cleanup failed: {e}"}


# Factory function for dependency injection
def get_fcm_service(db: Session = Depends(get_db)) -> FCMService:
    """Get FCM service instance."""
    return FCMService(db)
