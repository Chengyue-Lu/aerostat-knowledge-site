import HealthCheck from "../components/HealthCheck";

export default function HomePage() {
  return (
    <div>
      <h2>Home</h2>
      <p>Welcome to the Aerostat knowledge frontend.</p>
      <HealthCheck />
    </div>
  );
}
