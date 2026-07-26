import { BookOpen, History, LibraryBig, Settings2, SquareTerminal } from "lucide-react";
import { lazy, Suspense } from "react";
import { NavLink, Route, Routes } from "react-router";
import { LoadingState } from "./components/PageState";
import { ProblemListPage } from "./pages/ProblemListPage";

const ProblemPage = lazy(() => import("./pages/ProblemPage").then((module) => ({ default: module.ProblemPage })));
const SubmissionsPage = lazy(() => import("./pages/SubmissionsPage").then((module) => ({ default: module.SubmissionsPage })));
const SubmissionDetailPage = lazy(() => import("./pages/SubmissionDetailPage").then((module) => ({ default: module.SubmissionDetailPage })));
const ManageProblemsPage = lazy(() => import("./pages/ManageProblemsPage").then((module) => ({ default: module.ManageProblemsPage })));
const ProblemEditorPage = lazy(() => import("./pages/ProblemEditorPage").then((module) => ({ default: module.ProblemEditorPage })));

const navItems = [
  { to: "/", end: true, label: "题库", icon: LibraryBig },
  { to: "/submissions", label: "提交记录", icon: History },
  { to: "/manage", label: "题目管理", icon: Settings2 },
];

function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand" aria-label="408 Local Judge 首页">
          <span className="brand-mark"><SquareTerminal size={21} strokeWidth={2.2} /></span>
          <span className="brand-copy">
            <strong>408 Local Judge</strong>
            <small>408 ALGORITHM LAB</small>
          </span>
        </NavLink>
        <nav className="primary-nav" aria-label="主导航">
          {navItems.map(({ to, end, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? "active" : "")}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <BookOpen size={16} />
          <span>本地学习空间</span>
          <i className="online-dot" title="服务已连接" />
        </div>
      </aside>
      <main className="main-content">
        <Suspense fallback={<LoadingState />}>
          <Routes>
            <Route path="/" element={<ProblemListPage />} />
            <Route path="/problems/:id" element={<ProblemPage />} />
            <Route path="/submissions" element={<SubmissionsPage />} />
            <Route path="/submissions/:id" element={<SubmissionDetailPage />} />
            <Route path="/manage" element={<ManageProblemsPage />} />
            <Route path="/manage/new" element={<ProblemEditorPage />} />
            <Route path="/manage/:id" element={<ProblemEditorPage />} />
            <Route path="*" element={<ProblemListPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default function App() {
  return <Layout />;
}
