import React from 'react';

/**
 * Parses inline markdown elements (bold **, italic *, code `) into React elements.
 */
function parseInline(text) {
  if (!text) return '';

  const parts = [];
  let currentIndex = 0;

  // Match bold (**text** or __text__), italic (*text* or _text_), and inline code (`text`)
  const inlineRegex = /(\*\*|__)(.*?)\1|(\*|_)(.*?)\3|(`)(.*?)\5/g;
  let match;

  while ((match = inlineRegex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > currentIndex) {
      parts.push(text.substring(currentIndex, match.index));
    }

    if (match[1]) {
      // Bold
      parts.push(<strong key={`bold-${match.index}`}>{match[2]}</strong>);
    } else if (match[3]) {
      // Italic
      parts.push(<em key={`em-${match.index}`}>{match[4]}</em>);
    } else if (match[5]) {
      // Code
      parts.push(<code key={`code-${match.index}`}>{match[6]}</code>);
    }

    currentIndex = inlineRegex.lastIndex;
  }

  if (currentIndex < text.length) {
    parts.push(text.substring(currentIndex));
  }

  return parts.length > 0 ? parts : text;
}

/**
 * Parses block-level markdown (headers, bullets, horizontal rules, paragraphs)
 * line-by-line and returns React elements.
 */
export function parseMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let currentList = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Check for list items (e.g. "- item" or "* item")
    const listMatch = line.match(/^\s*[-*+]\s+(.*)$/);
    if (listMatch) {
      const content = parseInline(listMatch[1]);
      currentList.push(<li key={`li-${i}`}>{content}</li>);
      continue;
    }

    // If we were building a list and line is not a list item, flush it
    if (currentList.length > 0 && !listMatch) {
      elements.push(<ul key={`ul-${i}`}>{currentList}</ul>);
      currentList = [];
    }

    // Check for headers (e.g. "### Header")
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const content = parseInline(headingMatch[2]);
      const Tag = `h${level}`;
      elements.push(
        <Tag key={`h-${i}`} className={`md-h${level}`}>
          {content}
        </Tag>
      );
      continue;
    }

    // Check for horizontal rule (e.g. "---")
    if (line.trim() === '---' || line.trim() === '***') {
      elements.push(<hr key={`hr-${i}`} />);
      continue;
    }

    // Empty lines
    if (line.trim() === '') {
      continue;
    }

    // Standard paragraph
    const content = parseInline(line);
    elements.push(
      <p key={`p-${i}`} className="md-p">
        {content}
      </p>
    );
  }

  // Flush any remaining list items at the end
  if (currentList.length > 0) {
    elements.push(<ul key="ul-final">{currentList}</ul>);
  }

  return elements;
}
