import datetime
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
import pandas as pd
from django.utils import timezone
from .models import PollutionPoint, Comment
from .serializers import PollutionPointSerializer, CommentSerializer, PollutionStatusSerializer
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font


class PollutionPointViewSet(viewsets.ModelViewSet):
    queryset = PollutionPoint.objects.all().order_by('-created_at')
    serializer_class = PollutionPointSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user

        if user.is_authenticated:
            serializer.save(reporter=user)

        else:
            anonymous_name = self.request.data.get('anonymous_name')
            if not anonymous_name:
                raise serializers.ValidationError({
                    "anonymous_name": "Поле 'anonymous_name' обязательно для анонимных пользователей."
                })
            serializer.save(anonymous_name=anonymous_name)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated])
    def comments(self, request, pk=None):
        """
        GET: список комментариев к точке
        POST: создать комментарий для точки
        """
        try:
            point = PollutionPoint.objects.get(pk=pk)
        except PollutionPoint.DoesNotExist:
            return Response({"detail": "PollutionPoint not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            comments = point.comments.all().order_by('-created_at')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(author=request.user, point=point)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['patch'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='set-status',
        serializer_class=PollutionStatusSerializer
    )
    def set_status(self, request, pk=None):
        """Изменить статус точки (в работе / очищено)."""
        point = self.get_object()
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

       

        point.status = new_status
        point.handled_by = user.organization

        if new_status == 'in_progress' and not point.started_at:
            point.started_at = timezone.now()
        elif new_status == 'cleaned':
            if not point.started_at:
                point.started_at = timezone.now()
            point.cleaned_at = timezone.now()

        point.save()
        return Response(PollutionPointSerializer(point).data)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """
        Красивый Excel-отчёт по загрязнениям.
        ?period=today|week|month|year
        """
        period = request.query_params.get('period', 'today')
        now = datetime.datetime.now()
        start_date = None

        if period == 'today':
            start_date = now.date()
        elif period == 'week':
            start_date = now.date() - datetime.timedelta(days=7)
        elif period == 'month':
            start_date = now.date().replace(day=1)
        elif period == 'year':
            start_date = now.date().replace(month=1, day=1)
        else:
            return Response(
                {"detail": "Неверный параметр period. Используйте: today, week, month, year."},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = PollutionPoint.objects.filter(created_at__date__gte=start_date).order_by('created_at')

        # --- Подготавливаем данные ---
        data = []
        for point in queryset:
            started = point.started_at.strftime('%Y-%m-%d') if point.started_at else ''
            cleaned = point.cleaned_at.strftime('%Y-%m-%d') if point.cleaned_at else ''

            data.append({
                'Дата создания': point.created_at.strftime('%Y-%m-%d'),
                'Тип загрязнения': point.get_pollution_type_display(),
                'Описание': point.description or '',
                'Широта': point.latitude,
                'Долгота': point.longitude,
                'Статус': point.get_status_display(),
                'Организация': point.handled_by.name if point.handled_by else '',
                'Дата начала работ': started if point.status in ['in_progress', 'cleaned'] else '',
                'Дата очистки': cleaned if point.status == 'cleaned' else '',
                'Автор': point.reporter.username if point.reporter else point.anonymous_name or 'Аноним',
            })

        if not data:
            return Response({"detail": "Нет данных за выбранный период."}, status=status.HTTP_404_NOT_FOUND)

        df = pd.DataFrame(data)

        # --- Добавляем агрегированную сводку по дням ---
        summary = (
            df.groupby(['Дата создания', 'Статус'])
            .size()
            .reset_index(name='Количество')
            .sort_values(['Дата создания', 'Статус'])
        )

        # --- Создаём Excel ---
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="pollution_report_{period}.xlsx"'

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Детали')
            summary.to_excel(writer, index=False, sheet_name='По дням')

            # --- Украшаем таблицы ---
            workbook = writer.book

            for sheet_name in ['Детали', 'По дням']:
                sheet = workbook[sheet_name]

                # Заголовки — жирные, выравнивание по центру
                for cell in sheet[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')

                # Подгон ширины столбцов под содержимое
                for column_cells in sheet.columns:
                    max_length = 0
                    col_letter = get_column_letter(column_cells[0].column)
                    for cell in column_cells:
                        try:
                            cell_len = len(str(cell.value))
                            if cell_len > max_length:
                                max_length = cell_len
                        except Exception:
                            pass
                    adjusted_width = max_length + 2
                    sheet.column_dimensions[col_letter].width = adjusted_width

        return response


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        point_id = self.kwargs.get('point_pk')
        return Comment.objects.filter(point_id=point_id).order_by('-created_at')

    def perform_create(self, serializer):
        point_id = self.kwargs.get('point_pk')
        serializer.save(author=self.request.user, point_id=point_id)
