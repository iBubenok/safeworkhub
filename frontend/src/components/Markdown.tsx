import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Маппинг элементов на Tailwind-классы (в проекте нет typography-плагина,
// поэтому стилизуем теги вручную). react-markdown по умолчанию не рендерит
// сырой HTML — это безопасно от XSS.
const components: Components = {
  h1: ({ children }) => <h1 className="mb-2 mt-4 text-2xl font-bold text-gray-900">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 mt-4 text-xl font-semibold text-gray-900">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1 mt-3 text-lg font-semibold text-gray-900">{children}</h3>,
  p: ({ children }) => <p className="my-2 leading-6 text-gray-700">{children}</p>,
  ul: ({ children }) => <ul className="my-2 list-disc pl-6 text-gray-700">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal pl-6 text-gray-700">{children}</ol>,
  li: ({ children }) => <li className="my-1">{children}</li>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary-600 underline">
      {children}
    </a>
  ),
  code: ({ children }) => <code className="rounded bg-gray-100 px-1 py-0.5 text-sm">{children}</code>,
  pre: ({ children }) => (
    <pre className="my-2 overflow-x-auto rounded bg-gray-900 p-3 text-sm text-gray-100">{children}</pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-4 border-gray-200 pl-3 text-gray-600">{children}</blockquote>
  ),
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  table: ({ children }) => <table className="my-2 w-full border-collapse text-sm">{children}</table>,
  th: ({ children }) => <th className="border border-gray-200 bg-gray-50 px-2 py-1 text-left">{children}</th>,
  td: ({ children }) => <td className="border border-gray-200 px-2 py-1">{children}</td>,
};

export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {children}
    </ReactMarkdown>
  );
}
