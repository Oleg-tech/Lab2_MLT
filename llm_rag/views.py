import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .utils import extract_text_from_docx
from .ai_requests import get_response, get_prompt
from .vector_store import ChromaVectorStore


vector_store = ChromaVectorStore()


upload_file_param = openapi.Parameter(
    name='file',
    in_=openapi.IN_FORM,
    type=openapi.TYPE_FILE,
    description='Файл для завантаження',
    required=True,
)


@swagger_auto_schema(
    method='post',
    manual_parameters=[upload_file_param],
    operation_description="Завантаження документа у векторне сховище",
    responses={
        200: openapi.Response(description="Документ успішно додано"),
        400: openapi.Response(description="Помилка валідації або обробки файлу"),
    }
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
@csrf_exempt
def add_document(request):
    file_content = ''

    try:
        if 'file' not in request.FILES:
            return JsonResponse({"status": "error", "message": "Файл не передано"}, status=400)

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        file_type = file_name.split('.')[-1] if '.' in file_name else ''

        if file_type.lower() == 'docx':
            try:
                file_content = extract_text_from_docx(uploaded_file.read())
            except Exception as e:
                return JsonResponse(data={"status": "error", "message": f"Помилка при обробці PDF-файлу: {str(e)}"}, status=400)
        else:
            return JsonResponse(data={"status": "error", "message": "Підтримується тільки файл формату .docx"}, status=400)

        result = vector_store.upload_document(
            text=file_content,
            metadata={
                "file_name": file_name,
                "file_size": uploaded_file.size,
                "upload_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        )

        return JsonResponse({"status": "success", 'chunks_number': result, "text": file_content}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Помилка при обробці запиту: {str(e)}"}, status=500)


@swagger_auto_schema(
    method='post',
    operation_description="Пошук найбільш релевантних чанків у векторному сховищі",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['query_text'],
        properties={
            'query_text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст запиту для пошуку'),
            'top_k': openapi.Schema(type=openapi.TYPE_INTEGER, description='Кількість найрелевантніших результатів', default=5),
        },
    ),
    responses={
        200: openapi.Response(description="Успішна відповідь із результатами пошуку"),
        400: openapi.Response(description="Помилка валідації запиту або пошуку"),
    }
)
@api_view(['POST'])
@csrf_exempt
def query(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Тільки POST запити підтримуються"}, status=405)

    try:
        data = json.loads(request.body)

        query_text = data.get('query_text', '')
        if not query_text:
            return JsonResponse({"status": "error", "message": "Відсутній текст запиту"}, status=400)

        top_k = data.get('top_k', 5)
        result = vector_store.get_chunks_by_query(query=query_text, top_k=top_k)

        return JsonResponse({"status": "success", 'result': result}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Неправильний формат JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Помилка при обробці запиту: {str(e)}"}, status=500)


@swagger_auto_schema(
    method='post',
    operation_description="Пошук найбільш релевантних чанків у векторному сховищі",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['query_text'],
        properties={
            'question': openapi.Schema(type=openapi.TYPE_STRING, description='Текст запиту для пошуку'),
            'top_k': openapi.Schema(type=openapi.TYPE_INTEGER, description='Кількість найрелевантніших результатів', default=5),
        },
    ),
    responses={
        200: openapi.Response(description="Успішна відповідь із результатами пошуку"),
        500: openapi.Response(description="Помилка при обробці запиту"),
    }
)
@api_view(['POST'])
@csrf_exempt
def query_q_and_a_assistant(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Тільки POST запити підтримуються"}, status=405)

    try:
        data = json.loads(request.body)

        question = data.get('question', '')
        if not question:
            return JsonResponse({"status": "error", "message": "Відсутній текст запиту"}, status=400)

        top_k = data.get('top_k', 5)

        results = vector_store.get_chunks_by_query(query=question, top_k=top_k)
        text = "\n\n".join([r["text"] for r in results])

        answer = get_response(text=text, question=question)

        return JsonResponse(data={"status": "success", 'result': answer, 'context_chunks': [r["text"] for r in results]}, status=200)
    except Exception as e:
        return JsonResponse(data={"status": "error", "message": f"Помилка при обробці запиту: {str(e)}"}, status=500)
