export type Sample = {
  input: string;
  output: string;
};

export type Problem = {
  id: number;
  title: string;
  description: string;
  input_format: string;
  output_format: string;
  constraints: string;
  samples: Sample[];
  tags: string[];
  time_limit_ms: number;
  memory_limit_mb: number;
  test_case_count: number;
  submission_count: number;
  accepted: boolean;
  created_at: string;
  updated_at: string;
};

export type ProblemInput = Omit<
  Problem,
  "id" | "test_case_count" | "submission_count" | "accepted" | "created_at" | "updated_at"
>;

export type TestCase = {
  id: number;
  problem_id: number;
  name: string;
  ordinal: number;
  input_data: string;
  output_data: string;
  created_at: string;
};

export type CaseResult = {
  case: number;
  name: string;
  status: JudgeStatus;
  time_ms: number;
  message: string;
};

export type JudgeStatus =
  | "Queued"
  | "Judging"
  | "Accepted"
  | "Wrong Answer"
  | "Compile Error"
  | "Runtime Error"
  | "Time Limit Exceeded"
  | "Memory Limit Exceeded"
  | "System Error";

export type Submission = {
  id: number;
  problem_id: number;
  problem_title: string;
  language: "c" | "cpp";
  source_code: string;
  status: JudgeStatus;
  compile_output: string;
  judge_message: string;
  case_results: CaseResult[];
  runtime_ms: number | null;
  memory_kb: number | null;
  created_at: string;
  updated_at: string;
};

export type Stats = {
  problem_count: number;
  solved_count: number;
  submission_count: number;
  accepted_count: number;
  tag_counts: Record<string, number>;
};

