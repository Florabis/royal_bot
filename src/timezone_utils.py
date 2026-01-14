from datetime import timedelta, timezone

# Use fixed offset instead of zoneinfo to avoid [Errno 5] I/O errors on restricted filesystems
# EST is UTC-5 (Eastern Standard Time)
EST = timezone(timedelta(hours=-5))
