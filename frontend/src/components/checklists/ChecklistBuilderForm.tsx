import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowDown, ArrowUp, Plus, Search, Trash2, X } from 'lucide-react';

import * as checklistsApi from '@/api/checklists';
import { searchMaterials } from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { checklistAnswerTypeLabels } from '@/utils/checklistLabels';
import type { Checklist, ChecklistAnswerType, ChecklistStatus } from '@/types';

interface BuilderItem {
  key: string;
  text: string;
  answer_type: ChecklistAnswerType;
  required: boolean;
  help_text: string;
  reference_material_id: string | null;
  reference_material_title: string | null;
  reference_note: string;
}

function newItem(): BuilderItem {
  return {
    key: crypto.randomUUID(),
    text: '',
    answer_type: 'compliance',
    required: true,
    help_text: '',
    reference_material_id: null,
    reference_material_title: null,
    reference_note: '',
  };
}

function fromChecklist(checklist: Checklist): BuilderItem[] {
  return checklist.items.map((it) => ({
    key: crypto.randomUUID(),
    text: it.text,
    answer_type: it.answer_type,
    required: it.required,
    help_text: it.help_text ?? '',
    reference_material_id: it.reference_material_id,
    reference_material_title: it.reference_material_title,
    reference_note: it.reference_note ?? '',
  }));
}

