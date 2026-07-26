export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

export function languageLabel(language: "c" | "cpp"): string {
  return language === "cpp" ? "C++ 17" : "C 17";
}

export function truncate(value: string, length = 100): string {
  return value.length > length ? `${value.slice(0, length)}...` : value;
}

