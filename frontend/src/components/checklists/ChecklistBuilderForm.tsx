import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Plus, Search, Trash2, X } from 'lucide-react';

import * as checklistsApi from '@/api/checklists';
import { searchMaterials } from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { checklistAnswerTypeLabels } from '@/utils/checklistLabels';
import type { Checklist, ChecklistAnswerType, ChecklistNode, ChecklistNodeInput, ChecklistStatus } from '@/types';

interface BuilderNode {
  key: string;
  node_type: 'group' | 'item';
  text: string;
  answer_type: ChecklistAnswerType;
  required: boolean;
  help_text: string;
  reference_material_id: string | null;
  reference_material_title: string | null;
  reference_note: string;
  children: BuilderNode[];
}

function makeNode(node_type: 'group' | 'item'): BuilderNode {
  return {
    key: crypto.randomUUID(),
    node_type,
    text: '',
    answer_type: 'compliance',
    required: true,
    help_text: '',
    reference_material_id: null,
    reference_material_title: null,
    reference_note: '',
    children: [],
  };
}

function fromNodes(nodes: ChecklistNode[]): BuilderNode[] {
  return nodes.map((n) => ({
    key: crypto.randomUUID(),
    node_type: n.node_type,
    text: n.text,
    answer_type: n.answer_type ?? 'compliance',
    required: n.required,
    help_text: n.help_text ?? '',
    reference_material_id: n.reference_material_id,
    reference_material_title: n.reference_material_title,
    reference_note: n.reference_note ?? '',
    children: fromNodes(n.children),
  }));
}

function toInput(nodes: BuilderNode[]): ChecklistNodeInput[] {
  return nodes
    .filter((n) => n.text.trim())
    .map((n) =>
      n.node_type === 'group'
        ? { node_type: 'group' as const, text: n.text.trim(), required: false, children: toInput(n.children) }
        : {
            node_type: 'item' as const,
            text: n.text.trim(),
            answer_type: n.answer_type,
            required: n.required,
            help_text: n.help_text.trim() || null,
            reference_material_id: n.reference_material_id,
            reference_note: n.reference_note.trim() || null,
          },
    );
}

function countItems(nodes: ChecklistNodeInput[]): number {
  return nodes.reduce((acc, n) => acc + (n.node_type === 'item' ? 1 : countItems(n.children ?? [])), 0);
}

/** Контекст узла в дереве: список соседей, индекс и родитель. */
interface NodeCtx {
  siblings: BuilderNode[];
  index: number;
  parent: BuilderNode | null;
}

