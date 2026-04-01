from app.core.mail_service import MailService
from celery import shared_task
import asyncio

class MailTemplatesService:
    @staticmethod
    def mask_email(email: str) -> str:
        if "@" not in email:
            return email

        local, domain = email.split("@", 1)

        if len(local) <= 3:
            masked_local = local[:-1] + "*" if len(local) > 1 else "*"
        else:
            masked_local = local[:-3] + "***"

        return f"{masked_local}@{domain}"



    @staticmethod
    @shared_task(name="app.template.send_template_mail.send_credentials_template")
    def send_credentials_template(email: str, name: str, role: str, password: str, created_by: str = None):
        masked_email = MailTemplatesService.mask_email(email)
        role = role.lower()

        subjects = {
            "admin": "Thank You for Registering in Investment Portal",
            "investor-assistant": f"Your investor-assistant Account has been Created for {created_by} in ",
            "fund-assistant": f"Your fund-assistant Account has been Created for {created_by} in Investment Portal",
            "investor": f"Your investor Account has been Created for {created_by} in Investment Portal",
        }

        subject = subjects.get(role, "Your Investment Portal Account Details")

        html_message = f"""
            <html>
                <body>
                    <div>
                        <h2>🎉 Welcome to {created_by or 'Investment Portal'} 🎉</h2>

                        <p>Hi <strong>{name}</strong>,</p>

                        <p>
                            Your <strong>{role.capitalize()}</strong> account has been created successfully.
                        </p>

                        <div class="highlight">
                            <p><strong>Login Credentials</strong></p>
                            <ul>
                                <li><strong>Email:</strong> {masked_email}</li>
                                <li><strong>Password:</strong> {password}</li>
                            </ul>
                        </div>

                        <p>
                            ⚠️ <strong>Security Note:</strong>  
                            This is a temporary password. Please change it immediately after logging in.
                        </p>

                        <div class="footer">
                            Investment Portal Team <br>
                            {f"({created_by})" if created_by else ""}
                        </div>
                    </div>
                </body>
            </html>
        """

        asyncio.run(MailService.send_mail(email, subject, html_message))

    @staticmethod
    @shared_task(name="app.template.send_template_mail.send_otp_template")
    def send_otp_template(email: str, otp: str):
        masked_email = MailTemplatesService.mask_email(email)
        subject = "Your One-Time Password (OTP) for Investment Portal"
        html_message = f"""
            <html>
                <body>
                    <div>
                        <h2>🔐 OTP Verification</h2>

                        <p>Dear <strong>{masked_email}</strong>,</p>

                        <p>Your One-Time Password (OTP) is:</p>

                        <div class="highlight" style="text-align:center;">
                            <div class="otp">{otp}</div>
                        </div>

                        <p>
                            This OTP is valid for <strong>10 minutes</strong>.  
                            Please do not share it with anyone.
                        </p>

                        <div class="footer">
                            Investment Portal Team
                        </div>
                    </div>
                </body>
            </html>
        """

        asyncio.run(MailService.send_mail(email, subject, html_message))


    @staticmethod
    @shared_task(name="app.template.send_template_mail.send_notif_password_change")
    def send_notif_password_change(email: str):
        masked_email = MailTemplatesService.mask_email(email)
        subject = "Your Investment Portal Password Has Been Changed"
        html_message = f"""
            <html>
                <body>
                    <div>
                        <h2>🔒 Password Changed</h2>

                        <p>Dear <strong>{masked_email}</strong>,</p>

                        <p>
                            This is to inform you that your Investment Portal account password has been
                            <strong>changed successfully</strong>.
                        </p>

                        <div class="highlight">
                            <p>
                                If you did <strong>NOT</strong> initiate this change,  
                                please contact support immediately.
                            </p>
                        </div>

                        <div class="footer">
                            Investment Portal Team
                        </div>
                    </div>
                </body>
            </html>
        """
        asyncio.run(MailService.send_mail(email, subject, html_message))


