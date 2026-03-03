import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# dotenv is optional but recommended for config
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv not installed. Environment variables must be set manually.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMAIL = os.getenv("EMAIL_ADDRESS", "").strip()
PASSWORD = os.getenv("EMAIL_PASSWORD", "").strip()
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# Validate credentials are set and not placeholders
CREDENTIALS_INVALID = False
if not EMAIL:
    logger.error("EMAIL_ADDRESS not configured in environment variables")
    CREDENTIALS_INVALID = True
elif EMAIL == "saikrishy002@gmail.com":
    logger.warning(f"Using default test email: {EMAIL}. This may not work.")

if not PASSWORD or PASSWORD == "your_app_password_here":
    logger.error("EMAIL_PASSWORD not configured or using placeholder. Email notifications will fail.")
    logger.error("For Gmail: Use an App Password (not your regular password). See: https://myaccount.google.com/apppasswords")
    CREDENTIALS_INVALID = True

def send_email(to, subject, body, html=False):
    """
    Send email notification
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        html: If True, treat body as HTML content
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if CREDENTIALS_INVALID:
        error_msg = "Email credentials not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
    
    if not to or not isinstance(to, str):
        error_msg = f"Invalid recipient email: {to}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL
        msg['To'] = to
        msg['Subject'] = subject
        
        # Add body to email (text by default, can be HTML)
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Send via SMTP
        logger.info(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            logger.info(f"Authenticating with email: {EMAIL}")
            server.login(EMAIL, PASSWORD)
            logger.info(f"Sending email to {to}...")
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to}")
        return {'success': True, 'message': f'Email sent to {to}'}
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Authentication failed: Invalid email or password. Check your credentials in .env"
        logger.error(f"{error_msg} - {str(e)}")
        return {'success': False, 'message': error_msg}
    
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error while sending email: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
    
    except TimeoutError as e:
        error_msg = f"Connection timeout: Could not reach {SMTP_SERVER}:{SMTP_PORT}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error sending email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {'success': False, 'message': error_msg}


def test_email_connection():
    """
    Test email configuration and connection.
    Returns detailed diagnostic information.
    """
    logger.info("=" * 50)
    logger.info("Testing Email Configuration")
    logger.info("=" * 50)
    
    results = {
        'email_configured': bool(EMAIL),
        'password_configured': bool(PASSWORD) and PASSWORD != "your_app_password_here",
        'email': EMAIL,
        'smtp_server': SMTP_SERVER,
        'smtp_port': SMTP_PORT,
        'connection_test': False,
        'auth_test': False,
        'message': ''
    }
    
    logger.info(f"Email Address: {EMAIL if EMAIL else '❌ NOT SET'}")
    logger.info(f"Password: {'✓ Configured' if PASSWORD and PASSWORD != 'your_app_password_here' else '❌ NOT SET or placeholder'}")
    logger.info(f"SMTP Server: {SMTP_SERVER}")
    logger.info(f"SMTP Port: {SMTP_PORT}")
    
    if not EMAIL:
        results['message'] = "Email address not configured"
        logger.error(results['message'])
        return results
    
    if not PASSWORD or PASSWORD == "your_app_password_here":
        results['message'] = "Email password not configured or using placeholder"
        logger.error(results['message'])
        return results
    
    try:
        logger.info(f"Attempting connection to {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            results['connection_test'] = True
            logger.info("✓ Connection successful")
            
            logger.info(f"Attempting authentication with {EMAIL}...")
            server.login(EMAIL, PASSWORD)
            results['auth_test'] = True
            logger.info("✓ Authentication successful")
            
        results['message'] = "Email service is working correctly!"
        logger.info("=" * 50)
        logger.info("✓ All tests passed!")
        logger.info("=" * 50)
        return results
    
    except smtplib.SMTPAuthenticationError as e:
        results['message'] = "Authentication failed - check your email and password"
        logger.error(f"❌ {results['message']}: {str(e)}")
        return results
    
    except Exception as e:
        results['message'] = f"Connection failed: {str(e)}"
        logger.error(f"❌ {results['message']}")
        return results