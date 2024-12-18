from django.utils.deprecation import MiddlewareMixin
from django.contrib.messages import get_messages

class ClearMessagesMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        storage = get_messages(request)
        for message in storage:
            pass
        return response