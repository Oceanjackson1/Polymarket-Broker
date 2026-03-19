export function BackgroundOrbs() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div
        className="bg-orb"
        style={{
          width: 500, height: 500,
          top: "10%", left: "15%",
          background: "radial-gradient(circle, rgba(245,158,11,0.08), transparent 70%)",
        }}
      />
      <div
        className="bg-orb"
        style={{
          width: 400, height: 400,
          top: "50%", right: "10%",
          background: "radial-gradient(circle, rgba(59,130,246,0.06), transparent 70%)",
          animationDelay: "-7s",
        }}
      />
      <div
        className="bg-orb"
        style={{
          width: 350, height: 350,
          bottom: "20%", left: "40%",
          background: "radial-gradient(circle, rgba(6,182,212,0.05), transparent 70%)",
          animationDelay: "-14s",
        }}
      />
    </div>
  );
}
