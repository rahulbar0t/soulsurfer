import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Waves, Eye, Ruler, ChatCircleDots, Waveform, CheckCircle } from '@phosphor-icons/react';
import { getSession } from '../api';
import './ProcessingScreen.css';

const POLL_INTERVAL_MS = 2500;

const PROCESSING_STEPS = [
  { id: 'extract', icon: Eye, label: 'Extracting poses from video frames' },
  { id: 'measure', icon: Ruler, label: 'Measuring biomechanical angles' },
  { id: 'analyze', icon: Waveform, label: 'Analyzing technique patterns' },
  { id: 'coach', icon: ChatCircleDots, label: 'Generating coaching feedback' },
];

export default function ProcessingScreen({ sessionId, onComplete, onError }) {
  const cancelledRef = useRef(false);
  const [activeStep, setActiveStep] = useState(0);

  // Cycle through steps for visual effect
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep(prev => (prev + 1) % PROCESSING_STEPS.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    cancelledRef.current = false;

    async function poll() {
      if (cancelledRef.current) return;

      try {
        const data = await getSession(sessionId);

        if (cancelledRef.current) return;

        if (data.status === 'completed') {
          onComplete(data);
          return;
        }

        if (data.status === 'failed') {
          onError('Processing failed. Please try again with a different video.');
          return;
        }

        setTimeout(poll, POLL_INTERVAL_MS);
      } catch (err) {
        if (!cancelledRef.current) {
          onError(err.message);
        }
      }
    }

    const initialDelay = setTimeout(poll, 1500);

    return () => {
      cancelledRef.current = true;
      clearTimeout(initialDelay);
    };
  }, [sessionId, onComplete, onError]);

  return (
    <motion.div
      className="processing-screen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Barrel tunnel effect background */}
      <div className="barrel-tunnel">
        <div className="barrel-tunnel__ring barrel-tunnel__ring--1"></div>
        <div className="barrel-tunnel__ring barrel-tunnel__ring--2"></div>
        <div className="barrel-tunnel__ring barrel-tunnel__ring--3"></div>
        <div className="barrel-tunnel__ring barrel-tunnel__ring--4"></div>
        <div className="barrel-tunnel__ring barrel-tunnel__ring--5"></div>
        <div className="barrel-tunnel__center"></div>
      </div>

      <div className="processing-content">
        {/* Morphing blob loader */}
        <motion.div
          className="blob-loader"
          animate={{
            scale: [1, 1.05, 1],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="blob-loader__inner">
            <Waves weight="duotone" size={48} />
          </div>
        </motion.div>

        <motion.h2
          className="processing-title"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          Inside the Barrel
        </motion.h2>

        <motion.p
          className="processing-subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          SoulSurfer is analyzing your session
        </motion.p>

        {/* Processing steps */}
        <div className="processing-steps">
          {PROCESSING_STEPS.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === activeStep;
            const isComplete = index < activeStep;

            return (
              <motion.div
                key={step.id}
                className={`processing-step ${isActive ? 'processing-step--active' : ''} ${isComplete ? 'processing-step--complete' : ''}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
              >
                <div className="processing-step__icon">
                  {isComplete ? (
                    <CheckCircle weight="fill" size={20} />
                  ) : (
                    <Icon weight={isActive ? "fill" : "regular"} size={20} />
                  )}
                </div>
                <span className="processing-step__label">{step.label}</span>
                {isActive && (
                  <motion.div
                    className="processing-step__pulse"
                    layoutId="activePulse"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                  />
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Progress wave */}
        <div className="progress-wave">
          <div className="progress-wave__track">
            <motion.div
              className="progress-wave__fill"
              initial={{ width: "0%" }}
              animate={{ width: "100%" }}
              transition={{
                duration: 12,
                ease: "linear",
                repeat: Infinity
              }}
            />
            <div className="progress-wave__shimmer"></div>
          </div>
        </div>

        <motion.p
          className="processing-hint"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          Hang loose — this may take a moment depending on video length
        </motion.p>
      </div>
    </motion.div>
  );
}
