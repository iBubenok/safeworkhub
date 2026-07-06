"""Сервис подмодуля «Проверки» (проведение проверки по чек-листу)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.db.repositories import ChecklistRepository, ChecklistRunRepository, UserRepository
from app.models.checklist import (
    ChecklistAnswerType,
    ChecklistItem,
    ChecklistNodeType,
    ChecklistStatus,
    ChecklistVisibility,
)
from app.models.checklist_run import (
    ChecklistComplianceValue,
    ChecklistRun,
    ChecklistRunAnswer,
    ChecklistRunResult,
    ChecklistRunStatus,
)
from app.models.user import User
from app.schemas.checklist_run import (
    ChecklistRunCreate,
    ChecklistRunListItem,
    ChecklistRunListResponse,
    ChecklistRunResponse,
    ChecklistRunUpdate,
)
from app.services.utils import log_audit, utcnow


class ChecklistRunService:
    """Сервис проверок по чек-листам."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ChecklistRunRepository(session)
        self.checklist_repo = ChecklistRepository(session)
        self.user_repo = UserRepository(session)

    async def _validate_assignees(self, organization_id: int, assignee_ids: list[UUID]) -> list[User]:
        """Проверить, что все назначаемые — активные участники организации, и вернуть их."""
        if not assignee_ids:
            return []
        unique_ids = list(dict.fromkeys(assignee_ids))
        members = await self.user_repo.get_by_organization(organization_id)
        members_by_id = {user.id: user for user, _role in members if user.is_active}
        selected: list[User] = []
        for user_id in unique_ids:
            user = members_by_id.get(user_id)
            if user is None:
                raise ValidationError("Назначить можно только активных участников вашей организации")
            selected.append(user)
        return selected

    @staticmethod
    def _flatten_items(flat_items: list[ChecklistItem]) -> list[dict[str, Any]]:
        """Развернуть дерево пунктов шаблона в плоский список снимков пунктов (только ITEM).

        Для каждого пункта запоминается заголовок ближайшего раздела-родителя (group_title)
        и снимок ссылок на материалы.
        """
        children_by_parent: dict[UUID | None, list[ChecklistItem]] = {}
        for item in flat_items:
            children_by_parent.setdefault(item.parent_id, []).append(item)

        snapshots: list[dict[str, Any]] = []

        def walk(parent_id: UUID | None, group_title: str | None) -> None:
            for item in sorted(children_by_parent.get(parent_id, []), key=lambda i: i.sort_order):
                if item.node_type == ChecklistNodeType.GROUP:
                    walk(item.id, item.text)
                    continue
                references = [
                    {
                        "material_id": str(ref.material_id) if ref.material_id else None,
                        "material_title": ref.material.title if ref.material else None,
                        "note": ref.note,
                    }
                    for ref in sorted(item.references, key=lambda r: r.sort_order)
                ]
                snapshots.append(
                    {
                        "group_title": group_title,
                        "item_text": item.text,
                        "help_text": item.help_text,
                        "answer_type": item.answer_type,
                        "required": item.required,
                        "references": references,
                    }
                )

        walk(None, None)
        return snapshots

    @staticmethod
    def _counts(answers: list[ChecklistRunAnswer]) -> dict[str, int]:
        """Счётчики по пунктам типа «Соответствие»."""
        gradable = compliant = non_compliant = not_applicable = 0
        for answer in answers:
            if answer.answer_type != ChecklistAnswerType.COMPLIANCE:
                continue
            gradable += 1
            if answer.value == ChecklistComplianceValue.COMPLIANT:
                compliant += 1
            elif answer.value == ChecklistComplianceValue.NON_COMPLIANT:
                non_compliant += 1
            elif answer.value == ChecklistComplianceValue.NOT_APPLICABLE:
                not_applicable += 1
        return {
            "gradable_count": gradable,
            "compliant_count": compliant,
            "non_compliant_count": non_compliant,
            "not_applicable_count": not_applicable,
        }

    @staticmethod
    def _score(compliant: int, non_compliant: int) -> float | None:
        """Процент соответствия: compliant / (compliant + non_compliant), либо None."""
        denominator = compliant + non_compliant
        if denominator == 0:
            return None
        return round(compliant / denominator * 100, 1)

    def _to_response(self, run: ChecklistRun) -> ChecklistRunResponse:
        response = ChecklistRunResponse.model_validate(run)
        response.conducted_by_name = run.conducted_by.name if run.conducted_by else None
        response.score = self._score(run.compliant_count, run.non_compliant_count)
        return response

    def _to_list_item(self, run: ChecklistRun) -> ChecklistRunListItem:
        item = ChecklistRunListItem.model_validate(run)
        item.conducted_by_name = run.conducted_by.name if run.conducted_by else None
        item.score = self._score(run.compliant_count, run.non_compliant_count)
        return item

    async def start_run(
        self,
        *,
        organization_id: int,
        conducted_by_id: UUID,
        data: ChecklistRunCreate,
        request_id: str | None = None,
    ) -> ChecklistRunResponse:
        checklist = await self.checklist_repo.get_with_items(data.checklist_id)
        # Можно проводить проверку по своему чек-листу либо по публичному из другой организации.
        is_accessible = checklist is not None and (
            checklist.organization_id == organization_id or checklist.visibility == ChecklistVisibility.PUBLIC
        )
        if checklist is None or not is_accessible:
            raise NotFoundError("Чек-лист", str(data.checklist_id))
        if checklist.status != ChecklistStatus.PUBLISHED:
            raise ValidationError("Проводить проверку можно только по опубликованному чек-листу")

        snapshots = self._flatten_items(list(checklist.items))
        if not snapshots:
            raise ValidationError("В чек-листе нет пунктов для проверки")

        # Создатель всегда редактор — не дублируем его в списке назначенных.
        assignee_ids = [uid for uid in data.assignee_ids if uid != conducted_by_id]
        assignees = await self._validate_assignees(organization_id, assignee_ids)

        run = ChecklistRun(
            organization_id=organization_id,
            checklist_id=checklist.id,
            checklist_title=checklist.title,
            title=data.title.strip() if data.title and data.title.strip() else None,
            conducted_by_id=conducted_by_id,
            status=ChecklistRunStatus.IN_PROGRESS,
            assignees=assignees,
        )
        self.session.add(run)
        await self.session.flush()

        for index, snap in enumerate(snapshots):
            self.session.add(ChecklistRunAnswer(run_id=run.id, sort_order=index, **snap))
        await self.session.flush()

        # Монотонный счётчик использований шаблона: не уменьшается при удалении проверки.
        await self.checklist_repo.increment_runs(checklist.id)

        await log_audit(
            self.session,
            action="checklist_run_started",
            entity_type="checklist_run",
            entity_id=str(run.id),
            organization_id=organization_id,
            user_id=str(conducted_by_id),
            request_id=request_id,
            details={"checklist_id": str(checklist.id), "items": len(snapshots)},
        )
        loaded = await self.repository.get_with_answers(run.id)
        assert loaded is not None
        return self._to_response(loaded)

    async def list_runs(
        self,
        *,
        organization_id: int,
        status: ChecklistRunStatus | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ChecklistRunListResponse:
        statuses = [status] if status is not None else None
        offset = (page - 1) * page_size
        runs, total = await self.repository.list_for_org(
            organization_id=organization_id,
            statuses=statuses,
            search=search,
            limit=page_size,
            offset=offset,
        )
        items = [self._to_list_item(run) for run in runs]
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return ChecklistRunListResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)

    async def get_run(self, run_id: UUID, *, organization_id: int) -> ChecklistRunResponse:
        run = await self.repository.get_with_answers(run_id)
        if run is None or run.organization_id != organization_id:
            raise NotFoundError("Проверка", str(run_id))
        return self._to_response(run)

    async def set_assignees(
        self,
        run_id: UUID,
        *,
        organization_id: int,
        actor_id: UUID,
        is_owner: bool,
        assignee_ids: list[UUID],
        request_id: str | None = None,
    ) -> ChecklistRunResponse:
        """Заменить состав назначенных. Доступно создателю проверки или владельцу, пока она не завершена."""
        run = await self.repository.get_with_answers(run_id)
        if run is None or run.organization_id != organization_id:
            raise NotFoundError("Проверка", str(run_id))
        if run.conducted_by_id != actor_id and not is_owner:
            raise AuthorizationError(
                "Менять состав назначенных может только создатель проверки или владелец организации"
            )
        if run.status != ChecklistRunStatus.IN_PROGRESS:
            raise ConflictError("Проверка уже завершена — изменить состав нельзя")

        # Создатель всегда редактор — не дублируем его в списке назначенных.
        filtered_ids = [uid for uid in assignee_ids if uid != run.conducted_by_id]
        run.assignees = await self._validate_assignees(organization_id, filtered_ids)
        await self.session.flush()

        await log_audit(
            self.session,
            action="checklist_run_assignees_updated",
            entity_type="checklist_run",
            entity_id=str(run_id),
            organization_id=organization_id,
            user_id=str(actor_id),
            request_id=request_id,
            details={"assignees": [str(assignee.id) for assignee in run.assignees]},
        )
        loaded = await self.repository.get_with_answers(run_id)
        assert loaded is not None
        return self._to_response(loaded)

    def _ensure_editable(self, run: ChecklistRun, *, editor_id: UUID, is_owner: bool) -> None:
        """Редактировать ход проверки может создатель, назначенный или владелец, пока она не завершена."""
        if run.status != ChecklistRunStatus.IN_PROGRESS:
            raise ConflictError("Проверка уже завершена и доступна только для чтения")
        is_assignee = editor_id in {assignee.id for assignee in run.assignees}
        if run.conducted_by_id != editor_id and not is_assignee and not is_owner:
            raise AuthorizationError(
                "Редактировать проверку может проводящий её, назначенный сотрудник или владелец организации"
            )

    async def update_run(
        self,
        run_id: UUID,
        *,
        organization_id: int,
        editor_id: UUID,
        is_owner: bool,
        data: ChecklistRunUpdate,
        request_id: str | None = None,
    ) -> ChecklistRunResponse:
        run = await self.repository.get_with_answers(run_id)
        if run is None or run.organization_id != organization_id:
            raise NotFoundError("Проверка", str(run_id))
        self._ensure_editable(run, editor_id=editor_id, is_owner=is_owner)

        if data.title is not None:
            run.title = data.title.strip() or None
        if data.notes is not None:
            run.notes = data.notes
        if data.answers is not None:
            answers_by_id = {answer.id: answer for answer in run.answers}
            for patch in data.answers:
                answer = answers_by_id.get(patch.answer_id)
                if answer is None:
                    raise NotFoundError("Ответ проверки", str(patch.answer_id))
                answer.value = patch.value
                answer.comment = patch.comment

        counts = self._counts(list(run.answers))
        run.gradable_count = counts["gradable_count"]
        run.compliant_count = counts["compliant_count"]
        run.non_compliant_count = counts["non_compliant_count"]
        run.not_applicable_count = counts["not_applicable_count"]
        await self.session.flush()

        await log_audit(
            self.session,
            action="checklist_run_updated",
            entity_type="checklist_run",
            entity_id=str(run_id),
            organization_id=organization_id,
            user_id=str(editor_id),
            request_id=request_id,
        )
        loaded = await self.repository.get_with_answers(run_id)
        assert loaded is not None
        return self._to_response(loaded)

    async def complete_run(
        self,
        run_id: UUID,
        *,
        organization_id: int,
        editor_id: UUID,
        is_owner: bool,
        request_id: str | None = None,
    ) -> ChecklistRunResponse:
        run = await self.repository.get_with_answers(run_id)
        if run is None or run.organization_id != organization_id:
            raise NotFoundError("Проверка", str(run_id))
        self._ensure_editable(run, editor_id=editor_id, is_owner=is_owner)

        counts = self._counts(list(run.answers))
        run.gradable_count = counts["gradable_count"]
        run.compliant_count = counts["compliant_count"]
        run.non_compliant_count = counts["non_compliant_count"]
        run.not_applicable_count = counts["not_applicable_count"]
        run.result = ChecklistRunResult.HAS_ISSUES if counts["non_compliant_count"] > 0 else ChecklistRunResult.PASSED
        run.status = ChecklistRunStatus.COMPLETED
        run.completed_at = utcnow()
        await self.session.flush()

        await log_audit(
            self.session,
            action="checklist_run_completed",
            entity_type="checklist_run",
            entity_id=str(run_id),
            organization_id=organization_id,
            user_id=str(editor_id),
            request_id=request_id,
            details={"result": run.result, "score": self._score(run.compliant_count, run.non_compliant_count)},
        )
        loaded = await self.repository.get_with_answers(run_id)
        assert loaded is not None
        return self._to_response(loaded)

    async def delete_run(
        self,
        run_id: UUID,
        *,
        organization_id: int,
        user_id: UUID,
        is_owner: bool,
        request_id: str | None = None,
    ) -> None:
        run = await self.repository.get_by_id(run_id)
        if run is None or run.organization_id != organization_id:
            raise NotFoundError("Проверка", str(run_id))
        if run.conducted_by_id != user_id and not is_owner:
            raise AuthorizationError("Удалить проверку может только проводящий её или владелец организации")
        await self.repository.delete(run_id)
        await log_audit(
            self.session,
            action="checklist_run_deleted",
            entity_type="checklist_run",
            entity_id=str(run_id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
        )
