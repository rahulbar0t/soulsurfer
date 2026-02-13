import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Play, Eye, Target, TrendUp, Clock, HashStraight } from '@phosphor-icons/react';
import SeverityBadge from './SeverityBadge';
import './ErrorCard.css';

// Reference tips for each metric
const REFERENCE_TIPS = {
  left_knee_angle: {
    title: "Proper Knee Bend",
    tip: "Keep knees bent 110-170° for stability.",
    image: "/references/left_knee_angle.png"
  },
  right_knee_angle: {
    title: "Proper Knee Bend",
    tip: "Keep knees bent 110-170° for stability.",
    image: "/references/right_knee_angle.png"
  },
  left_hip_angle: {
    title: "Hip Hinge Position",
    tip: "Maintain 90-170° hip angle.",
    image: "/references/left_hip_angle.png"
  },
  right_hip_angle: {
    title: "Hip Hinge Position",
    tip: "Maintain 90-170° hip angle.",
    image: "/references/right_hip_angle.png"
  },
  left_elbow_angle: {
    title: "Relaxed Arms",
    tip: "Keep elbows soft (100-180°).",
    image: "/references/left_elbow_angle.png"
  },
  right_elbow_angle: {
    title: "Relaxed Arms",
    tip: "Keep elbows soft (100-180°).",
    image: "/references/right_elbow_angle.png"
  },
  left_arm_raise: {
    title: "Arm Balance Position",
    tip: "Arms at 20-120° from body.",
    image: "/references/left_arm_raise.png"
  },
  right_arm_raise: {
    title: "Arm Balance Position",
    tip: "Arms at 20-120° from body.",
    image: "/references/right_arm_raise.png"
  },
  shoulder_tilt: {
    title: "Level Shoulders",
    tip: "Keep shoulders roughly horizontal.",
    image: "/references/shoulder_tilt.png"
  },
  spinal_angle: {
    title: "Upright Posture",
    tip: "Stay within 35° from vertical.",
    image: "/references/spinal_angle.png"
  },
  head_forward_offset: {
    title: "Head Position",
    tip: "Keep head centered over shoulders.",
    image: "/references/head_forward_offset.png"
  },
  stance_width_ratio: {
    title: "Stance Width",
    tip: "Feet 1.5-3x hip width apart.",
    image: "/references/stance_width_ratio.png"
  }
};

function formatMetricName(metric) {
  return metric
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getUnit(metric) {
  if (metric === 'stance_width_ratio') return '';
  if (metric === 'head_forward_offset') return 'm';
  return '\u00B0';
}

export default function ErrorCard({ error }) {
  const unit = getUnit(error.metric);
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const reference = REFERENCE_TIPS[error.metric] || {
    title: "Technique Reference",
    tip: "Aim for the ideal range.",
    image: null
  };

  const hasClip = error.clip_path && error.thumbnail_path;

  const handleVideoClick = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleVideoEnded = () => {
    setIsPlaying(false);
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
    }
  };

  return (
    <motion.div
      className={`error-card error-card--${error.severity} ${hasClip ? 'error-card--expanded' : ''}`}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      {/* Severity glow bar */}
      <div className="error-card__glow"></div>

      <div className="error-card__header">
        <h4 className="error-card__metric">{formatMetricName(error.metric)}</h4>
        <SeverityBadge severity={error.severity} />
      </div>

      {/* Video comparison section */}
      {hasClip && (
        <div className="error-card__comparison">
          {/* User's clip */}
          <div className="error-card__clip-container">
            <span className="error-card__clip-label">
              <Eye weight="fill" size={12} />
              Your Technique
            </span>
            <motion.div
              className="error-card__video-wrapper"
              onClick={handleVideoClick}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <video
                ref={videoRef}
                className="error-card__video"
                poster={error.thumbnail_path}
                onEnded={handleVideoEnded}
                playsInline
                muted
              >
                <source src={error.clip_path} type="video/mp4" />
              </video>
              {!isPlaying && (
                <div className="error-card__play-overlay">
                  <motion.div
                    className="error-card__play-btn"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Play weight="fill" size={24} />
                  </motion.div>
                </div>
              )}
            </motion.div>
            <span className="error-card__clip-value">
              <Clock weight="fill" size={12} />
              {error.worst_measured_value}{unit} at {error.worst_timestamp_sec?.toFixed(1)}s
            </span>
          </div>

          {/* Reference image */}
          <div className="error-card__reference-container">
            <span className="error-card__clip-label">
              <Target weight="fill" size={12} />
              {reference.title}
            </span>
            <div className="error-card__reference-wrapper">
              {reference.image ? (
                <img
                  src={reference.image}
                  alt={reference.title}
                  className="error-card__reference-img"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div className="error-card__reference-placeholder" style={{ display: reference.image ? 'none' : 'flex' }}>
                <Target weight="duotone" size={32} />
                <span>{reference.title}</span>
              </div>
            </div>
            <span className="error-card__reference-tip">{reference.tip}</span>
          </div>
        </div>
      )}

      <div className="error-card__values">
        <div className="error-card__measured">
          <span className="error-card__label">
            <TrendUp weight="fill" size={12} />
            Avg. Measured
          </span>
          <span className="error-card__value error-card__value--mono">
            {error.avg_measured_value}{unit}
          </span>
        </div>
        <div className="error-card__ideal">
          <span className="error-card__label">
            <Target weight="fill" size={12} />
            Ideal Range
          </span>
          <span className="error-card__value error-card__value--mono">
            {error.ideal_min}{unit} &ndash; {error.ideal_max}{unit}
          </span>
        </div>
      </div>

      <div className="error-card__freq">
        <div className="error-card__freq-header">
          <span className="error-card__label">Frequency</span>
          <span className="error-card__freq-pct">{error.frequency_pct}%</span>
        </div>
        <div className="error-card__bar-bg">
          <motion.div
            className={`error-card__bar-fill error-card__bar-fill--${error.severity}`}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(error.frequency_pct, 100)}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <div className="error-card__bar-shine"></div>
          </motion.div>
        </div>
      </div>

      <div className="error-card__footer">
        <span className="error-card__footer-item">
          <TrendUp weight="fill" size={12} />
          Max: {error.max_deviation}{unit}
        </span>
        <span className="error-card__footer-item">
          <HashStraight weight="fill" size={12} />
          {error.frame_count} / {error.total_frames_analyzed} frames
        </span>
      </div>
    </motion.div>
  );
}
