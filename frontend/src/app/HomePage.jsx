import AdminHomePage from "./AdminHomePage.jsx";
import StudentHomePage from "./StudentHomePage.jsx";
import TeacherHomePage from "./TeacherHomePage.jsx";

export default function HomePage({ user }) {
  if (user.role === "admin") {
    return <AdminHomePage user={user} />;
  }
  if (user.role === "teacher") {
    return <TeacherHomePage user={user} />;
  }
  if (user.role === "student") {
    return <StudentHomePage user={user} />;
  }

  return <StudentHomePage user={user} />;
}
