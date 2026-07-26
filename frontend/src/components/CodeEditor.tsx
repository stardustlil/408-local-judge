import CodeMirror from "@uiw/react-codemirror";
import { cpp } from "@codemirror/lang-cpp";

type CodeEditorProps = {
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  minHeight?: string;
};

export function CodeEditor({ value, onChange, readOnly = false, minHeight = "520px" }: CodeEditorProps) {
  return (
    <CodeMirror
      value={value}
      height={minHeight}
      extensions={[cpp()]}
      onChange={onChange}
      readOnly={readOnly}
      basicSetup={{
        lineNumbers: true,
        highlightActiveLineGutter: !readOnly,
        highlightActiveLine: !readOnly,
        foldGutter: true,
        bracketMatching: true,
        closeBrackets: true,
        autocompletion: true,
        indentOnInput: true,
      }}
      theme="light"
      className="code-editor"
    />
  );
}