function locate(tree: BuilderNode[], key: string, parent: BuilderNode | null = null): NodeCtx | null {
  for (let i = 0; i < tree.length; i += 1) {
    const node = tree[i];
    if (!node) continue;
    if (node.key === key) return { siblings: tree, index: i, parent };
    const found = locate(node.children, key, node);
    if (found) return found;
  }
  return null;
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

interface NodeHandlers {
  patch: (key: string, patch: Partial<BuilderNode>) => void;
  move: (key: string, delta: number) => void;
  indent: (key: string) => void;
  outdent: (key: string) => void;
  remove: (key: string) => void;
  addChild: (parentKey: string, node_type: 'group' | 'item') => void;
}

function NodeEditor({
  node,
  depth,
  index,
  siblings,
  handlers,
}: {
  node: BuilderNode;
  depth: number;
  index: number;
  siblings: BuilderNode[];
  handlers: NodeHandlers;
}) {
  const prev = index > 0 ? siblings[index - 1] : null;
  const canIndent = prev?.node_type === 'group';

  return (
    <div style={{ marginLeft: depth * 16 }} className="space-y-2">
      <div className={`space-y-2 rounded-lg border p-3 ${node.node_type === 'group' ? 'border-primary-200 bg-primary-50/40' : 'border-gray-200'}`}>
        <div className="flex items-start gap-2">
          <span className="mt-2 shrink-0 text-xs font-medium uppercase text-gray-400">
            {node.node_type === 'group' ? 'Раздел' : 'Пункт'}
          </span>
          <textarea
            className="input min-h-[40px] flex-1"
            placeholder={node.node_type === 'group' ? 'Название раздела' : 'Текст вопроса/проверки'}
            value={node.text}
            onChange={(e) => handlers.patch(node.key, { text: e.target.value })}
          />
          <div className="flex shrink-0 flex-col gap-1">
            <button
              type="button"
              className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
              disabled={index === 0}
              onClick={() => handlers.move(node.key, -1)}
              aria-label="Вверх"
            >
              <ArrowUp className="h-4 w-4" />
            </button>
            <button
              type="button"
              className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
              disabled={index === siblings.length - 1}
              onClick={() => handlers.move(node.key, 1)}
              aria-label="Вниз"
            >
              <ArrowDown className="h-4 w-4" />
            </button>
            <button
              type="button"
              className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
              disabled={!canIndent}
              onClick={() => handlers.indent(node.key)}
              aria-label="Вложить"
              title="Вложить в предыдущий раздел"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
            <button
              type="button"
              className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
              disabled={depth === 0}
              onClick={() => handlers.outdent(node.key)}
              aria-label="Выдвинуть"
              title="Выдвинуть на уровень выше"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
              onClick={() => handlers.remove(node.key)}
              aria-label="Удалить"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        {node.node_type === 'item' ? (
          <>
            <select
              className="input"
              value={node.answer_type}
              onChange={(e) => handlers.patch(node.key, { answer_type: e.target.value as ChecklistAnswerType })}
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
              value={node.help_text}
              onChange={(e) => handlers.patch(node.key, { help_text: e.target.value })}
            />
            <div className="rounded-md bg-gray-50 p-2">
              <span className="mb-1 block text-xs text-gray-500">Ссылка на закон/статью (необязательно)</span>
              <MaterialPicker
                value={
                  node.reference_material_id
                    ? { id: node.reference_material_id, title: node.reference_material_title ?? 'Материал' }
                    : null
                }
                onSelect={(m) =>
                  handlers.patch(node.key, { reference_material_id: m.id, reference_material_title: m.title })
                }
                onClear={() => handlers.patch(node.key, { reference_material_id: null, reference_material_title: null })}
              />
              <input
                className="input mt-2"
                placeholder="Заметка (напр. пункт закона)"
                value={node.reference_note}
                onChange={(e) => handlers.patch(node.key, { reference_note: e.target.value })}
              />
            </div>
          </>
        ) : (
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-secondary flex items-center gap-1 px-2 py-1 text-xs"
              onClick={() => handlers.addChild(node.key, 'group')}
            >
              <Plus size={12} /> Подраздел
            </button>
            <button
              type="button"
              className="btn-secondary flex items-center gap-1 px-2 py-1 text-xs"
              onClick={() => handlers.addChild(node.key, 'item')}
            >
              <Plus size={12} /> Пункт
            </button>
          </div>
        )}
      </div>

      {node.children.map((child, i) => (
        <NodeEditor
          key={child.key}
          node={child}
          depth={depth + 1}
          index={i}
          siblings={node.children}
          handlers={handlers}
        />
      ))}
    </div>
  );
}

/**
 * Тело конструктора чек-листа (без диалога). Поддерживает дерево разделов/пунктов.
 * `onSaved` вызывается после успешного сохранения (родитель закрывает окно).
 */
export function ChecklistBuilderForm({ checklist, onSaved }: { checklist?: Checklist; onSaved: () => void }) {
  const [title, setTitle] = useState(checklist?.title ?? '');
  const [description, setDescription] = useState(checklist?.description ?? '');
  const [tree, setTree] = useState<BuilderNode[]>(() =>
    checklist ? fromNodes(checklist.items) : [makeNode('item')],
  );
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const mutate = (fn: (clone: BuilderNode[]) => void) =>
    setTree((prev) => {
      const clone = structuredClone(prev) as BuilderNode[];
      fn(clone);
      return clone;
    });

  const handlers: NodeHandlers = {
    patch: (key, patch) =>
      mutate((clone) => {
        const ctx = locate(clone, key);
        if (ctx) Object.assign(ctx.siblings[ctx.index] as BuilderNode, patch);
      }),
    move: (key, delta) =>
      mutate((clone) => {
        const ctx = locate(clone, key);
        if (!ctx) return;
        const target = ctx.index + delta;
        if (target < 0 || target >= ctx.siblings.length) return;
        const [n] = ctx.siblings.splice(ctx.index, 1);
        if (n) ctx.siblings.splice(target, 0, n);
      }),
    indent: (key) =>
      mutate((clone) => {
        const ctx = locate(clone, key);
        if (!ctx || ctx.index === 0) return;
        const prev = ctx.siblings[ctx.index - 1];
        if (!prev || prev.node_type !== 'group') return;
        const [n] = ctx.siblings.splice(ctx.index, 1);
        if (n) prev.children.push(n);
      }),
    outdent: (key) =>
      mutate((clone) => {
        const ctx = locate(clone, key);
        if (!ctx || !ctx.parent) return;
        const parentCtx = locate(clone, ctx.parent.key);
        if (!parentCtx) return;
        const [n] = ctx.siblings.splice(ctx.index, 1);
        if (n) parentCtx.siblings.splice(parentCtx.index + 1, 0, n);
      }),
    remove: (key) =>
      mutate((clone) => {
        const ctx = locate(clone, key);
        if (ctx) ctx.siblings.splice(ctx.index, 1);
      }),
    addChild: (parentKey, node_type) =>
      mutate((clone) => {
        const ctx = locate(clone, parentKey);
        if (ctx) (ctx.siblings[ctx.index] as BuilderNode).children.push(makeNode(node_type));
      }),
  };

  const addRoot = (node_type: 'group' | 'item') => setTree((prev) => [...prev, makeNode(node_type)]);

  const save = useMutation({
    mutationFn: (nextStatus: ChecklistStatus) => {
      const items = toInput(tree);
      const payload = { title, description: description || null, status: nextStatus, items };
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
    if (countItems(toInput(tree)) === 0) {
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
          <span className="label mb-0">Структура чек-листа</span>
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-secondary flex items-center gap-1 px-3 py-1 text-xs"
              onClick={() => addRoot('group')}
            >
              <Plus size={14} /> Раздел
            </button>
            <button
              type="button"
              className="btn-secondary flex items-center gap-1 px-3 py-1 text-xs"
              onClick={() => addRoot('item')}
            >
              <Plus size={14} /> Пункт
            </button>
          </div>
        </div>

        {tree.map((node, i) => (
          <NodeEditor key={node.key} node={node} depth={0} index={i} siblings={tree} handlers={handlers} />
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
