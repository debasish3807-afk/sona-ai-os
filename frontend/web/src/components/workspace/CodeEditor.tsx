import { useState, useRef, useEffect, useCallback } from "react";

interface CodeEditorProps {
  filePath?: string;
  initialContent?: string;
  language?: string;
  onContentChange?: (content: string) => void;
  readOnly?: boolean;
  theme?: "dark" | "light";
}

const KEYWORDS = [
  "import", "from", "def", "class", "return", "if", "elif", "else", "for", "while",
  "try", "except", "finally", "with", "as", "async", "await", "yield", "lambda",
  "True", "False", "None", "in", "not", "and", "or", "is", "pass", "raise",
  "continue", "break", "global", "nonlocal", "assert", "del", "print",
];

export function CodeEditor({ filePath, initialContent = "", language = "python", onContentChange, readOnly = false }: CodeEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [isDirty, setIsDirty] = useState(false);
  const [cursorLine, setCursorLine] = useState(1);
  const [cursorCol, setCursorCol] = useState(1);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { setContent(initialContent); setIsDirty(false); }, [initialContent, filePath]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setContent(newContent);
    setIsDirty(true);
    onContentChange?.(newContent);
  };

  const handleCursorMove = (e: React.KeyboardEvent | React.MouseEvent) => {
    const ta = textareaRef.current;
    if (!ta) return;
    const textBefore = ta.value.substring(0, ta.selectionStart);
    setCursorLine((textBefore.match(/\n/g) || []).length + 1);
    setCursorCol(ta.selectionStart - textBefore.lastIndexOf("\n"));
  };

  const lineCount = content.split("\n").length;
  const lineNumbers = Array.from({ length: Math.max(lineCount, 1) }, (_, i) => i + 1);

  // Simple syntax highlight — convert to HTML
  const highlighted = content.split("\n").map((line) => {
    let html = line
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/(["'`])(?:(?!\1|\\).|\\.)*?\1/g, '<span class="text-green-400">$&</span>')
      .replace(/(#.*)$/g, '<span class="text-gray-600">$1</span>');
    
    // Highlight keywords
    for (const kw of KEYWORDS) {
      html = html.replace(new RegExp(`\\b${kw}\\b`, "g"), `<span class="text-blue-400">${kw}</span>`);
    }
    
    // Highlight decorators
    html = html.replace(/(@\w+)/g, '<span class="text-yellow-400">$1</span>');
    
    // Highlight types/classes
    html = html.replace(/```/g, '');  // remove triple backticks in line
    
    return html;
  });

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Editor header */}
      {filePath && (
        <div className="flex items-center justify-between px-3 py-1 bg-gray-900 border-b border-gray-800 shrink-0">
          <div className="flex items-center gap-2 text-xs">
            <svg className="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-gray-300">{filePath}</span>
            {isDirty && <span className="text-yellow-400 font-bold">●</span>}
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{language}</span>
            <span>Ln {cursorLine}, Col {cursorCol}</span>
          </div>
        </div>
      )}
      {/* Editor body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Line numbers */}
        <div className="select-none text-right pr-3 pt-2 pb-2 text-xs text-gray-600 font-mono bg-gray-950 overflow-hidden shrink-0" style={{ minWidth: "40px" }}>
          {lineNumbers.map((n) => (
            <div key={n} className={`leading-5 ${n === cursorLine ? "text-gray-300" : ""}`}>{n}</div>
          ))}
        </div>
        {/* Code area */}
        <div className="flex-1 relative overflow-auto">
          {readOnly ? (
            <div className="p-2 font-mono text-sm leading-5 whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ __html: highlighted.join("\n") }} />
          ) : (
            <textarea
              ref={textareaRef}
              value={content}
              onChange={handleChange}
              onKeyUp={handleCursorMove}
              onClick={handleCursorMove}
              spellCheck={false}
              className="absolute inset-0 w-full h-full p-2 font-mono text-sm leading-5 bg-transparent text-transparent caret-white resize-none outline-none overflow-auto"
              style={{ caretColor: "white" }}
            />
          )}
          {/* Syntax overlay (readable, behind textarea) */}
          {!readOnly && (
            <div className="absolute inset-0 p-2 font-mono text-sm leading-5 pointer-events-none whitespace-pre-wrap overflow-hidden"
              dangerouslySetInnerHTML={{ __html: highlighted.join("\n") }} />
          )}
        </div>
      </div>
    </div>
  );
}
