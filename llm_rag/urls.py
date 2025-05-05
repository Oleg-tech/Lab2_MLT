from django.urls import path
from .views import *


urlpatterns = [
    path('add_document', add_document, name='add_document'),
    path('query', query, name='query'),
    path('query_task2', query_q_and_a_assistant, name='query_task2'),
]
