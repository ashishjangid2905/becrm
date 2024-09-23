from typing import Any
from django.core.mail.backends.smtp import EmailBackend

class CustomEmailBackend(EmailBackend):
    def __init__(self, *args, **kwargs: Any):
        self.smtp_host = kwargs.pop('host', 'smtp.gmail.com')
        self.smtp_port = kwargs.pop('port', '587')
        self.smtp_username = kwargs.pop('username', 'productionbepl@gmail.com')
        self.smtp_password = kwargs.pop('password', '!bepl@007')
        self.use_tls = kwargs.pop('use_tls', True)

        super().__init__(
            host = self.smtp_host,
            port = self.smtp_port,
            username = self.smtp_username,
            password = self.smtp_password,
            use_tls = self.use_tls
        )