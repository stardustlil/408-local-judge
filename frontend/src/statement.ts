import type { Problem, ProblemInput } from "./types";

type StatementFields = Pick<
  Problem | ProblemInput,
  "title" | "description" | "input_format" | "output_format" | "constraints" | "samples"
>;

function fenced(value: string): string {
  return `\`\`\`\n${value.replace(/\s+$/, "")}\n\`\`\``;
}

export function statementMarkdown(problem: StatementFields): string {
  const description = problem.description.trim();
  const isCompleteMarkdown = /^#\s+.+/m.test(description) && /^##\s+.+/m.test(description);
  const hasLegacyFields = Boolean(
    problem.input_format.trim() ||
      problem.output_format.trim() ||
      problem.constraints.trim() ||
      problem.samples.length,
  );

  if (isCompleteMarkdown || !hasLegacyFields) return description;

  const sections = [
    `# ${problem.title.trim() || "未命名题目"}`,
    `## 题目描述\n\n${description}`,
  ];
  if (problem.input_format.trim()) sections.push(`## 输入格式\n\n${problem.input_format.trim()}`);
  if (problem.output_format.trim()) sections.push(`## 输出格式\n\n${problem.output_format.trim()}`);
  problem.samples.forEach((sample, index) => {
    sections.push(
      `## 输入输出样例 #${index + 1}\n\n### 输入 #${index + 1}\n\n${fenced(sample.input)}\n\n### 输出 #${index + 1}\n\n${fenced(sample.output)}`,
    );
  });
  if (problem.constraints.trim()) sections.push(`## 说明/提示\n\n${problem.constraints.trim()}`);
  return sections.join("\n\n");
}
