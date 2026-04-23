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
            "admin": "Thank You for Registering in Investment Portal of Infinite Property Group.",
            "investor-assistant": f"Your investor-assistant Account has been Created by {created_by} in Investment Portal of Infinite Property Group ",
            "fund-assistant": f"Your fund-assistant Account has been Created by {created_by} in Investment Portal of Infinite Property Group",
            "investor": f"Your investor Account has been Created by {created_by} in Investment Portal of Infinite Property Group",
        }

        subject = subjects.get(role, "Your Investment Portal Account Details")

        html_message = f"""
            <html>
                <body>
                    <div>
                        <h2>🎉 Welcome to {'Investment Portal'} 🎉</h2>

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
        subject = "Your One-Time Password (OTP) for Investment Portal of Infinite Property Group"
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
        subject = "Your Infinite Property Group Investment Portal Password Has Been Changed"
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



    @staticmethod
    @shared_task(name="app.template.send_template_mail.send_notif_invested_property_info")
    def send_notif_invested_property_info(email, property_id, property_name, investor_id, investor_name, assistant_id, assistant_name, amount):
        subject = f"Investment Confirmation: {property_name} (Ref: {property_id})"
        formatted_amount = f"${amount:,.2f}" if isinstance(amount, (int, float)) else amount

        html_message = f"""
        <html>
            <head>
                <style>
                    .container {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }}
                    .header {{ background-color: #1a73e8; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .summary-box {{ background-color: #f8f9fa; border-left: 4px solid #1a73e8; padding: 15px; margin: 20px 0; }}
                    .summary-item {{ margin: 8px 0; font-size: 14px; }}
                    .label {{ font-weight: bold; color: #555; display: inline-block; width: 140px; }}
                    .highlight {{ color: #d93025; font-weight: bold; margin-top: 20px; font-size: 13px; }}
                    .footer {{ background-color: #f1f3f4; color: #70757a; padding: 15px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2 style="margin:0;">Investment Confirmed</h2>
                    </div>
                    <div class="content">
                        <p>Dear <strong> {investor_name} (ID : {investor_id}) </strong>,</p>
                        <p>We are pleased to confirm that your investment has been successfully processed through the Investment Portal of Infinite Property Group.</p>
                        
                        <div class="summary-box">
                            <div class="summary-item"><span class="label">Property:</span> {property_name}</div>
                            <div class="summary-item"><span class="label">Property ID:</span> {property_id}</div>
                            <div class="summary-item"><span class="label">Investment Amount:</span> <strong>{formatted_amount}</strong></div>
                            <div class="summary-item"><span class="label">Assistant:</span> {assistant_name} (ID: {assistant_id})</div>
                        </div>

                        <p>Your portfolio has been updated to reflect this transaction. You can view the full details and documents by logging into your dashboard.</p>

                        <div class="highlight">
                            Note: If you did not authorize this transaction, please contact your Exampt Market Dealer immediately.
                        </div>
                    </div>
                    <div class="footer">
                        © 2026 Investment Portal Team <br>
                        This is an automated security notification.
                    </div>
                </div>
            </body>
        </html>
        """
        asyncio.run(MailService.send_mail(email, subject, html_message))


    @staticmethod
    @shared_task(name="app.template.send_template_mail.send_notif_updated_investment_info")
    def send_notif_updated_investment_info(email, property_id, property_name, investor_id, investor_name, assistant_id, assistant_name, amount, old_amount):
        subject = f"Investment Confirmation: {property_name} (Ref: {property_id})"
        formatted_amount = f"${amount:,.2f}" if isinstance(amount, (int, float)) else amount
        formatted_old_amount = f"${old_amount:,.2f}" if isinstance(old_amount, (int, float)) else old_amount

        html_message = f"""
        <html>
            <head>
                <style>
                    .container {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }}
                    .header {{ background-color: #1a73e8; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .summary-box {{ background-color: #f8f9fa; border-left: 4px solid #1a73e8; padding: 15px; margin: 20px 0; }}
                    .summary-item {{ margin: 8px 0; font-size: 14px; }}
                    .label {{ font-weight: bold; color: #555; display: inline-block; width: 140px; }}
                    .highlight {{ color: #d93025; font-weight: bold; margin-top: 20px; font-size: 13px; }}
                    .footer {{ background-color: #f1f3f4; color: #70757a; padding: 15px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2 style="margin:0;">Investment Confirmed</h2>
                    </div>
                    <div class="content">
                        <p>Dear <strong> {investor_name} (ID : {investor_id}) </strong>,</p>
                        <p>We are pleased to confirm that your investment has been updated successfully processed through the Investment Portal.</p>
                        
                        <div class="summary-box">
                            <div class="summary-item"><span class="label">Property:</span> {property_name}</div>
                            <div class="summary-item"><span class="label">Property ID:</span> {property_id}</div>
                            <div class="summary-item"><span class="label">Old Investment Amount:</span> <strong>{formatted_old_amount}</strong></div>
                            <div class="summary-item"><span class="label">As per your request we have update the amount from old amount: </span> 
                            <strong>{formatted_old_amount}</strong> to new amount : <strong>{formatted_amount}</strong></div>
                            <div class="summary-item"><span class="label">Now Your New Investment Amount is :</span> <strong>{formatted_amount}</strong></div>
                            <div class="summary-item"><span class="label">Assistant:</span> {assistant_name} (ID: {assistant_id})</div>
                        </div>

                        <p>Your portfolio has been updated to reflect this transaction. You can view the full details and documents by logging into your dashboard.</p>

                        <div class="highlight">
                            Note: If you did not authorize this transaction, please contact Your Exempt Market Dealer immediately.
                        </div>
                    </div>
                    <div class="footer">
                        © 2026 Investment Portal Team <br>
                        This is an automated security notification.
                    </div>
                </div>
            </body>
        </html>
        """
        print(subject, html_message)
        asyncio.run(MailService.send_mail(email, subject, html_message))







