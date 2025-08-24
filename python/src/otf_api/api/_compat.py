# ruff: noqa


import warnings


_LEGACY_METHOD_MAP = {
    "book_class": "bookings.book_class",
    "book_class_new": "bookings.book_class_new",
    "cancel_booking": "bookings.cancel_booking",
    "cancel_booking_new": "bookings.cancel_booking_new",
    "get_booking": "bookings.get_booking",
    "get_booking_from_class": "bookings.get_booking_from_class",
    "get_booking_from_class_new": "bookings.get_booking_from_class_new",
    "get_booking_new": "bookings.get_booking_new",
    "get_bookings": "bookings.get_bookings",
    "get_bookings_new": "bookings.get_bookings_new",
    "get_bookings_new_by_date": "bookings.get_bookings_new_by_date",
    "get_classes": "bookings.get_classes",
    "get_historical_bookings": "bookings.get_historical_bookings",
    "rate_class": "bookings.rate_class",
    "get_email_notification_settings": "members.get_email_notification_settings",
    "get_member_detail": "members.get_member_detail",
    "get_member_membership": "members.get_member_membership",
    "get_member_purchases": "members.get_member_purchases",
    "get_sms_notification_settings": "members.get_sms_notification_settings",
    "update_email_notification_settings": "members.update_email_notification_settings",
    "update_member_name": "members.update_member_name",
    "update_sms_notification_settings": "members.update_sms_notification_settings",
    "add_favorite_studio": "studios.add_favorite_studio",
    "get_favorite_studios": "studios.get_favorite_studios",
    "get_studio_detail": "studios.get_studio_detail",
    "get_studio_services": "studios.get_studio_services",
    "get_studios_by_geo": "studios.get_studios_by_geo",
    "remove_favorite_studio": "studios.remove_favorite_studio",
    "search_studios_by_geo": "studios.search_studios_by_geo",
    "get_benchmarks": "workouts.get_benchmarks",
    "get_benchmarks_by_challenge_category": "workouts.get_benchmarks_by_challenge_category",
    "get_benchmarks_by_equipment": "workouts.get_benchmarks_by_equipment",
    "get_body_composition_list": "workouts.get_body_composition_list",
    "get_challenge_tracker": "workouts.get_challenge_tracker",
    "get_challenge_tracker_detail": "workouts.get_challenge_tracker_detail",
    "get_hr_history": "workouts.get_hr_history",
    "get_member_lifetime_stats_in_studio": "workouts.get_member_lifetime_stats_in_studio",
    "get_member_lifetime_stats_out_of_studio": "workouts.get_member_lifetime_stats_out_of_studio",
    "get_out_of_studio_workout_history": "workouts.get_out_of_studio_workout_history",
    "get_performance_summary": "workouts.get_performance_summary",
    "get_telemetry": "workouts.get_telemetry",
    "get_workout_from_booking": "workouts.get_workout_from_booking",
    "get_workouts": "workouts.get_workouts",
    "rate_class_from_workout": "workouts.rate_class_from_workout",
}


def _generate_legacy_method(old_name, new_path):
    def method(self, *args, **kwargs):
        warnings.warn(
            f"`Otf.{old_name}()` is deprecated. Use `Otf.{new_path}()` instead.", DeprecationWarning, stacklevel=2
        )

        # Resolve nested attributes like 'bookings.cancel'
        target = self
        for attr in new_path.split("."):
            target = getattr(target, attr)

        return target(*args, **kwargs)

    method.__name__ = old_name
    return method


class _LegacyCompatMixin:
    pass


for legacy_name, new_path in _LEGACY_METHOD_MAP.items():
    setattr(_LegacyCompatMixin, legacy_name, _generate_legacy_method(legacy_name, new_path))
