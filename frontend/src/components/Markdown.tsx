import ReactMarkdown, { type Components } from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';

// Схема санитайзера на базе GitHub-набора (defaultSchema из hast-util-sanitize).
// Разрешаем сырой HTML, но строго по белому списку — скрипты, onerror,
// javascript:-ссылки и т.п. вырезаются. Дополнительно разрешаем:
//  • width/height у <img> — размер как на GitHub (<img src=… height=400>);
//  • style/class у любых тегов — чтобы автор мог делать аккуратную вёрстку
//    (flex-карточки и т.п.). CSS не исполняет код, а авторство статей — у владельца.
const sanitizeSchema = {
  ...defaultSchema,
  // Дополнительно к белому списку GitHub разрешаем video/source (файлы) и iframe
  // (встраивание видео). Хост iframe дополнительно проверяется при рендере.
  tagNames: [...(defaultSchema.tagNames ?? []), 'div', 'span', 'video', 'source', 'iframe'],
  attributes: {
    ...defaultSchema.attributes,
    '*': [...(defaultSchema.attributes?.['*'] ?? []), 'style', 'className'],
    img: [...(defaultSchema.attributes?.img ?? []), 'width', 'height'],
    video: ['src', 'controls', 'width', 'height', 'poster', 'preload', 'muted', 'loop', 'playsInline'],
    source: ['src', 'type', 'srcSet'],
    iframe: ['src', 'width', 'height', 'allow', 'allowFullScreen', 'frameBorder', 'title', 'loading'],
  },
};

// Разрешённые хосты для встраивания видео через iframe (белый список).
const ALLOWED_EMBED_HOSTS = ['youtube.com', 'youtube-nocookie.com', 'vimeo.com', 'rutube.ru'];

function isAllowedEmbed(src: string | undefined): boolean {
  if (!src) return false;
  try {
    const url = new URL(src);
    if (url.protocol !== 'https:') return false;
    const host = url.hostname.toLowerCase();
    return ALLOWED_EMBED_HOSTS.some((d) => host === d || host.endsWith(`.${d}`));
  } catch {
    return false;
  }
}

// Число → пиксели; значения с единицами (например "50%") оставляем как есть.
function sizeToCss(value: string | number | undefined): string | undefined {
  if (value == null) return undefined;
  return /^\d+$/.test(String(value)) ? `${value}px` : String(value);
}

// Маппинг элементов на Tailwind-классы (в проекте нет typography-плагина,
// поэтому стилизуем теги вручную).
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
  code: ({ children }) => (
    <code className="rounded bg-gray-100 px-1 py-0.5 text-sm text-gray-800">{children}</code>
  ),
  // Внутри блока кода сбрасываем «инлайн»-стиль code, иначе светлый текст на
  // светлом фоне становится невидимым — фон и цвет задаёт сам pre.
  pre: ({ children }) => (
    <pre className="my-2 overflow-x-auto rounded bg-gray-900 p-3 text-sm text-gray-100 [&>code]:bg-transparent [&>code]:p-0 [&>code]:text-inherit">
      {children}
    </pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-4 border-gray-200 pl-3 text-gray-600">{children}</blockquote>
  ),
  hr: () => <hr className="my-4 border-t border-gray-200" />,
  img: ({ src, alt, width, height, style: htmlStyle }) => {
    const w = sizeToCss(width);
    const h = sizeToCss(height);
    // Если задано хотя бы одно измерение — переводим в inline-стиль, недостающее
    // ставим auto (сохраняет пропорции). Инлайн-стиль из HTML (border-radius и т.п.)
    // домешиваем сверху. max-w-full всегда ограничивает ширину.
    const sizeStyle = w || h ? { width: w ?? 'auto', height: h ?? 'auto' } : undefined;
    const style = sizeStyle || htmlStyle ? { ...sizeStyle, ...htmlStyle } : undefined;
    return (
      <img
        src={typeof src === 'string' ? src : undefined}
        alt={alt ?? ''}
        style={style}
        className="my-2 h-auto max-w-full rounded border border-gray-200"
      />
    );
  },
  video: ({ src, poster, children }) => (
    <video
      src={typeof src === 'string' ? src : undefined}
      poster={typeof poster === 'string' ? poster : undefined}
      controls
      className="my-2 max-w-full rounded border border-gray-200"
    >
      {children}
    </video>
  ),
  source: ({ src, type }) => (
    <source src={typeof src === 'string' ? src : undefined} type={typeof type === 'string' ? type : undefined} />
  ),
  // iframe рендерим только с доверенных видеохостов (белый список), иначе — просто ссылка.
  iframe: ({ src, title }) => {
    const url = typeof src === 'string' ? src : undefined;
    if (!isAllowedEmbed(url)) {
      return url ? (
        <a href={url} target="_blank" rel="noopener noreferrer" className="text-primary-600 underline">
          {url}
        </a>
      ) : null;
    }
    return (
      <div className="my-3 aspect-video w-full max-w-2xl">
        <iframe
          src={url}
          title={typeof title === 'string' ? title : 'Видео'}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="h-full w-full rounded border border-gray-200"
        />
      </div>
    );
  },
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  table: ({ children }) => <table className="my-2 w-full border-collapse text-sm">{children}</table>,
  th: ({ children }) => <th className="border border-gray-200 bg-gray-50 px-2 py-1 text-left">{children}</th>,
  td: ({ children }) => <td className="border border-gray-200 px-2 py-1">{children}</td>,
};

export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      // Порядок важен: rehypeRaw парсит HTML, затем rehypeSanitize чистит его.
      rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
      components={components}
    >
      {children}
    </ReactMarkdown>
  );
}
