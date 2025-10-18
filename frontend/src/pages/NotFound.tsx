import { Link } from "react-router-dom";

function NotFound(): JSX.Element {
  return (
    <section className="mx-auto max-w-xl text-center">
      <h2 className="text-3xl font-semibold text-white">Page not found</h2>
      <p className="mt-3 text-sm text-slate-400">
        The page you are looking for doesn\'t exist. Head back to the dashboard to continue exploring the
        starter project.
      </p>
      <Link
        to="/"
        className="mt-6 inline-flex items-center justify-center rounded-full bg-indigo-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-400"
      >
        Go home
      </Link>
    </section>
  );
}

export default NotFound;
