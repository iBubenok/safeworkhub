import * as Tabs from '@radix-ui/react-tabs';

import { useAuth } from '@/hooks/useAuth';
import { ChecklistsTab } from '@/components/checklists/ChecklistsTab';
import { CreateCheckDialog } from '@/components/checklists/CreateCheckDialog';

const tabs = [
  { value: 'all', label: 'Все вместе' },
  { value: 'runs', label: 'Проверки' },
  { value: 'checklists', label: 'Чек-листы' },
];

export function ChecksPage() {
  const { role } = useAuth();
  const isOwner = role === 'org_owner';

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Проверки и чек-листы</h1>
          <p className="mt-1 text-gray-600">
            Конструктор чек-листов и проведение проверок для обеспечения безопасности на рабочем месте.
          </p>
        </div>
        {isOwner && <CreateCheckDialog />}
      </div>

      <Tabs.Root defaultValue="checklists">
        <Tabs.List className="-mb-px flex gap-1 overflow-x-auto border-b border-gray-200">
          {tabs.map((tab) => (
            <Tabs.Trigger
              key={tab.value}
              value={tab.value}
              className="whitespace-nowrap border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-gray-500 transition-colors hover:border-gray-300 hover:text-gray-700 data-[state=active]:border-primary-600 data-[state=active]:text-primary-700"
            >
              {tab.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <Tabs.Content value="all" className="pt-6 focus:outline-none">
          <ChecklistsTab emptyMessage="Проверки и чек-листы не найдены" />
        </Tabs.Content>
        <Tabs.Content value="runs" className="pt-6 focus:outline-none">
          <div className="rounded-lg border-2 border-dashed border-gray-300 p-10 text-center">
            <h2 className="text-lg font-semibold text-gray-900">Проверки</h2>
            <p className="mt-1 text-sm text-gray-500">
              Проведение проверок по чек-листам — в разработке (следующий этап).
            </p>
          </div>
        </Tabs.Content>
        <Tabs.Content value="checklists" className="pt-6 focus:outline-none">
          <ChecklistsTab />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
