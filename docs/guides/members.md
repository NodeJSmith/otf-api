# Members

The members API provides access to your OrangeTheory member profile, membership details,
purchase history, and notification preferences. All member operations are accessed through
`otf.members`.

## Getting Member Details

Retrieve your full member profile:

```python
member = otf.members.get_member_detail()

print(f"Name: {member.first_name} {member.last_name}")
print(f"Email: {member.email}")
print(f"Phone: {member.phone_number}")
print(f"Home Studio: {member.home_studio.name}")
print(f"Member Since: {member.created_date}")
```

!!! tip
    The current member is also available directly on the client as `otf.member` after
    initialization, without making an additional API call.

## Viewing Membership

Get details about your current membership plan:

```python
membership = otf.members.get_member_membership()
print(membership.model_dump_json(indent=2))
```

The membership object contains your plan type, status, and billing details.

## Purchase History

View your purchases including monthly subscriptions, class packs, and other services:

```python
purchases = otf.members.get_member_purchases()

for purchase in purchases:
    print(f"  {purchase.name} - ${purchase.price}")
    print(f"  Studio: {purchase.studio.name}")
```

Each purchase includes the associated studio details, pricing, and quantity information.

## Updating Member Name

Update your first and/or last name on your profile:

```python
# Update both names
updated = otf.members.update_member_name(first_name="Jane", last_name="Smith")
print(f"Updated: {updated.first_name} {updated.last_name}")

# Update only first name (last name stays the same)
updated = otf.members.update_member_name(first_name="Jane")

# Update only last name (first name stays the same)
updated = otf.members.update_member_name(last_name="Smith")
```

!!! note
    If the provided name matches your current name, no API call is made and the
    existing member details are returned unchanged.

## Notification Settings

### SMS Notifications

View and update your SMS notification preferences:

```python
# Get current SMS settings
sms_settings = otf.members.get_sms_notification_settings()
print(f"Promotional: {sms_settings.is_promotional_sms_opt_in}")
print(f"Transactional: {sms_settings.is_transactional_sms_opt_in}")

# Update SMS settings
updated_sms = otf.members.update_sms_notification_settings(
    promotional_enabled=False,
    transactional_enabled=True,
)
```

### Email Notifications

View and update your email notification preferences:

```python
# Get current email settings
email_settings = otf.members.get_email_notification_settings()
print(f"Promotional: {email_settings.is_promotional_email_opt_in}")
print(f"Transactional: {email_settings.is_transactional_email_opt_in}")

# Update email settings
updated_email = otf.members.update_email_notification_settings(
    promotional_enabled=False,
    transactional_enabled=True,
)
```

!!! tip
    Both `update_sms_notification_settings` and `update_email_notification_settings`
    accept optional arguments. Any argument not provided will keep its current value,
    so you can update just one setting without affecting the other.

!!! warning
    Disabling transactional notifications may prevent you from receiving important
    messages like booking confirmations and class cancellation alerts.
