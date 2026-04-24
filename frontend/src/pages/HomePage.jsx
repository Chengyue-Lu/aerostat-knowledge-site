import HealthCheck from "../components/HealthCheck";

export default function HomePage() {
  return (
    <section>
      <h2>Home</h2>
      <p>Welcome to the Aerostat knowledge frontend.</p>
      <HealthCheck />
    </section>
  );
}
