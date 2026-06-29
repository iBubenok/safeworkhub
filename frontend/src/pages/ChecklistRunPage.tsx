import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, BookText, CheckCircle2, Save, Trash2 } from 'lucide-react';

import * as runsApi from '@/api/checklistRuns';
import { getErrorMessage } from '@/api/client';
import { useAuth } from '@/hooks/useAuth';
import {
  checklistRunResultLabels,
  checklistRunStatusLabels,
  complianceValueLabels,
} from '@/utils/checklistLabels';
import type { ChecklistComplianceValue, ChecklistRunAnswer } from '@/types';

type Draft = Record<string, { value: string | null; comment: string | null }>;

const complianceOptions: ChecklistComplianceValue[] = ['compliant', 'non_compliant', 'not_applicable'];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'medium', timeStyle: 'short' });
}

function AnswerInput({
  answer,
  value,
  onChange,
  disabled,
}: {
  answer: ChecklistRunAnswer;
  value: string | null;
  onChange: (value: string | null) => void;
  disabled: boolean;
}) {
  if (answer.answer_type === 'compliance') {
    return (
      <div className="flex flex-wrap gap-2">
        {complianceOptions.map((opt) => (
          <button
            key={opt}
            type="button"
            disabled={disabled}
            onClick={() => onChange(value === opt ? null : opt)}
            className={`rounded-full border px-3 py-1 text-sm transition disabled:opacity-60 ${
              value === opt
                ? opt === 'compliant'
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : opt === 'non_compliant'
                    ? 'border-red-500 bg-red-50 text-red-700'
                    : 'border-gray-400 bg-gray-100 text-gray-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            {complianceValueLabels[opt]}
          </button>
        ))}
      </div>
    );
  }

  if (answer.answer_type === 'yes_no') {
    return (
      <div className="flex gap-2">
        {[
          { v: 'true', label: 'Да' },
          { v: 'false', label: 'Нет' },
        ].map((opt) => (
          <button
            key={opt.v}
            type="button"
            disabled={disabled}
            onClick={() => onChange(value === opt.v ? null : opt.v)}
            className={`rounded-full border px-4 py-1 text-sm transition disabled:opacity-60 ${
              value === opt.v
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    );
  }

  if (answer.answer_type === 'number') {
    return (
      <input
        type="number"
        className="input max-w-xs"
        value={value ?? ''}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value || null)}
      />
    );
  }

  return (
    <textarea
      className="input min-h-[60px]"
      value={value ?? ''}
      disabled={disabled}
      placeholder="Ответ / комментарий"
      onChange={(e) => onChange(e.target.value || null)}
    />
  );
}

export function ChecklistRunPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, role } = useAuth();
  const isOwner = role === 'org_owner';

  const { data, isLoading, isError } = useQuery({
    queryKey: ['checklist-run', id],
    queryFn: () => runsApi.getRun(id as string),
    enabled: !!id,
  });

  const [draft, setDraft] = useState<Draft>({});
  const [title, setTitle] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!data) return;
    const next: Draft = {};
    for (const a of data.answers) next[a.id] = { value: a.value, comment: a.comment };
    setDraft(next);
    setTitle(data.title ?? '');
    setNotes(data.notes ?? '');
  }, [data]);

  const canEdit = !!data && data.status === 'in_progress' && (data.conducted_by_id === user?.id || isOwner);

  const buildPayload = () => ({
    title: title.trim() || null,
    notes: notes.trim() || null,
    answers: Object.entries(draft).map(([answer_id, v]) => ({
      answer_id,
      value: v.value,
      comment: v.comment,
    })),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['checklist-run', id] });
    queryClient.invalidateQueries({ queryKey: ['checklist-runs'] });
  };

  const save = useMutation({
    mutationFn: () => runsApi.updateRun(id as string, buildPayload()),
    onSuccess: invalidate,
    onError: (e) => alert(getErrorMessage(e)),
  });

  const complete = useMutation({
    mutationFn: async () => {
      await runsApi.updateRun(id as string, buildPayload());
      return runsApi.completeRun(id as string);
    },
    onSuccess: invalidate,
    onError: (e) => alert(getErrorMessage(e)),
  });

  const remove = useMutation({
    mutationFn: () => runsApi.deleteRun(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checklist-runs'] });
      navigate('/checks');
    },
    onError: (e) => alert(getErrorMessage(e)),
  });

  if (isLoading) return <div className="card h-40 animate-pulse" />;
  if (isError || !data) {
    return (
      <div className="card text-center">
        <p className="text-gray-500">Проверка не найдена</p>
        <Link to="/checks" className="btn-secondary mt-4 inline-block">
          К списку
        </Link>
      </div>
    );
  }

  const busy = save.isPending || complete.isPending || remove.isPending;
  const canDelete = data.conducted_by_id === user?.id || isOwner;

  const setValue = (answerId: string, value: string | null) =>
    setDraft((d) => ({ ...d, [answerId]: { value, comment: d[answerId]?.comment ?? null } }));
  const setComment = (answerId: string, comment: string | null) =>
    setDraft((d) => ({ ...d, [answerId]: { value: d[answerId]?.value ?? null, comment } }));

  const handleComplete = () => {
    if (window.confirm('Завершить проверку? После завершения её нельзя будет изменить.')) complete.mutate();
  };
  const handleDelete = () => {
    if (window.confirm('Удалить проверку без возможности восстановления?')) remove.mutate();
  };

  // Группируем ответы по разделу (group_title), сохраняя порядок.
  const groups: { title: string | null; answers: ChecklistRunAnswer[] }[] = [];
  for (const a of [...data.answers].sort((x, y) => x.sort_order - y.sort_order)) {
    const last = groups[groups.length - 1];
    if (last && last.title === a.group_title) last.answers.push(a);
    else groups.push({ title: a.group_title, answers: [a] });
  }

  return (
    <div className="space-y-4">
      <Link to="/checks" className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
        <ArrowLeft size={16} /> К проверкам и чек-листам
      </Link>

      <article className="card">
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
          <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
            {checklistRunStatusLabels[data.status]}
          </span>
          {data.result && (
            <span
              className={`rounded-full px-2 py-1 font-medium ${
                data.result === 'passed' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}
            >
              {checklistRunResultLabels[data.result]}
              {data.score !== null && ` · ${data.score}%`}
            </span>
          )}
          {data.conducted_by_name && <span>Проверяющий: {data.conducted_by_name}</span>}
          <span>{formatDate(data.created_at)}</span>

          {canDelete && (
            <button
              type="button"
              title="Удалить"
              aria-label="Удалить"
              onClick={handleDelete}
              disabled={busy}
              className="ml-auto rounded p-1.5 text-gray-500 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-40"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>

        {canEdit ? (
          <input
            type="text"
            className="input mt-3 text-lg font-semibold"
            value={title}
            placeholder={data.checklist_title}
            onChange={(e) => setTitle(e.target.value)}
          />
        ) : (
          <h1 className="mt-2 text-2xl font-bold text-gray-900">{data.title || data.checklist_title}</h1>
        )}
        <p className="mt-1 text-sm text-gray-500">Чек-лист: {data.checklist_title}</p>

        <div className="mt-5 space-y-5">
          {groups.map((group, gi) => (
            <div key={gi} className="space-y-3">
              {group.title && <h2 className="text-sm font-semibold text-gray-800">{group.title}</h2>}
              {group.answers.map((answer) => (
                <div key={answer.id} className="rounded-lg border border-gray-200 p-3">
                  <p className="text-gray-900">
                    {answer.item_text}
                    {answer.required && (
                      <span className="ml-1 text-red-500" title="Обязательный">
                        *
                      </span>
                    )}
                  </p>
                  {answer.help_text && <p className="mt-0.5 text-xs text-gray-400">{answer.help_text}</p>}

                  {answer.references.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {answer.references.map((ref, ri) => (
                        <li key={ri} className="flex flex-wrap items-center gap-1.5 text-xs text-gray-500">
                          <BookText className="h-3.5 w-3.5 shrink-0 text-gray-400" />
                          {ref.material_id && (
                            <Link to={`/materials/${ref.material_id}`} className="text-primary-600 underline">
                              {ref.material_title ?? 'Материал'}
                            </Link>
                          )}
                          {ref.note && <span>{ref.note}</span>}
                        </li>
                      ))}
                    </ul>
                  )}

                  <div className="mt-3">
                    <AnswerInput
                      answer={answer}
                      value={draft[answer.id]?.value ?? null}
                      onChange={(v) => setValue(answer.id, v)}
                      disabled={!canEdit}
                    />
                  </div>

                  {answer.answer_type !== 'text' && (
                    <input
                      type="text"
                      className="input mt-2 text-sm"
                      placeholder="Комментарий"
                      value={draft[answer.id]?.comment ?? ''}
                      disabled={!canEdit}
                      onChange={(e) => setComment(answer.id, e.target.value || null)}
                    />
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>

        {canEdit && (
          <div className="mt-5 space-y-3">
            <textarea
              className="input min-h-[60px]"
              placeholder="Общий комментарий по проверке"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="btn-secondary flex items-center gap-1"
                disabled={busy}
                onClick={() => save.mutate()}
              >
                <Save size={16} /> Сохранить
              </button>
              <button
                type="button"
                className="btn-primary flex items-center gap-1"
                disabled={busy}
                onClick={handleComplete}
              >
                <CheckCircle2 size={16} /> Завершить проверку
              </button>
            </div>
          </div>
        )}

        {!canEdit && data.notes && (
          <div className="mt-5 rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
            <span className="font-medium">Комментарий: </span>
            {data.notes}
          </div>
        )}
      </article>
    </div>
  );
}
