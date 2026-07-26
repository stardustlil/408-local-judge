import type { Problem, ProblemInput, Stats, Submission, TestCase } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    let message = `请求失败 (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      if (Array.isArray(body.detail)) message = body.detail.map((item: { msg: string }) => item.msg).join("；");
    } catch {
      // Keep the HTTP fallback when the server did not return JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  getStats: () => request<Stats>("/stats"),
  getProblems: () => request<Problem[]>("/problems"),
  getProblem: (id: number) => request<Problem>(`/problems/${id}`),
  createProblem: (input: ProblemInput) =>
    request<Problem>("/problems", { method: "POST", body: JSON.stringify(input) }),
  updateProblem: (id: number, input: ProblemInput) =>
    request<Problem>(`/problems/${id}`, { method: "PUT", body: JSON.stringify(input) }),
  deleteProblem: (id: number) => request<void>(`/problems/${id}`, { method: "DELETE" }),
  getTestCases: (problemId: number) => request<TestCase[]>(`/problems/${problemId}/test-cases`),
  createTestCase: (problemId: number, input: Pick<TestCase, "name" | "input_data" | "output_data">) =>
    request<TestCase>(`/problems/${problemId}/test-cases`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  uploadTestCase: (problemId: number, data: FormData) =>
    request<TestCase>(`/problems/${problemId}/test-cases/upload`, { method: "POST", body: data }),
  deleteTestCase: (problemId: number, testCaseId: number) =>
    request<void>(`/problems/${problemId}/test-cases/${testCaseId}`, { method: "DELETE" }),
  createSubmission: (problemId: number, language: "c" | "cpp", sourceCode: string) =>
    request<Submission>(`/problems/${problemId}/submissions`, {
      method: "POST",
      body: JSON.stringify({ language, source_code: sourceCode }),
    }),
  getSubmissions: (problemId?: number) =>
    request<Submission[]>(`/submissions${problemId ? `?problem_id=${problemId}` : ""}`),
  getSubmission: (id: number) => request<Submission>(`/submissions/${id}`),
};

