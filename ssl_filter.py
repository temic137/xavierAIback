import logging

# Configure logging to filter out SSL handshake errors
log = logging.getLogger('werkzeug')

# Define a filter to ignore SSL handshake errors
class SSLErrorFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        # Filter out SSL handshake errors
        if 'code 400' in message and ('Bad request syntax' in message or 'Bad request version' in message):
            return False
        return True

# Apply the filter
log.addFilter(SSLErrorFilter())
