import { motion } from 'framer-motion';
import Markdown from 'react-markdown';
import { Timer, FrameCorners, FastForward, Lightning, Quotes, Waves, ArrowsClockwise } from '@phosphor-icons/react';
import ErrorCard from './ErrorCard';
import ChatPanel from './ChatPanel';
import './ResultsScreen.css';

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

const STAT_ICONS = {
  duration: Timer,
  frames: FrameCorners,
  skipped: FastForward,
  processing: Lightning,
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

export default function ResultsScreen({ report, onReset }) {
  const { aggregated_errors: errors = [] } = report;
  const hasFeedback = report.coaching_feedback && report.coaching_feedback.trim();

  const stats = [
    { key: 'duration', icon: STAT_ICONS.duration, value: formatDuration(report.video_duration_sec), label: 'Video Duration' },
    { key: 'frames', icon: STAT_ICONS.frames, value: report.analyzed_frames.toLocaleString(), label: 'Frames Analyzed' },
    { key: 'skipped', icon: STAT_ICONS.skipped, value: report.skipped_frames.toLocaleString(), label: 'Frames Skipped' },
    { key: 'processing', icon: STAT_ICONS.processing, value: formatDuration(report.processing_time_sec), label: 'Processing Time' },
  ];

  return (
    <motion.div
      className="results-screen"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <motion.div className="results-header" variants={itemVariants}>
        <div className="results-header__left">
          <h1 className="results-title">
            <Waves weight="duotone" size={32} />
            Session Report
          </h1>
          <p className="results-subtitle">Your AI surf coach has analyzed your session</p>
        </div>
        <motion.button
          className="reset-btn"
          onClick={onReset}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <ArrowsClockwise weight="bold" size={18} />
          New Session
        </motion.button>
      </motion.div>

      <motion.div className="stats-grid" variants={itemVariants}>
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.key}
              className="stat-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.1 }}
            >
              <div className="stat-card__accent"></div>
              <div className="stat-card__icon">
                <Icon weight="duotone" size={24} />
              </div>
              <div className="stat-card__content">
                <span className="stat-card__value">{stat.value}</span>
                <span className="stat-card__label">{stat.label}</span>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      <motion.section className="coaching-section" variants={itemVariants}>
        <h2 className="section-title">
          <span className="section-title__icon">
            <Quotes weight="fill" size={20} />
          </span>
          Coach's Analysis
        </h2>
        <div className="coaching-card">
          <div className="coaching-card__glow"></div>
          {hasFeedback ? (
            <div className="coaching-content">
              <Markdown>{report.coaching_feedback}</Markdown>
            </div>
          ) : (
            <div className="coaching-content coaching-empty">
              <Waves weight="duotone" size={48} />
              <p>
                Your coach is ready to help. Ask a question below to get personalized feedback!
              </p>
            </div>
          )}
          <ChatPanel sessionId={report.session_id} />
        </div>
      </motion.section>

      {errors.length > 0 && (
        <motion.section className="errors-section" variants={itemVariants}>
          <h2 className="section-title">
            <span className="section-title__icon section-title__icon--warning">
              <Lightning weight="fill" size={20} />
            </span>
            Technique Issues
            <span className="section-badge">{errors.length}</span>
          </h2>
          <div className="errors-grid">
            {errors.map((err, i) => (
              <motion.div
                key={`${err.metric}-${i}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.05 }}
              >
                <ErrorCard error={err} />
              </motion.div>
            ))}
          </div>
        </motion.section>
      )}

      <motion.div className="results-footer" variants={itemVariants}>
        <motion.button
          className="reset-btn reset-btn--large"
          onClick={onReset}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <ArrowsClockwise weight="bold" size={20} />
          Analyze Another Session
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
