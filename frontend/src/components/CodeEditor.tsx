import { indentWithTab } from "@codemirror/commands";
import { cpp } from "@codemirror/lang-cpp";
import { indentUnit } from "@codemirror/language";
import { EditorState } from "@codemirror/state";
import { keymap } from "@codemirror/view";
import CodeMirror from "@uiw/react-codemirror";

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
      extensions={[
        cpp(),
        EditorState.tabSize.of(4),
        indentUnit.of("    "),
        keymap.of([indentWithTab]),
      ]}
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
