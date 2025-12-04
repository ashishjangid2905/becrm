from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BankDetail
from django.core.files.base import ContentFile
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from io import BytesIO


@receiver(post_save, sender=BankDetail)
def generate_upi_qr(sender, instance, created, **kwargs):

    """Generate or update QR only when UPI ID or Beneficiary Name changes."""

    # If UPI is not enabled → Remove QR if exists
    if not instance.upi_id:
        return
    
    # Generate QR Data
    upi_uri = instance.get_upi_uri()
    if not upi_uri:
        return
    
    # Create QR Code

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)

    qr.add_data(upi_uri)
    qr.make(fit=True)

    dark_color = (77, 167, 224)
    light_color = (255, 255, 255)

    img = qr.make_image(
        image_factory=StyledPilImage,
        color_mask = SolidFillColorMask(
            back_color=light_color,
            front_color=dark_color
        )
    ).convert("RGB")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"upi_qr_{instance.pk}.png"

    #Save file only if changed
    instance.upi_qr.save(filename, ContentFile(buffer.getvalue()), save=False)

    # Only update the QR field (does not trigger recursion)
    BankDetail.objects.filter(pk=instance.pk).update(upi_qr=instance.upi_qr)
