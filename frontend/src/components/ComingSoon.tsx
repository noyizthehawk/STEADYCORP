export default function ComingSoon({ label = "Coming soon" }: { label?: string }) {
  return <p>{label.toUpperCase()}</p>;
}