/** Поиск-выбор материала-ссылки для пункта. */
function MaterialPicker({
  value,
  onSelect,
  onClear,
}: {
  value: { id: string; title: string } | null;
  onSelect: (m: { id: string; title: string }) => void;
  onClear: () => void;
}) {
  const [query, setQuery] = useState('');
  const { data } = useQuery({
    queryKey: ['checklist-mat-picker', query],
    queryFn: () => searchMaterials({ query, page_size: 6 }),
    enabled: query.trim().length >= 2,
  });

  if (value) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm">
        <span className="min-w-0 flex-1 truncate" title={value.title}>
          {value.title}
        </span>
        <button type="button" className="text-gray-400 hover:text-red-600" onClick={onClear}>
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          className="input pl-9"
          placeholder="Найти материал (НПА/статью)…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {data && data.items.length > 0 && (
        <ul className="mt-1 max-h-36 overflow-y-auto rounded-md border border-gray-200 bg-white text-sm">
          {data.items.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                className="block w-full truncate px-3 py-2 text-left hover:bg-gray-50"
                onClick={() => {
                  onSelect({ id: m.id, title: m.title });
                  setQuery('');
                }}
              >
                {m.title}
              </button>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

/**
 * Тело конструктора чек-листа (без диалога). Без `checklist` — создание, с ним — правка.
 * `onSaved` вызывается после успешного сохранения (родитель закрывает окно).
 */
export function ChecklistBuilderForm({
  checklist,
  onSaved,
}: {
  checklist?: Checklist;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState(checklist?.title ?? '');
  const [description, setDescription] = useState(checklist?.description ?? '');
  const [items, setItems] = useState<BuilderItem[]>(() => (checklist ? fromChecklist(checklist) : [newItem()]));
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const patchItem = (key: string, patch: Partial<BuilderItem>) =>
    setItems((prev) => prev.map((it) => (it.key === key ? { ...it, ...patch } : it)));

  const move = (index: number, delta: number) =>
    setItems((prev) => {
      const target = index + delta;
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      const current = next[index];
      const swapWith = next[target];
      if (!current || !swapWith) return prev;
      next[index] = swapWith;
      next[target] = current;
      return next;
    });

  const save = useMutation({
    mutationFn: (nextStatus: ChecklistStatus) => {
      const payloadItems = items
        .filter((it) => it.text.trim())
        .map((it) => ({
          text: it.text.trim(),
          answer_type: it.answer_type,
          required: it.required,
          help_text: it.help_text.trim() || null,
          reference_material_id: it.reference_material_id,
          reference_note: it.reference_note.trim() || null,
        }));
      const payload = { title, description: description || null, status: nextStatus, items: payloadItems };
      return checklist ? checklistsApi.updateChecklist(checklist.id, payload) : checklistsApi.createChecklist(payload);
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ['checklists'] });
      queryClient.invalidateQueries({ queryKey: ['checklist', saved.id] });
      onSaved();
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const submit = (nextStatus: ChecklistStatus) => {
    setError(null);
    if (!title.trim()) {
      setError('Укажите название чек-листа');
      return;
    }
    if (!items.some((it) => it.text.trim())) {
      setError('Добавьте хотя бы один пункт');
      return;
    }
    save.mutate(nextStatus);
  };

  return (
    <form
      className="space-y-4 overflow-y-auto px-5 py-4"
      onSubmit={(e) => {
        e.preventDefault();
        submit('draft');
      }}
    >
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

      <div>
        <label className="label" htmlFor="cl-title">
          Название
        </label>
        <input id="cl-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
      </div>

      <div>
        <label className="label" htmlFor="cl-desc">
          Описание
        </label>
        <textarea
          id="cl-desc"
          className="input min-h-[60px]"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="label mb-0">Пункты проверки</span>
          <button
            type="button"
            className="btn-secondary flex items-center gap-1 px-3 py-1 text-xs"
            onClick={() => setItems((prev) => [...prev, newItem()])}
          >
            <Plus size={14} /> Добавить пункт
          </button>
        </div>

        {items.map((item, index) => (
          <div key={item.key} className="space-y-2 rounded-lg border border-gray-200 p-3">
            <div className="flex items-start gap-2">
              <span className="mt-2 text-xs font-medium text-gray-400">{index + 1}</span>
              <textarea
                className="input min-h-[44px] flex-1"
                placeholder="Текст вопроса/проверки"
                value={item.text}
                onChange={(e) => patchItem(item.key, { text: e.target.value })}
              />
              <div className="flex flex-col gap-1">
                <button
                  type="button"
                  className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
                  disabled={index === 0}
                  onClick={() => move(index, -1)}
                  aria-label="Вверх"
                >
                  <ArrowUp className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
                  disabled={index === items.length - 1}
                  onClick={() => move(index, 1)}
                  aria-label="Вниз"
                >
                  <ArrowDown className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                  onClick={() => setItems((prev) => prev.filter((it) => it.key !== item.key))}
                  aria-label="Удалить пункт"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            <select
              className="input"
              value={item.answer_type}
              onChange={(e) => patchItem(item.key, { answer_type: e.target.value as ChecklistAnswerType })}
            >
              {(Object.keys(checklistAnswerTypeLabels) as ChecklistAnswerType[]).map((t) => (
                <option key={t} value={t}>
                  {checklistAnswerTypeLabels[t]}
                </option>
              ))}
            </select>

            <input
              className="input"
              placeholder="Подсказка (необязательно)"
              value={item.help_text}
              onChange={(e) => patchItem(item.key, { help_text: e.target.value })}
            />

            <div className="rounded-md bg-gray-50 p-2">
              <span className="mb-1 block text-xs text-gray-500">Ссылка на закон/статью (необязательно)</span>
              <MaterialPicker
                value={
                  item.reference_material_id
                    ? { id: item.reference_material_id, title: item.reference_material_title ?? 'Материал' }
                    : null
                }
                onSelect={(m) => patchItem(item.key, { reference_material_id: m.id, reference_material_title: m.title })}
                onClear={() => patchItem(item.key, { reference_material_id: null, reference_material_title: null })}
              />
              <input
                className="input mt-2"
                placeholder="Заметка (напр. пункт закона)"
                value={item.reference_note}
                onChange={(e) => patchItem(item.key, { reference_note: e.target.value })}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <button type="submit" className="btn-secondary" disabled={save.isPending}>
          {save.isPending ? 'Сохранение...' : 'Сохранить черновик'}
        </button>
        <button type="button" className="btn-primary" disabled={save.isPending} onClick={() => submit('published')}>
          Опубликовать
        </button>
      </div>
    </form>
  );
}
