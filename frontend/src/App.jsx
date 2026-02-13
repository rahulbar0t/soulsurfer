import { useState, useCallback, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X, Waves } from '@phosphor-icons/react';
import UploadForm from './components/UploadForm';
import ProcessingScreen from './components/ProcessingScreen';
import ResultsScreen from './components/ResultsScreen';
import './App.css';

// Konami code sequence
const KONAMI_CODE = [
  'ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown',
  'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight',
  'KeyB', 'KeyA'
];

export default function App() {
  const [screen, setScreen] = useState('upload');
  const [sessionId, setSessionId] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [showEasterEgg, setShowEasterEgg] = useState(false);
  const konamiIndex = useRef(0);

  // Scroll to top whenever the screen changes or on initial load
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [screen]);

  // Konami code easter egg listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.code === KONAMI_CODE[konamiIndex.current]) {
        konamiIndex.current++;
        if (konamiIndex.current === KONAMI_CODE.length) {
          setShowEasterEgg(true);
          konamiIndex.current = 0;
          // Auto-hide after animation
          setTimeout(() => setShowEasterEgg(false), 3000);
        }
      } else {
        konamiIndex.current = 0;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSessionCreated = useCallback((id) => {
    setSessionId(id);
    setScreen('processing');
    setError('');
  }, []);

  const handleComplete = useCallback((data) => {
    setReport(data);
    setScreen('results');
  }, []);

  const handleError = useCallback((msg) => {
    setError(msg);
    setScreen('upload');
  }, []);

  const handleReset = useCallback(() => {
    setScreen('upload');
    setSessionId(null);
    setReport(null);
    setError('');
  }, []);

  return (
    <div className="app">
      {/* Easter egg overlay */}
      <AnimatePresence>
        {showEasterEgg && (
          <motion.div
            className="easter-egg-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="easter-egg-content"
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0, rotate: 180 }}
              transition={{ type: "spring", stiffness: 200 }}
            >
              <Waves weight="fill" size={80} />
              <h2>Barrel Roll!</h2>
              <p>You found the secret move!</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {screen === 'upload' && (
          <motion.div
            key="upload"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <AnimatePresence>
              {error && (
                <motion.div
                  className="app-error"
                  initial={{ opacity: 0, y: -20, height: 0 }}
                  animate={{ opacity: 1, y: 0, height: 'auto' }}
                  exit={{ opacity: 0, y: -20, height: 0 }}
                >
                  <p>{error}</p>
                  <button onClick={() => setError('')} aria-label="Dismiss error">
                    <X weight="bold" size={18} />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
            <UploadForm onSessionCreated={handleSessionCreated} />
          </motion.div>
        )}

        {screen === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <ProcessingScreen
              sessionId={sessionId}
              onComplete={handleComplete}
              onError={handleError}
            />
          </motion.div>
        )}

        {screen === 'results' && report && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <ResultsScreen report={report} onReset={handleReset} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
