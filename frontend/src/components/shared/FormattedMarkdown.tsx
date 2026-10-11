import React from 'react';

interface FormattedMarkdownProps {
  content: string;
  isRtl?: boolean;
}

export const FormattedMarkdown: React.FC<FormattedMarkdownProps> = ({ content, isRtl = false }) => {
  if (!content) return null;

  // Process text block into sections (Headings, Tables, Lists, Callouts, Paragraphs)
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let tableRows: string[][] = [];
  let inTable = false;
  let listItems: string[] = [];
  let inList = false;
  let keyIndex = 0;

  const renderInline = (text: string) => {
    // Parse **bold**, *italic*, `code`, and [link](url)
    const parts: React.ReactNode[] = [];
    let remaining = text;

    while (remaining.length > 0) {
      // Bold **text**
      const boldMatch = remaining.match(/\*\*(.*?)\*\*/);
      if (boldMatch && boldMatch.index === 0) {
        parts.push(
          <strong key={parts.length} className="font-bold text-teal-950 dark:text-teal-100">
            {boldMatch[1]}
          </strong>
        );
        remaining = remaining.slice(boldMatch[0].length);
        continue;
      }

      // Link [text](url)
      const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (linkMatch && linkMatch.index === 0) {
        parts.push(
          <a
            key={parts.length}
            href={linkMatch[2]}
            target="_blank"
            rel="noreferrer"
            className="text-teal-600 hover:text-teal-700 underline font-medium inline-flex items-center gap-0.5"
          >
            {linkMatch[1]}
          </a>
        );
        remaining = remaining.slice(linkMatch[0].length);
        continue;
      }

      // Find next special token
      const nextBold = remaining.indexOf('**');
      const nextLink = remaining.indexOf('[');

      let nextCut = remaining.length;
      if (nextBold !== -1 && nextBold < nextCut) nextCut = nextBold;
      if (nextLink !== -1 && nextLink < nextCut && remaining.includes('](', nextLink)) nextCut = nextLink;

      if (nextCut === remaining.length) {
        parts.push(remaining);
        break;
      } else {
        parts.push(remaining.slice(0, nextCut));
        remaining = remaining.slice(nextCut);
      }
    }

    return parts;
  };

  const flushList = () => {
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`list-${keyIndex++}`} className="my-2.5 space-y-1.5 list-disc pl-5 text-gray-800 leading-relaxed">
          {listItems.map((item, idx) => (
            <li key={idx} className="text-xs sm:text-sm">
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const flushTable = () => {
    if (inTable && tableRows.length > 0) {
      const header = tableRows[0];
      const body = tableRows.slice(1).filter((r) => !r.every((cell) => cell.trim().startsWith('-')));

      elements.push(
        <div key={`table-${keyIndex++}`} className="my-4 overflow-x-auto rounded-xl border border-teal-200/80 shadow-sm bg-white">
          <table className="min-w-full divide-y divide-teal-100 text-xs sm:text-sm">
            <thead className="bg-teal-50/90 text-teal-950 font-bold">
              <tr>
                {header.map((col, cIdx) => (
                  <th key={cIdx} className="px-3.5 py-2.5 text-left font-semibold border-b border-teal-200/70">
                    {renderInline(col.trim())}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {body.map((row, rIdx) => (
                <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-teal-50/30'}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-3.5 py-2 text-gray-800 align-top">
                      {renderInline(cell.trim())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
      inTable = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Check if table line (| ... |)
    if (line.startsWith('|') && line.endsWith('|')) {
      flushList();
      inTable = true;
      const cells = line.split('|').slice(1, -1);
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      flushTable();
    }

    // Check list line (- or * or 1. or •)
    if (line.match(/^[-*•]\s+/) || line.match(/^\d+\.\s+/)) {
      inList = true;
      const cleanItem = line.replace(/^[-*•]\s+/, '').replace(/^\d+\.\s+/, '');
      listItems.push(cleanItem);
      continue;
    } else if (inList && line === '') {
      flushList();
      continue;
    }

    // Headers
    if (line.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${keyIndex++}`} className="mt-4 mb-2 text-base font-bold text-teal-900 border-b border-teal-100 pb-1">
          {renderInline(line.replace(/^###\s+/, ''))}
        </h3>
      );
      continue;
    }

    if (line.startsWith('## ')) {
      flushList();
      elements.push(
        <h2 key={`h2-${keyIndex++}`} className="mt-5 mb-2.5 text-lg font-extrabold text-teal-950 flex items-center gap-2">
          <span className="size-2 rounded-full bg-teal-600 inline-block" />
          {renderInline(line.replace(/^##\s+/, ''))}
        </h2>
      );
      continue;
    }

    if (line.startsWith('# ')) {
      flushList();
      elements.push(
        <h1 key={`h1-${keyIndex++}`} className="mt-6 mb-3 text-xl font-black text-teal-950">
          {renderInline(line.replace(/^#\s+/, ''))}
        </h1>
      );
      continue;
    }

    // Blockquote
    if (line.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote key={`bq-${keyIndex++}`} className="my-3 border-l-4 border-teal-600 bg-teal-50/70 p-3.5 rounded-r-xl text-xs sm:text-sm font-medium text-teal-950">
          {renderInline(line.replace(/^>\s+/, ''))}
        </blockquote>
      );
      continue;
    }

    // Horizontal Rule
    if (line === '---' || line === '***' || line === '___') {
      flushList();
      elements.push(<hr key={`hr-${keyIndex++}`} className="my-4 border-teal-100" />);
      continue;
    }

    // Regular Paragraph
    if (line.length > 0) {
      elements.push(
        <p key={`p-${keyIndex++}`} className="my-2 text-xs sm:text-sm text-gray-800 leading-relaxed font-normal">
          {renderInline(line)}
        </p>
      );
    }
  }

  flushList();
  flushTable();

  return (
    <div className={`space-y-1.5 ${isRtl ? 'text-right leading-loose' : 'text-left leading-normal'}`} dir={isRtl ? 'rtl' : 'ltr'}>
      {elements}
    </div>
  );
};
