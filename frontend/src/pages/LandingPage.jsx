import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/20 blur-[100px] rounded-full pointer-events-none" />
      <div className="absolute top-1/4 right-1/4 w-[400px] h-[400px] bg-secondary/10 blur-[80px] rounded-full pointer-events-none" />
      
      {/* Navbar */}
      <nav className="fixed top-0 w-full p-6 flex justify-between items-center z-50 bg-bg-surface/50 backdrop-blur-md border-b border-white/5">
        <div className="font-bold text-2xl bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          SafeDrive AI
        </div>
        <div>
          <Link to="/login" className="text-sm font-semibold hover:text-primary transition-colors">
            Access Portal
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="z-10 text-center px-4 max-w-4xl">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
          Intelligence for <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
            Safer Journeys.
          </span>
        </h1>
        <p className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
          Advanced computer vision monitoring road conditions in real-time. Anticipate hazards before they happen.
        </p>
        <Link 
          to="/login"
          className="inline-flex items-center justify-center px-8 py-4 rounded-full bg-gradient-to-r from-primary to-secondary text-white font-bold text-lg hover:scale-105 transition-transform shadow-[0_10px_25px_rgba(56,189,248,0.3)]"
        >
          Launch Dashboard
        </Link>
      </main>

      {/* Decorative Elements */}
      <div className="absolute bottom-0 w-full h-32 bg-gradient-to-t from-bg-base to-transparent pointer-events-none" />
    </div>
  );
}
